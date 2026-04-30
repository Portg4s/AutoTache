import json
from pathlib import Path

from autotache_jobs.storage import (
    filter_new_offers,
    load_seen_offer_ids,
    save_seen_offer_ids,
    update_seen_ids,
)


def test_load_seen_offer_ids_missing_file_returns_empty_set(tmp_path: Path) -> None:
    assert load_seen_offer_ids(tmp_path / "missing.json") == set()


def test_load_seen_offer_ids_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "seen.json"
    path.write_text(json.dumps(["A1", "B2", "A1"]), encoding="utf-8")

    assert load_seen_offer_ids(path) == {"A1", "B2"}


def test_load_seen_offer_ids_invalid_or_empty_returns_empty_set(tmp_path: Path) -> None:
    invalid_path = tmp_path / "invalid.json"
    empty_path = tmp_path / "empty.json"
    invalid_path.write_text("{not-json", encoding="utf-8")
    empty_path.write_text("", encoding="utf-8")

    assert load_seen_offer_ids(invalid_path) == set()
    assert load_seen_offer_ids(empty_path) == set()


def test_save_seen_offer_ids_writes_sorted_json(tmp_path: Path) -> None:
    path = tmp_path / "data" / "seen.json"

    save_seen_offer_ids(path, {"B2", "A1", "C3"})

    assert json.loads(path.read_text(encoding="utf-8")) == ["A1", "B2", "C3"]


def test_filter_new_offers_ignores_seen_and_missing_ids() -> None:
    offers = [
        {"id_offre": "A1", "titre": "deja vue"},
        {"id_offre": "B2", "titre": "nouvelle"},
        {"titre": "sans id"},
    ]

    assert filter_new_offers(offers, {"A1"}) == [{"id_offre": "B2", "titre": "nouvelle"}]


def test_update_seen_ids_adds_offer_ids_without_mutating_input() -> None:
    seen_ids = {"A1"}

    updated = update_seen_ids(seen_ids, [{"id_offre": "B2"}, {"id_offre": ""}, {"titre": "sans id"}])

    assert seen_ids == {"A1"}
    assert updated == {"A1", "B2"}
