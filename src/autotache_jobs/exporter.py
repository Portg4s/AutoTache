"""CSV export helpers for normalized offers."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any


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


def _format_csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)
