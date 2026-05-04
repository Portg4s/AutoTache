"""Export helpers for normalized offers."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter


CSV_COLUMNS = [
    "date_detection",
    "id_offre",
    "source",
    "titre",
    "entreprise",
    "localisation",
    "code_postal",
    "type_contrat",
    "experience",
    "salaire_brut",
    "salaire_min",
    "salaire_max",
    "salaire_moyen",
    "salaire_type",
    "teletravail_mention",
    "teletravail_jours",
    "technologies",
    "date_publication",
    "date_actualisation",
    "is_relevant",
    "relevance_reason",
    "matched_keywords",
    "excluded_by",
    "url_offre",
]

XLSX_RELEVANT_FILL = PatternFill(fill_type="solid", fgColor="EAF4EA")
XLSX_HEADER_FILL = PatternFill(fill_type="solid", fgColor="D9EAF7")
XLSX_MAX_COLUMN_WIDTH = 60


def export_offers_to_csv(
    offers: list[dict],
    export_dir: str | Path,
    filename: str | None = None,
) -> Path | None:
    """Export normalized offers to an Excel-friendly French CSV."""

    if not offers:
        return None

    target_dir = Path(export_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"offres_{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv"

    output_path = target_dir / filename
    with output_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=CSV_COLUMNS,
            delimiter=";",
            extrasaction="ignore",
        )
        writer.writeheader()
        for offer in offers:
            writer.writerow({column: _format_csv_value(offer.get(column)) for column in CSV_COLUMNS})

    return output_path


def export_offers_to_xlsx(
    offers: list[dict],
    export_dir: str | Path,
    filename: str | None = None,
) -> Path | None:
    """Export normalized offers to a formatted Excel workbook."""

    if not offers:
        return None

    target_dir = Path(export_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"offres_{datetime.now().strftime('%Y-%m-%d_%H%M')}.xlsx"

    output_path = target_dir / filename
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Offres"

    worksheet.append(CSV_COLUMNS)
    for cell in worksheet[1]:
        cell.font = Font(bold=True)
        cell.fill = XLSX_HEADER_FILL

    url_column_index = CSV_COLUMNS.index("url_offre") + 1
    is_relevant_column_index = CSV_COLUMNS.index("is_relevant") + 1

    for offer in offers:
        row_values = [_format_xlsx_value(column, offer.get(column)) for column in CSV_COLUMNS]
        worksheet.append(row_values)
        row_index = worksheet.max_row

        if offer.get("is_relevant") is True:
            for cell in worksheet[row_index]:
                cell.fill = XLSX_RELEVANT_FILL

        url_cell = worksheet.cell(row=row_index, column=url_column_index)
        if url_cell.value:
            url_cell.hyperlink = str(url_cell.value)
            url_cell.style = "Hyperlink"

        relevant_cell = worksheet.cell(row=row_index, column=is_relevant_column_index)
        relevant_cell.value = _format_relevance_value(offer.get("is_relevant"))

    worksheet.auto_filter.ref = worksheet.dimensions
    worksheet.freeze_panes = "A2"
    _adjust_column_widths(worksheet)

    workbook.save(output_path)
    return output_path


def _format_csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _format_xlsx_value(column: str, value: Any) -> Any:
    if column == "is_relevant":
        return _format_relevance_value(value)
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return value


def _format_relevance_value(value: Any) -> str:
    if value is True:
        return "Oui"
    if value is False:
        return "Non"
    return ""


def _adjust_column_widths(worksheet: Any) -> None:
    for column_cells in worksheet.columns:
        max_length = 0
        column_letter = get_column_letter(column_cells[0].column)
        for cell in column_cells:
            if cell.value is None:
                continue
            max_length = max(max_length, len(str(cell.value)))
        worksheet.column_dimensions[column_letter].width = min(max_length + 2, XLSX_MAX_COLUMN_WIDTH)
