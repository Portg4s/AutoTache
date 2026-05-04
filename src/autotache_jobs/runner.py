"""Main orchestration for the AutoTache job search flow."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import time
from typing import Any

from .exporter import export_offers_to_csv, export_offers_to_xlsx
from .france_travail_client import FranceTravailClient
from .normalizer import normalize_france_travail_offer
from .storage import filter_new_offers, load_seen_offer_ids, save_seen_offer_ids, update_seen_ids


def run_job_search(
    config: Any,
    env_settings: Any,
    client: Any | None = None,
    data_dir: str | Path = "data",
    export_dir: str | Path = "exports",
    include_debug_offers: bool = False,
    sleep_func: Any = time.sleep,
) -> dict[str, Any]:
    """Run the full local job search pipeline and return a summary."""

    active_client = client or FranceTravailClient(
        client_id=env_settings.client_id,
        client_secret=env_settings.client_secret,
        scope=env_settings.scope,
        token_url=env_settings.token_url,
        api_base_url=env_settings.api_base_url,
        max_retries=config.api.max_retries,
    )

    raw_offers = _collect_raw_offers(config, active_client, sleep_func=sleep_func)
    normalized_offers = [
        normalize_france_travail_offer(
            raw_offer,
            allow_stage=config.allow_internship,
            allow_alternance=config.allow_apprenticeship,
        )
        for raw_offer in raw_offers
    ]
    unique_normalized_offers = _deduplicate_by_id(normalized_offers)
    relevant_offers = [offer for offer in normalized_offers if offer["is_relevant"] is True]
    deduplicated_relevant_offers = _deduplicate_by_id(relevant_offers)

    seen_ids_path = Path(data_dir) / "seen_offer_ids.json"
    seen_ids = load_seen_offer_ids(seen_ids_path)
    new_offers = filter_new_offers(deduplicated_relevant_offers, seen_ids)
    export_path = export_offers_to_csv(new_offers, export_dir)
    xlsx_export_path = export_offers_to_xlsx(new_offers, export_dir) if export_path else None
    debug_export_path = _export_debug_offers(unique_normalized_offers, export_dir) if include_debug_offers else None
    debug_xlsx_export_path = (
        _export_debug_offers_to_xlsx(unique_normalized_offers, export_dir)
        if include_debug_offers and debug_export_path
        else None
    )

    if new_offers:
        save_seen_offer_ids(seen_ids_path, update_seen_ids(seen_ids, new_offers))

    summary = {
        "total_raw": len(raw_offers),
        "total_normalized": len(normalized_offers),
        "total_unique_normalized": len(unique_normalized_offers),
        "total_relevant": len(deduplicated_relevant_offers),
        "total_new": len(new_offers),
        "export_path": str(export_path) if export_path else None,
        "xlsx_export_path": str(xlsx_export_path) if xlsx_export_path else None,
        "debug_export_path": str(debug_export_path) if debug_export_path else None,
        "debug_xlsx_export_path": str(debug_xlsx_export_path) if debug_xlsx_export_path else None,
        "seen_ids_path": str(seen_ids_path),
    }
    if include_debug_offers:
        summary["debug_offers"] = unique_normalized_offers
    return summary


def _collect_raw_offers(config: Any, client: Any, sleep_func: Any = time.sleep) -> list[dict]:
    raw_offers: list[dict] = []
    min_creation_date, max_creation_date = _creation_date_range(config.days_back)
    is_first_call = True

    for keyword in config.keywords:
        for commune in config.communes:
            for contract_type in config.contract_types:
                if not is_first_call and config.api.request_delay_seconds > 0:
                    sleep_func(config.api.request_delay_seconds)
                is_first_call = False
                results = client.search_offers(
                    keyword=keyword,
                    commune=commune,
                    distance=config.distance_km,
                    type_contrat=contract_type,
                    min_creation_date=min_creation_date,
                    max_creation_date=max_creation_date,
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


def _export_debug_offers(offers: list[dict], export_dir: str | Path) -> Path | None:
    filename = f"debug_offres_{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv"
    return export_offers_to_csv(offers, export_dir, filename=filename)


def _export_debug_offers_to_xlsx(offers: list[dict], export_dir: str | Path) -> Path | None:
    filename = f"debug_offres_{datetime.now().strftime('%Y-%m-%d_%H%M')}.xlsx"
    return export_offers_to_xlsx(offers, export_dir, filename=filename)


def _creation_date_range(days_back: int) -> tuple[str, str]:
    now = datetime.now()
    min_creation_date = (now - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00Z")
    max_creation_date = now.strftime("%Y-%m-%dT23:59:59Z")
    return min_creation_date, max_creation_date
