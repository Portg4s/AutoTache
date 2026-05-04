import csv
from pathlib import Path

from openpyxl import load_workbook

from autotache_jobs.exporter import CSV_COLUMNS, export_offers_to_csv, export_offers_to_xlsx


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


def test_export_offers_to_xlsx_creates_file(tmp_path: Path) -> None:
    output = export_offers_to_xlsx([_sample_offer()], tmp_path, filename="offres.xlsx")

    assert output == tmp_path / "offres.xlsx"
    assert output.exists()


def test_export_offers_to_xlsx_empty_list_creates_nothing(tmp_path: Path) -> None:
    output = export_offers_to_xlsx([], tmp_path, filename="offres.xlsx")

    assert output is None
    assert not (tmp_path / "offres.xlsx").exists()


def test_export_xlsx_contains_expected_columns(tmp_path: Path) -> None:
    output = export_offers_to_xlsx([_sample_offer()], tmp_path, filename="offres.xlsx")
    workbook = load_workbook(output)
    worksheet = workbook["Offres"]

    header = [cell.value for cell in worksheet[1]]

    assert header == CSV_COLUMNS


def test_export_xlsx_converts_lists_to_readable_text(tmp_path: Path) -> None:
    output = export_offers_to_xlsx([_sample_offer()], tmp_path, filename="offres.xlsx")
    workbook = load_workbook(output)
    worksheet = workbook["Offres"]
    columns = {cell.value: cell.column for cell in worksheet[1]}

    assert worksheet.cell(row=2, column=columns["technologies"]).value == "WordPress, Figma"
    assert worksheet.cell(row=2, column=columns["matched_keywords"]).value == "WordPress, Figma"
    assert worksheet.cell(row=2, column=columns["excluded_by"]).value in {"", None}
    assert worksheet.cell(row=2, column=columns["is_relevant"]).value == "Oui"


def test_export_xlsx_url_is_clickable(tmp_path: Path) -> None:
    output = export_offers_to_xlsx([_sample_offer()], tmp_path, filename="offres.xlsx")
    workbook = load_workbook(output)
    worksheet = workbook["Offres"]
    columns = {cell.value: cell.column for cell in worksheet[1]}
    url_cell = worksheet.cell(row=2, column=columns["url_offre"])

    assert url_cell.value == "https://candidat.francetravail.fr/offres/recherche/detail/A1"
    assert url_cell.hyperlink is not None
    assert url_cell.hyperlink.target == url_cell.value
