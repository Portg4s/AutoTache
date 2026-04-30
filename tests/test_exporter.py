import csv
from pathlib import Path

from autotache_jobs.exporter import CSV_COLUMNS, export_offers_to_csv


def _sample_offer() -> dict:
    return {
        "date_detection": "2026-04-29T10:00:00",
        "id_offre": "A1",
        "source": "France Travail",
        "titre": "Developpeur WordPress",
        "entreprise": "Agence Numérique",
        "localisation": "Lyon",
        "code_postal": "69000",
        "type_contrat": "CDI",
        "experience": "2 ans",
        "salaire_brut": "Annuel de 35000 Euros a 42000 Euros",
        "salaire_min": 35000,
        "salaire_max": 42000,
        "salaire_moyen": 38500,
        "salaire_type": "annuel",
        "teletravail_mention": "teletravail partiel",
        "teletravail_jours": 2,
        "technologies": ["WordPress", "Figma"],
        "date_publication": "2026-04-20",
        "date_actualisation": "2026-04-21",
        "is_relevant": True,
        "relevance_reason": "Offre conservée",
        "matched_keywords": ["WordPress", "Figma"],
        "excluded_by": [],
        "url_offre": "https://candidat.francetravail.fr/offres/recherche/detail/A1",
    }


def test_export_offers_to_csv_creates_file(tmp_path: Path) -> None:
    output = export_offers_to_csv([_sample_offer()], tmp_path, filename="offres.csv")

    assert output == tmp_path / "offres.csv"
    assert output.exists()


def test_export_offers_to_csv_empty_list_creates_nothing(tmp_path: Path) -> None:
    output = export_offers_to_csv([], tmp_path, filename="offres.csv")

    assert output is None
    assert not (tmp_path / "offres.csv").exists()


def test_export_csv_contains_expected_columns(tmp_path: Path) -> None:
    output = export_offers_to_csv([_sample_offer()], tmp_path, filename="offres.csv")

    with output.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file, delimiter=";")
        header = next(reader)

    assert header == CSV_COLUMNS


def test_export_csv_encodes_accents_with_utf8_sig(tmp_path: Path) -> None:
    output = export_offers_to_csv([_sample_offer()], tmp_path, filename="offres.csv")
    raw_bytes = output.read_bytes()

    assert raw_bytes.startswith(b"\xef\xbb\xbf")
    assert "Agence Numérique" in raw_bytes.decode("utf-8-sig")


def test_export_csv_converts_lists_to_readable_text(tmp_path: Path) -> None:
    output = export_offers_to_csv([_sample_offer()], tmp_path, filename="offres.csv")

    with output.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file, delimiter=";"))

    assert rows[0]["technologies"] == "WordPress, Figma"
    assert rows[0]["matched_keywords"] == "WordPress, Figma"
    assert rows[0]["excluded_by"] == ""
