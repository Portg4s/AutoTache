from pathlib import Path

import pytest
from openpyxl import Workbook

from autotache_jobs.cv.offer_reader import OfferReaderError, read_offer_from_xlsx


def test_reads_offer_from_temporary_xlsx(tmp_path: Path) -> None:
    xlsx_path = _workbook(
        tmp_path,
        ["source", "titre", "entreprise", "decision", "score_total", "technologies"],
        ["France Travail", "Integrateur web", "Studio", "Pertinent", 82, "HTML, CSS"],
    )

    offer = read_offer_from_xlsx(xlsx_path, 2)

    assert offer["row"] == 2
    assert offer["source"] == "France Travail"
    assert offer["titre"] == "Integrateur web"
    assert offer["entreprise"] == "Studio"
    assert offer["score_total"] == 82
    assert offer["technologies"] == "HTML, CSS"


def test_missing_columns_are_empty(tmp_path: Path) -> None:
    xlsx_path = _workbook(tmp_path, ["titre"], ["Webdesigner"])

    offer = read_offer_from_xlsx(xlsx_path, 2)

    assert offer["titre"] == "Webdesigner"
    assert offer["entreprise"] == ""
    assert offer["description"] == ""


def test_invalid_row_has_clear_error(tmp_path: Path) -> None:
    xlsx_path = _workbook(tmp_path, ["titre"], ["Webdesigner"])

    with pytest.raises(OfferReaderError, match="Ligne Excel invalide"):
        read_offer_from_xlsx(xlsx_path, 99)


def _workbook(tmp_path: Path, header: list[str], row: list[object]) -> Path:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(header)
    worksheet.append(row)
    xlsx_path = tmp_path / "debug.xlsx"
    workbook.save(xlsx_path)
    return xlsx_path

