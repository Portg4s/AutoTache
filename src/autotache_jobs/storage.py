"""Local storage helpers for already-seen offer IDs."""

from __future__ import annotations

import json
from pathlib import Path


def load_seen_offer_ids(path: str | Path) -> set[str]:
    """Load already-seen offer IDs from a JSON list."""

    storage_path = Path(path)
    if not storage_path.exists():
        return set()

    try:
        raw_content = storage_path.read_text(encoding="utf-8").strip()
        if not raw_content:
            return set()
        loaded = json.loads(raw_content)
    except (OSError, json.JSONDecodeError):
        return set()

    if not isinstance(loaded, list):
        return set()

    return {str(offer_id).strip() for offer_id in loaded if str(offer_id).strip()}


def save_seen_offer_ids(path: str | Path, ids: set[str]) -> None:
    """Save seen offer IDs as a sorted, readable JSON list."""

    storage_path = Path(path)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_ids = sorted(str(offer_id).strip() for offer_id in ids if str(offer_id).strip())
    storage_path.write_text(
        json.dumps(sorted_ids, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def filter_new_offers(offers: list[dict], seen_ids: set[str]) -> list[dict]:
    """Return offers whose id_offre has not been seen yet."""

    return [
        offer
        for offer in offers
        if offer.get("id_offre") and str(offer["id_offre"]) not in seen_ids
    ]


def update_seen_ids(seen_ids: set[str], offers: list[dict]) -> set[str]:
    """Return a seen-ID set updated with ids from the provided offers."""

    updated_ids = set(seen_ids)
    for offer in offers:
        offer_id = offer.get("id_offre")
        if offer_id:
            updated_ids.add(str(offer_id))
    return updated_ids
