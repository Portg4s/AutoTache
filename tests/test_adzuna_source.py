import httpx
import pytest

from autotache_jobs.sources.adzuna import (
    AdzunaSource,
    AdzunaSourceError,
    normalize_adzuna_offer,
)


def _source_with_transport(transport: httpx.MockTransport, **overrides) -> AdzunaSource:
    values = {
        "app_id": "test-app-id",
        "app_key": "test-app-key",
        "endpoint_base_url": "https://example.test/adzuna",
        "http_client": httpx.Client(transport=transport),
    }
    values.update(overrides)
    return AdzunaSource(**values)


def _frontend_offer(**overrides) -> dict:
    values = {
        "id": "adzuna-front",
        "title": "Frontend Developer WordPress",
        "description": (
            "Build WordPress interfaces with Elementor, HTML, CSS and JavaScript. "
            "Remote work possible."
        ),
        "company": {"display_name": "Studio Web"},
        "location": {"display_name": "Paris, France", "area": ["France", "Ile-de-France", "Paris"]},
        "category": {"label": "IT Jobs"},
        "contract_type": "permanent",
        "salary_min": 35000,
        "salary_max": 45000,
        "created": "2026-05-01T10:00:00Z",
        "redirect_url": "https://www.adzuna.fr/details/adzuna-front",
    }
    values.update(overrides)
    return values


def test_collect_raw_offers_returns_results_from_mocked_response() -> None:
    seen_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, json={"results": [{"id": "A1"}, {"id": "A2"}]})

    source = _source_with_transport(httpx.MockTransport(handler))

    assert source.collect_raw_offers() == [{"id": "A1"}, {"id": "A2"}]
    assert seen_urls == [
        "https://example.test/adzuna/fr/search/1?app_id=test-app-id&app_key=test-app-key&results_per_page=20"
    ]


def test_collect_raw_offers_handles_empty_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    source = _source_with_transport(httpx.MockTransport(handler))

    assert source.collect_raw_offers() == []


def test_collect_raw_offers_raises_clear_error_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="API unavailable")

    source = _source_with_transport(httpx.MockTransport(handler))

    with pytest.raises(AdzunaSourceError, match="Erreur HTTP 500"):
        source.collect_raw_offers()


def test_collect_raw_offers_follows_pagination_up_to_max_pages() -> None:
    seen_paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        page = request.url.path.rsplit("/", maxsplit=1)[-1]
        return httpx.Response(200, json={"results": [{"id": f"A{page}"}]})

    source = _source_with_transport(httpx.MockTransport(handler), max_pages=2)

    assert source.collect_raw_offers() == [{"id": "A1"}, {"id": "A2"}]
    assert seen_paths == ["/adzuna/fr/search/1", "/adzuna/fr/search/2"]


def test_collect_raw_offers_sends_adzuna_query_params_without_real_network() -> None:
    seen_params = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_params.update(dict(request.url.params))
        return httpx.Response(200, json={"results": []})

    source = _source_with_transport(
        httpx.MockTransport(handler),
        country="fr",
        keywords=["frontend", "wordpress"],
        location="Dijon",
        results_per_page=10,
    )

    source.collect_raw_offers()

    assert seen_params["app_id"] == "test-app-id"
    assert seen_params["app_key"] == "test-app-key"
    assert seen_params["what"] == "frontend wordpress"
    assert seen_params["where"] == "Dijon"
    assert seen_params["results_per_page"] == "10"


def test_normalize_adzuna_offer_marks_frontend_offer_relevant() -> None:
    normalized = normalize_adzuna_offer(_frontend_offer())

    assert normalized["id_offre"] == "adzuna-front"
    assert normalized["source"] == "Adzuna"
    assert normalized["titre"] == "Frontend Developer WordPress"
    assert normalized["entreprise"] == "Studio Web"
    assert normalized["url_offre"] == "https://www.adzuna.fr/details/adzuna-front"
    assert normalized["is_relevant"] is True
    assert "WordPress" in normalized["matched_keywords"]
    assert normalized["decision"] in {"Pertinent", "À vérifier"}


def test_normalize_adzuna_offer_marks_non_relevant_offer_rejected() -> None:
    normalized = normalize_adzuna_offer(
        {
            "id": "data-analyst",
            "title": "Data Analyst",
            "description": "SQL reporting and BI dashboards.",
            "company": {"display_name": "Data Corp"},
            "redirect_url": "https://www.adzuna.fr/details/data-analyst",
        }
    )

    assert normalized["source"] == "Adzuna"
    assert normalized["is_relevant"] is False
    assert "data analyst" in normalized["excluded_by"]
    assert normalized["decision"].startswith("Rejet")


def test_normalize_adzuna_offer_extracts_technologies_from_title_and_description() -> None:
    normalized = normalize_adzuna_offer(
        _frontend_offer(
            title="UI Designer",
            description="Create Figma mockups and HTML CSS JavaScript React interfaces.",
        )
    )

    assert normalized["technologies"] == ["HTML", "CSS", "JavaScript", "React", "Figma", "UI"]


def test_normalize_adzuna_offer_extracts_salary_from_salary_fields() -> None:
    normalized = normalize_adzuna_offer(_frontend_offer(salary_min=32000, salary_max=42000))

    assert normalized["salaire_brut"] == "32000 euros - 42000 euros annuel"
    assert normalized["salaire_min"] == 32000
    assert normalized["salaire_max"] == 42000
    assert normalized["salaire_moyen"] == 37000
    assert normalized["salaire_type"] == "annuel"


def test_collect_adds_normalization_and_scoring_without_real_network() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [_frontend_offer()]})

    source = _source_with_transport(httpx.MockTransport(handler))
    result = source.collect()

    assert result.source_name == "Adzuna"
    assert len(result.raw_offers) == 1
    assert len(result.normalized_offers) == 1
    assert result.stats.enabled is True
    assert result.stats.fetched == 1
    assert result.stats.kept == 1
    assert result.stats.filtered == 0
    assert result.normalized_offers[0]["source"] == "Adzuna"
    assert isinstance(result.normalized_offers[0]["score_total"], int)
    assert result.normalized_offers[0]["score_reason"]
    assert isinstance(result.normalized_offers[0]["score_details"], dict)
