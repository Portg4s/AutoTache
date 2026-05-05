"""Main orchestration for the AutoTache job search flow."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time
from typing import Any

from .exporter import export_offers_to_csv, export_offers_to_tracking_xlsx, export_offers_to_xlsx
from .france_travail_client import FranceTravailClient
from .notifications import send_discord_summary
from .scoring import DECISION_RELEVANT, DECISION_REVIEW, score_offer
from .sources.arbeitnow import ArbeitnowSource
from .sources.base import SourceResult, SourceStats
from .sources.france_travail import FranceTravailSource
from .sources.remotive import RemotiveSource
from .storage import filter_new_offers, load_seen_offer_ids, save_seen_offer_ids, update_seen_ids


def run_job_search(
    config: Any,
    env_settings: Any,
    client: Any | None = None,
    data_dir: str | Path = "data",
    export_dir: str | Path = "exports",
    include_debug_offers: bool = False,
    sleep_func: Any = time.sleep,
    discord_sender: Any = send_discord_summary,
    arbeitnow_client: Any | None = None,
    remotive_client: Any | None = None,
) -> dict[str, Any]:
    """Run the full local job search pipeline and return a summary."""

    source_results = _collect_source_results(
        config,
        env_settings,
        france_travail_client=client,
        arbeitnow_client=arbeitnow_client,
        remotive_client=remotive_client,
        sleep_func=sleep_func,
    )
    raw_offers = [offer for result in source_results for offer in result.raw_offers]
    normalized_offers = [offer for result in source_results for offer in result.normalized_offers]
    normalized_offers = [_with_score(offer) for offer in normalized_offers]
    unique_normalized_offers = _deduplicate_by_id(normalized_offers)
    relevant_offers = [offer for offer in normalized_offers if offer["is_relevant"] is True]
    deduplicated_relevant_offers = _deduplicate_by_id(relevant_offers)
    exportable_offers = [offer for offer in normalized_offers if _is_exportable_decision(offer)]
    deduplicated_exportable_offers = _deduplicate_by_id(exportable_offers)

    seen_ids_path = Path(data_dir) / "seen_offer_ids.json"
    main_export_dir = Path(export_dir) / "offres"
    debug_export_dir = Path(export_dir) / "debug"
    seen_ids = load_seen_offer_ids(seen_ids_path)
    new_offers = filter_new_offers(deduplicated_exportable_offers, seen_ids)
    export_path = export_offers_to_csv(new_offers, main_export_dir)
    xlsx_export_path = export_offers_to_xlsx(new_offers, main_export_dir) if export_path else None
    tracking_xlsx_export_path = export_offers_to_tracking_xlsx(new_offers, main_export_dir)
    debug_export_path = _export_debug_offers(unique_normalized_offers, debug_export_dir) if include_debug_offers else None
    debug_xlsx_export_path = (
        _export_debug_offers_to_xlsx(unique_normalized_offers, debug_export_dir)
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
        "total_exportable": len(deduplicated_exportable_offers),
        "total_new": len(new_offers),
        "export_path": str(export_path) if export_path else None,
        "xlsx_export_path": str(xlsx_export_path) if xlsx_export_path else None,
        "tracking_xlsx_export_path": str(tracking_xlsx_export_path) if tracking_xlsx_export_path else None,
        "debug_export_path": str(debug_export_path) if debug_export_path else None,
        "debug_xlsx_export_path": str(debug_xlsx_export_path) if debug_xlsx_export_path else None,
        "seen_ids_path": str(seen_ids_path),
        "decision_counts": _count_decisions(unique_normalized_offers),
        "total_decision_pertinent": _count_decisions(unique_normalized_offers).get(DECISION_RELEVANT, 0),
        "total_decision_a_verifier": _count_decisions(unique_normalized_offers).get(DECISION_REVIEW, 0),
        "total_decision_rejete": _count_rejected_decisions(unique_normalized_offers),
        "best_score": _best_score(unique_normalized_offers),
        "sources_enabled": _enabled_source_names(config),
        "source_counts": _source_counts(source_results),
        "source_stats": _source_stats(config, source_results),
        "source_status": "collected" if source_results else "no_sources_enabled",
        "discord_enabled": bool(config.notifications.discord_enabled),
        "discord_sent": False,
        "discord_status": "disabled",
        "discord_error": None,
    }
    if include_debug_offers:
        summary["debug_offers"] = unique_normalized_offers
    _notify_discord_if_needed(config, env_settings, summary, discord_sender)
    return summary


def _collect_source_results(
    config: Any,
    env_settings: Any,
    france_travail_client: Any | None = None,
    arbeitnow_client: Any | None = None,
    remotive_client: Any | None = None,
    sleep_func: Any = time.sleep,
) -> list[SourceResult]:
    source_results: list[SourceResult] = []

    if config.sources.france_travail.enabled:
        active_client = france_travail_client or FranceTravailClient(
            client_id=env_settings.client_id,
            client_secret=env_settings.client_secret,
            scope=env_settings.scope,
            token_url=env_settings.token_url,
            api_base_url=env_settings.api_base_url,
            max_retries=config.api.max_retries,
        )
        source_results.append(FranceTravailSource(config, active_client, sleep_func=sleep_func).collect())

    if config.sources.arbeitnow.enabled:
        source_results.append(
            ArbeitnowSource(
                max_pages=config.sources.arbeitnow.max_pages,
                keywords=config.sources.arbeitnow.keywords,
                allowed_locations=config.sources.arbeitnow.allowed_locations,
                http_client=arbeitnow_client,
            ).collect()
        )

    if config.sources.remotive.enabled:
        source_results.append(
            RemotiveSource(
                keywords=config.sources.remotive.keywords,
                http_client=remotive_client,
            ).collect()
        )

    return source_results


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


def _with_score(offer: dict) -> dict:
    scoring = score_offer(offer)
    return {
        **offer,
        "score_total": scoring["score_total"],
        "decision": scoring["decision"],
        "score_reason": scoring["score_reason"],
        "score_details": scoring["score_details"],
    }


def _is_exportable_decision(offer: dict) -> bool:
    return offer.get("decision") in {DECISION_RELEVANT, DECISION_REVIEW}


def _count_decisions(offers: list[dict]) -> dict[str, int]:
    counts = {"Pertinent": 0, "À vérifier": 0, "Rejeté": 0}
    for offer in offers:
        decision = offer.get("decision")
        if decision in counts:
            counts[decision] += 1
    return counts


def _count_rejected_decisions(offers: list[dict]) -> int:
    return sum(1 for offer in offers if str(offer.get("decision", "")).startswith("Rejet"))


def _best_score(offers: list[dict]) -> int | None:
    scores = [offer.get("score_total") for offer in offers if isinstance(offer.get("score_total"), int)]
    return max(scores) if scores else None


def _enabled_source_names(config: Any) -> list[str]:
    enabled = []
    if config.sources.france_travail.enabled:
        enabled.append("France Travail")
    if config.sources.arbeitnow.enabled:
        enabled.append("Arbeitnow")
    if config.sources.remotive.enabled:
        enabled.append("Remotive")
    return enabled


def _source_counts(source_results: list[SourceResult]) -> dict[str, dict[str, int]]:
    return {
        result.source_name: {
            "raw": len(result.raw_offers),
            "normalized": len(result.normalized_offers),
        }
        for result in source_results
    }


def _source_stats(config: Any, source_results: list[SourceResult]) -> dict[str, dict[str, int | bool]]:
    stats = {
        "France Travail": _stats_dict(SourceStats(enabled=bool(config.sources.france_travail.enabled), fetched=0, kept=0, filtered=0)),
        "Arbeitnow": _stats_dict(SourceStats(enabled=bool(config.sources.arbeitnow.enabled), fetched=0, kept=0, filtered=0)),
        "Remotive": _stats_dict(SourceStats(enabled=bool(config.sources.remotive.enabled), fetched=0, kept=0, filtered=0)),
    }
    for result in source_results:
        stats[result.source_name] = _stats_dict(result.stats)
    return stats


def _stats_dict(stats: SourceStats) -> dict[str, int | bool]:
    return {
        "enabled": stats.enabled,
        "fetched": stats.fetched,
        "kept": stats.kept,
        "filtered": stats.filtered,
    }


def _export_debug_offers(offers: list[dict], export_dir: str | Path) -> Path | None:
    filename = f"debug_offres_{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv"
    return export_offers_to_csv(offers, export_dir, filename=filename)


def _export_debug_offers_to_xlsx(offers: list[dict], export_dir: str | Path) -> Path | None:
    filename = f"debug_offres_{datetime.now().strftime('%Y-%m-%d_%H%M')}.xlsx"
    return export_offers_to_xlsx(offers, export_dir, filename=filename)


def _notify_discord_if_needed(config: Any, env_settings: Any, summary: dict[str, Any], discord_sender: Any) -> None:
    if not config.notifications.discord_enabled:
        return

    summary["discord_status"] = "skipped_no_relevant_offers"
    should_notify = summary["total_new"] > 0 or config.notifications.notify_when_no_results
    if not should_notify:
        return

    result = discord_sender(env_settings.discord_webhook_url, summary)
    summary["discord_sent"] = bool(result.get("sent"))
    summary["discord_status"] = result.get("status")
    summary["discord_error"] = result.get("error")
