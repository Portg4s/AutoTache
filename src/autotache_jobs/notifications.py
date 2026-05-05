"""Optional notification helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import PureWindowsPath
from typing import Any

import httpx


DISCORD_TITLE = "📌 AutoTache - Résumé recherche emploi"
COLOR_SUCCESS = 0x2ECC71
COLOR_REVIEW = 0xF1C40F
COLOR_NEUTRAL = 0x5DADE2


def send_discord_summary(
    webhook_url: str,
    summary: dict[str, Any],
    http_post: Any = httpx.post,
) -> dict[str, Any]:
    """Send a compact Discord summary through a webhook."""

    if not webhook_url or not webhook_url.strip():
        return {
            "sent": False,
            "status": "webhook_missing",
            "error": "DISCORD_WEBHOOK_URL est vide ou absent.",
        }

    payload = _build_discord_payload(summary)
    try:
        response = http_post(webhook_url.strip(), json=payload, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        return {
            "sent": False,
            "status": "send_failed",
            "error": f"Echec envoi Discord ({type(exc).__name__}).",
        }

    return {"sent": True, "status": "sent", "error": None}


def _build_discord_payload(summary: dict[str, Any]) -> dict[str, Any]:
    decision_counts = _decision_counts(summary)
    review_count = decision_counts.get("À vérifier", 0)
    best_score = summary.get("best_score")

    fields = [
        {
            "name": "📊 Résultats",
            "value": "\n".join(
                [
                    f"🔎 Offres brutes: {summary.get('total_raw', 0)}",
                    f"✅ Pertinentes: {summary.get('total_relevant', 0)}",
                    f"🆕 Nouvelles exportées: {summary.get('total_new', 0)}",
                ]
            ),
            "inline": False,
        },
        {
            "name": "🧠 Scoring",
            "value": "\n".join(
                [
                    f"🟢 Pertinent: {decision_counts.get('Pertinent', 0)}",
                    f"🟡 À vérifier: {review_count}",
                    f"🔴 Rejeté: {decision_counts.get('Rejeté', 0)}",
                    f"🏆 Meilleur score: {best_score}/100" if isinstance(best_score, int) else "🏆 Meilleur score: aucun",
                ]
            ),
            "inline": False,
        },
        {
            "name": "📁 Exports",
            "value": "\n".join(
                [
                    f"📌 Suivi: {_filename_or_none(summary.get('tracking_xlsx_export_path'))}",
                    f"🆕 Nouvelles offres: {_filename_or_none(summary.get('xlsx_export_path'))}",
                    f"🧪 Debug: {_filename_or_none(summary.get('debug_xlsx_export_path'))}",
                    "Fichiers disponibles dans le dossier exports/",
                ]
            ),
            "inline": False,
        },
    ]

    status_lines = []
    if summary.get("total_relevant", 0) == 0:
        status_lines.append("Aucune offre pertinente trouvée.")
        if review_count > 0:
            status_lines.append("Des offres sont à vérifier manuellement.")
    else:
        status_lines.append("Résumé généré avec succès.")
    fields.append({"name": "ℹ️ Statut", "value": "\n".join(status_lines), "inline": False})

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
        return {"Pertinent": 0, "À vérifier": 0, "Rejeté": 0}
    return {
        "Pertinent": int(raw_counts.get("Pertinent", 0) or 0),
        "À vérifier": int(raw_counts.get("À vérifier", 0) or 0),
        "Rejeté": int(raw_counts.get("Rejeté", 0) or 0),
    }


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
