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
    print(f"- Export CSV principal: {summary['export_path'] or 'aucun'}")
    print(f"- Export Excel principal: {summary['xlsx_export_path'] or 'aucun'}")
    print(f"- Export CSV debug: {summary['debug_export_path'] or 'aucun'}")
    print(f"- Export Excel debug: {summary['debug_xlsx_export_path'] or 'aucun'}")
    print(f"- IDs vus: {summary['seen_ids_path']}")
    if debug:
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
        print(f"- url_offre: {_format_debug_value(offer.get('url_offre'))}")


def _format_debug_value(value: Any) -> str:
    if value is None or value == "":
        return "Non specifie"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "aucun"
    return str(value)


if __name__ == "__main__":
    main()
