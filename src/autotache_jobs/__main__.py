"""CLI entrypoint for AutoTache job search."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from .config import ConfigFileNotFoundError, ConfigValidationError, load_config, summarize_config
from .env import EnvValidationError, load_france_travail_env
from .runner import run_job_search


def main(argv: list[str] | None = None) -> None:
    """Load local env/config, run the job search flow, and print a summary."""

    args = sys.argv[1:] if argv is None else argv
    debug = _is_debug_mode(args)
    project_root = Path.cwd()
    try:
        env_settings = load_france_travail_env(project_root / ".env")
        config = load_config(project_root / "config.yaml")
    except (EnvValidationError, ConfigFileNotFoundError, ConfigValidationError) as exc:
        raise SystemExit(str(exc)) from exc

    print(summarize_config(config))
    summary = run_job_search(
        config=config,
        env_settings=env_settings,
        data_dir=project_root / "data",
        export_dir=project_root / "exports",
        include_debug_offers=debug,
    )
    print("Recherche terminee.")
    print(f"- Offres brutes: {summary['total_raw']}")
    print(f"- Offres normalisees: {summary['total_normalized']}")
    print(f"- Offres normalisees uniques: {summary['total_unique_normalized']}")
    print(f"- Offres pertinentes: {summary['total_relevant']}")
    print(f"- Nouvelles offres exportees: {summary['total_new']}")
    _print_source_stats(summary.get("source_stats", {}))
    print(f"- Export CSV principal: {summary['export_path'] or 'aucun'}")
    print(f"- Export Excel principal: {summary['xlsx_export_path'] or 'aucun'}")
    print(f"- Export CSV debug: {summary['debug_export_path'] or 'aucun'}")
    print(f"- Export Excel debug: {summary['debug_xlsx_export_path'] or 'aucun'}")
    print(f"- IDs vus: {summary['seen_ids_path']}")
    print(f"- Discord active: {'oui' if summary['discord_enabled'] else 'non'}")
    print(f"- Discord envoye: {'oui' if summary['discord_sent'] else 'non'}")
    print(f"- Discord statut: {summary['discord_status'] or 'aucun'}")
    if summary["discord_error"]:
        print(f"- Discord erreur: {summary['discord_error']}")
    if debug:
        decision_counts = summary.get("decision_counts", {})
        print(f"- Offres decision Pertinent: {decision_counts.get('Pertinent', 0)}")
        print(f"- Offres decision A verifier: {decision_counts.get('À vérifier', 0)}")
        print(f"- Offres decision Rejete: {decision_counts.get('Rejeté', 0)}")
        _print_debug_offers(summary.get("debug_offers", []))


def _is_debug_mode(args: list[str]) -> bool:
    return any(arg in {"--debug", "debug"} for arg in args)


def _print_debug_offers(offers: list[dict[str, Any]]) -> None:
    print("Apercu debug des offres normalisees:")
    if not offers:
        print("- aucune offre normalisee")
        return

    for index, offer in enumerate(offers, start=1):
        print(f"Offre {index}")
        print(f"- id_offre: {_format_debug_value(offer.get('id_offre'))}")
        print(f"- titre: {_format_debug_value(offer.get('titre'))}")
        print(f"- entreprise: {_format_debug_value(offer.get('entreprise'))}")
        print(f"- localisation: {_format_debug_value(offer.get('localisation'))}")
        print(f"- type_contrat: {_format_debug_value(offer.get('type_contrat'))}")
        print(f"- technologies: {_format_debug_value(offer.get('technologies'))}")
        print(f"- is_relevant: {_format_debug_value(offer.get('is_relevant'))}")
        print(f"- relevance_reason: {_format_debug_value(offer.get('relevance_reason'))}")
        print(f"- matched_keywords: {_format_debug_value(offer.get('matched_keywords'))}")
        print(f"- excluded_by: {_format_debug_value(offer.get('excluded_by'))}")
        print(f"- decision: {_format_debug_value(offer.get('decision'))}")
        print(f"- score_total: {_format_debug_value(offer.get('score_total'))}")
        print(f"- score_reason: {_format_debug_value(offer.get('score_reason'))}")
        print(f"- score_details: {_format_score_details(offer.get('score_details'))}")
        print(f"- url_offre: {_format_debug_value(offer.get('url_offre'))}")


def _print_source_stats(source_stats: dict[str, dict[str, Any]]) -> None:
    print("Sources :")
    if not source_stats:
        print("- aucune source renseignee")
        return

    for source_name, stats in source_stats.items():
        print(
            f"- {source_name} : active {'oui' if stats.get('enabled') else 'non'}, "
            f"recuperees {stats.get('fetched', 0)}, "
            f"conservees {stats.get('kept', 0)}, "
            f"filtrees {stats.get('filtered', 0)}"
        )


def _format_debug_value(value: Any) -> str:
    if value is None or value == "":
        return "Non specifie"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "aucun"
    return str(value)


def _format_score_details(value: Any) -> str:
    if not isinstance(value, dict):
        return "Non specifie"

    parts = []
    for key in ["technologies", "titre", "domaine_metier", "localisation", "teletravail", "contrat"]:
        detail = value.get(key)
        if isinstance(detail, dict):
            parts.append(f"{key}={detail.get('score', 0)}")
    penalties = value.get("penalties")
    if isinstance(penalties, dict) and penalties.get("score", 0):
        parts.append(f"penalites={penalties.get('score', 0)}")
    if value.get("eliminatory_reason"):
        parts.append(f"eliminatoire={value['eliminatory_reason']}")

    return ", ".join(parts) if parts else "aucun"


if __name__ == "__main__":
    main()
