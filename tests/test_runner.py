import json
from pathlib import Path

from autotache_jobs.models import AppConfig, FranceTravailEnv
from autotache_jobs.runner import run_job_search


class FakeFranceTravailClient:
    def __init__(self, results_by_call: list[list[dict]]) -> None:
        self.results_by_call = results_by_call
        self.calls: list[dict] = []

    def search_offers(self, **kwargs) -> list[dict]:
        self.calls.append(kwargs)
        if not self.results_by_call:
            return []
        return self.results_by_call.pop(0)


def _config(**overrides) -> AppConfig:
    values = {
        "keywords": ["wordpress"],
        "communes": ["75056"],
        "distance_km": 20,
        "contract_types": ["CDI"],
        "days_back": 7,
        "allow_internship": False,
        "allow_apprenticeship": False,
    }
    values.update(overrides)
    return AppConfig(**values)


def _env() -> FranceTravailEnv:
    return FranceTravailEnv(
        client_id="fake-client-id",
        client_secret="fake-client-secret",
        scope="fake-scope",
        token_url="https://example.test/token",
        api_base_url="https://example.test/api",
    )


def _wordpress_offer(offer_id: str = "A1") -> dict:
    return {
        "id": offer_id,
        "intitule": "Developpeur WordPress",
        "description": "Creation de themes WordPress avec Elementor.",
        "typeContratLibelle": "CDI",
    }


def test_runner_exports_new_relevant_offer(tmp_path: Path) -> None:
    client = FakeFranceTravailClient([[_wordpress_offer()]])

    summary = run_job_search(_config(), _env(), client=client, data_dir=tmp_path / "data", export_dir=tmp_path / "exports")

    assert summary["total_raw"] == 1
    assert summary["total_normalized"] == 1
    assert summary["total_relevant"] == 1
    assert summary["total_new"] == 1
    assert summary["export_path"] is not None
    assert Path(summary["export_path"]).exists()


def test_runner_ignores_non_relevant_offer(tmp_path: Path) -> None:
    client = FakeFranceTravailClient(
        [[{"id": "DATA", "intitule": "Data analyst", "description": "Reporting BI et SQL."}]]
    )

    summary = run_job_search(_config(), _env(), client=client, data_dir=tmp_path / "data", export_dir=tmp_path / "exports")

    assert summary["total_raw"] == 1
    assert summary["total_relevant"] == 0
    assert summary["total_new"] == 0
    assert summary["export_path"] is None


def test_runner_ignores_already_seen_offer(tmp_path: Path) -> None:
    seen_path = tmp_path / "data" / "seen_offer_ids.json"
    seen_path.parent.mkdir(parents=True)
    seen_path.write_text(json.dumps(["A1"]), encoding="utf-8")
    client = FakeFranceTravailClient([[_wordpress_offer()]])

    summary = run_job_search(_config(), _env(), client=client, data_dir=tmp_path / "data", export_dir=tmp_path / "exports")

    assert summary["total_relevant"] == 1
    assert summary["total_new"] == 0
    assert summary["export_path"] is None
    assert json.loads(seen_path.read_text(encoding="utf-8")) == ["A1"]


def test_runner_deduplicates_between_multiple_searches(tmp_path: Path) -> None:
    client = FakeFranceTravailClient([[_wordpress_offer("A1")], [_wordpress_offer("A1")]])
    config = _config(keywords=["wordpress", "elementor"])

    summary = run_job_search(config, _env(), client=client, data_dir=tmp_path / "data", export_dir=tmp_path / "exports")

    assert len(client.calls) == 2
    assert summary["total_raw"] == 2
    assert summary["total_relevant"] == 1
    assert summary["total_new"] == 1


def test_runner_returns_none_export_path_when_no_new_offer(tmp_path: Path) -> None:
    client = FakeFranceTravailClient([[]])

    summary = run_job_search(_config(), _env(), client=client, data_dir=tmp_path / "data", export_dir=tmp_path / "exports")

    assert summary["total_raw"] == 0
    assert summary["total_new"] == 0
    assert summary["export_path"] is None


def test_runner_updates_seen_ids_only_with_exported_offers(tmp_path: Path) -> None:
    client = FakeFranceTravailClient(
        [
            [
                _wordpress_offer("A1"),
                {"id": "DATA", "intitule": "Data analyst", "description": "Reporting BI et SQL."},
            ]
        ]
    )

    summary = run_job_search(_config(), _env(), client=client, data_dir=tmp_path / "data", export_dir=tmp_path / "exports")
    seen_ids = json.loads(Path(summary["seen_ids_path"]).read_text(encoding="utf-8"))

    assert seen_ids == ["A1"]


def test_runner_uses_injected_client_without_network_client(tmp_path: Path) -> None:
    client = FakeFranceTravailClient([[_wordpress_offer()]])

    summary = run_job_search(_config(), _env(), client=client, data_dir=tmp_path / "data", export_dir=tmp_path / "exports")

    assert client.calls
    assert client.calls[0]["keyword"] == "wordpress"
    assert client.calls[0]["commune"] == "75056"
    assert client.calls[0]["distance"] == 20
    assert client.calls[0]["type_contrat"] == "CDI"
    assert summary["total_new"] == 1
