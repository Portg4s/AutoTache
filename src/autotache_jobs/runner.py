"""Main orchestration for the AutoTache job search flow."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .exporter import export_offers_to_csv
from .france_travail_client import FranceTravailClient
from .normalizer import normalize_france_travail_offer
from .storage import filter_new_offers, load_seen_offer_ids, save_seen_offer_ids, update_seen_ids


def run_job_search(
    config: Any,
    env_settings: Any,
    client: Any | None = None,
    data_dir: str | Path = "data",
    export_dir: str | Path = "exports",
) -> dict[str, Any]:
    """Run the full local job search pipeline and return a summary."""

    active_client = client or FranceTravailClient(
        client_id=env_settings.client_id,
        client_secret=env_settings.client_secret,
        scope=env_settings.scope,
        token_url=env_settings.token_url,
        api_base_url=env_settings.api_base_url,
    )

    raw_offers = _collect_raw_offers(config, active_client)
    normalized_offers = [
        normalize_france_travail_offer(
            raw_offer,
            allow_stage=config.allow_internship,
            allow_alternance=config.allow_apprenticeship,
        )
        for raw_offer in raw_offers
    ]
    relevant_offers = [offer for offer in normalized_offers if offer["is_relevant"] is True]
    deduplicated_relevant_offers = _deduplicate_by_id(relevant_offers)

    seen_ids_path = Path(data_dir) / "seen_offer_ids.json"
    seen_ids = load_seen_offer_ids(seen_ids_path)
    new_offers = filter_new_offers(deduplicated_relevant_offers, seen_ids)
    export_path = export_offers_to_csv(new_offers, export_dir)

    if new_offers:
        save_seen_offer_ids(seen_ids_path, update_seen_ids(seen_ids, new_offers))

    return {
        "total_raw": len(raw_offers),
        "total_normalized": len(normalized_offers),
        "total_relevant": len(deduplicated_relevant_offers),
        "total_new": len(new_offers),
        "export_path": str(export_path) if export_path else None,
        "seen_ids_path": str(seen_ids_path),
    }


def _collect_raw_offers(config: Any, client: Any) -> list[dict]:
    raw_offers: list[dict] = []
    min_creation_date = _min_creation_date(config.days_back)

    for keyword in config.keywords:
        for commune in config.communes:
            for contract_type in config.contract_types:
                results = client.search_offers(
                    keyword=keyword,
                    commune=commune,
                    distance=config.distance_km,
                    type_contrat=contract_type,
                    min_creation_date=min_creation_date,
                )
                raw_offers.extend(results or [])

    return raw_offers


def _deduplicate_by_id(offers: list[dict]) -> list[dict]:
    deduplicated: list[dict] = []
    seen: set[str] = set()

    for offer in offers:
        offer_id = offer.get("id_offre")
        if not offer_id:
            continue
        offer_id = str(offer_id)
        if offer_id in seen:
            continue
        seen.add(offer_id)
        deduplicated.append(offer)

    return deduplicated


def _min_creation_date(days_back: int) -> str:
    return (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00Z")
