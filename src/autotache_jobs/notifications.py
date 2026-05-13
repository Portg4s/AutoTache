"""Optional notification helpers."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path, PureWindowsPath
from typing import Any

import httpx


DISCORD_TITLE = "\U0001F4CC AutoTache - R\u00e9sum\u00e9 recherche emploi"
COLOR_SUCCESS = 0x2ECC71
COLOR_REVIEW = 0xF1C40F
COLOR_NEUTRAL = 0x5DADE2


def send_discord_summary(
    webhook_url: str,
    summary: dict[str, Any],
    http_post: Any = httpx.post,
    tracking_file_path: str | Path | None = None,
) -> dict[str, Any]:
    """Send a compact Discord summary through a webhook."""

    if not webhook_url or not webhook_url.strip():
        return {
            "sent": False,
            "status": "webhook_missing",
            "error": "DISCORD_WEBHOOK_URL est vide ou absent.",
        }

    attachment_path = _tracking_attachment_path(summary, tracking_file_path)
    payload = _build_discord_payload(summary, has_tracking_attachment=attachment_path is not None)
    try:
        if attachment_path is None:
            response = http_post(webhook_url.strip(), json=payload, timeout=10)
        else:
            with attachment_path.open("rb") as tracking_file:
                response = http_post(
                    webhook_url.strip(),
                    data={"payload_json": json.dumps(payload)},
                    files={
                        "file": (
                            "offres_suivi.xlsx",
                            tracking_file,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    },
                    timeout=10,
                )
        response.raise_for_status()
    except Exception as exc:
        return {
            "sent": False,
            "status": "send_failed",
            "error": f"Echec envoi Discord ({type(exc).__name__}).",
        }

    return {"sent": True, "status": "sent", "error": None}


def _build_discord_payload(summary: dict[str, Any], has_tracking_attachment: bool = False) -> dict[str, Any]:
    decision_counts = _decision_counts(summary)
    review_count = decision_counts.get("\u00c0 v\u00e9rifier", 0)
    best_score = summary.get("best_score")

    fields = [
        {
            "name": "\U0001F4CA R\u00e9sultats",
            "value": "\n".join(
                [
                    f"\U0001F50E Offres brutes: {summary.get('total_raw', 0)}",
                    f"\u2705 Pertinentes: {summary.get('total_relevant', 0)}",
                    f"\U0001F195 Nouvelles export\u00e9es: {summary.get('total_new', 0)}",
                ]
            ),
            "inline": False,
        },
        {
            "name": "\U0001F310 Sources",
            "value": "\n".join(_source_lines(summary)),
            "inline": False,
        },
        {
            "name": "\U0001F9E0 Scoring",
            "value": "\n".join(
                [
                    f"\U0001F7E2 Pertinent: {decision_counts.get('Pertinent', 0)}",
                    f"\U0001F7E1 \u00c0 v\u00e9rifier: {review_count}",
                    f"\U0001F534 Rejet\u00e9: {decision_counts.get('Rejet\u00e9', 0)}",
                    f"\U0001F3C6 Meilleur score: {best_score}/100"
                    if isinstance(best_score, int)
                    else "\U0001F3C6 Meilleur score: aucun",
                ]
            ),
            "inline": False,
        },
        {
            "name": "\U0001F4C1 Exports",
            "value": "\n".join(
                [
                    f"\U0001F4CC Suivi: {_filename_or_none(summary.get('tracking_xlsx_export_path'))}",
                    f"\U0001F195 Nouvelles offres: {_filename_or_none(summary.get('xlsx_export_path'))}",
                    f"\U0001F9EA Debug: {_filename_or_none(summary.get('debug_xlsx_export_path'))}",
                    "Fichiers disponibles dans le dossier exports/",
                ]
            ),
            "inline": False,
        },
    ]

    status_lines = []
    if summary.get("total_relevant", 0) == 0:
        status_lines.append("Aucune offre pertinente trouv\u00e9e.")
        if review_count > 0:
            status_lines.append("Des offres sont \u00e0 v\u00e9rifier manuellement.")
    else:
        status_lines.append("R\u00e9sum\u00e9 g\u00e9n\u00e9r\u00e9 avec succ\u00e8s.")
    if has_tracking_attachment:
        status_lines.append("Le fichier de suivi cumulatif est joint.")
    fields.append({"name": "\u2139\ufe0f Statut", "value": "\n".join(status_lines), "inline": False})

    return {
        "embeds": [
            {
                "title": DISCORD_TITLE,
                "description": f"Date/heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "color": _embed_color(summary, review_count),
                "fields": fields,
            }
        ]
    }


def _decision_counts(summary: dict[str, Any]) -> dict[str, int]:
    raw_counts = summary.get("decision_counts")
    if not isinstance(raw_counts, dict):
        return {"Pertinent": 0, "\u00c0 v\u00e9rifier": 0, "Rejet\u00e9": 0}
    return {
        "Pertinent": int(raw_counts.get("Pertinent", 0) or 0),
        "\u00c0 v\u00e9rifier": int(
            raw_counts.get("\u00c0 v\u00e9rifier", raw_counts.get("Ã€ vÃ©rifier", 0)) or 0
        ),
        "Rejet\u00e9": int(raw_counts.get("Rejet\u00e9", raw_counts.get("RejetÃ©", 0)) or 0),
    }


def _source_lines(summary: dict[str, Any]) -> list[str]:
    source_stats = summary.get("source_stats")
    if not isinstance(source_stats, dict):
        return ["Aucune offre r\u00e9cup\u00e9r\u00e9e"]

    lines = []
    for source_name, stats in source_stats.items():
        if not isinstance(stats, dict):
            continue
        fetched = int(stats.get("fetched", 0) or 0)
        if fetched > 0:
            lines.append(f"{source_name} : {fetched} r\u00e9cup\u00e9r\u00e9es")

    return lines or ["Aucune offre r\u00e9cup\u00e9r\u00e9e"]


def _embed_color(summary: dict[str, Any], review_count: int) -> int:
    if summary.get("total_new", 0) > 0:
        return COLOR_SUCCESS
    if review_count > 0:
        return COLOR_REVIEW
    return COLOR_NEUTRAL


def _filename_or_none(value: Any) -> str:
    if not value:
        return "aucun"
    path = str(value)
    return PureWindowsPath(path).name


def _tracking_attachment_path(summary: dict[str, Any], override_path: str | Path | None = None) -> Path | None:
    raw_path = override_path if override_path is not None else summary.get("tracking_xlsx_export_path")
    if not raw_path:
        return None

    try:
        path = Path(raw_path)
        is_file = path.is_file()
    except (OSError, ValueError):
        return None

    if is_file:
        return path
    return None
