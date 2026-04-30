"""CLI entrypoint for AutoTache job search."""

from __future__ import annotations

from pathlib import Path

from .config import ConfigFileNotFoundError, ConfigValidationError, load_config, summarize_config
from .env import EnvValidationError, load_france_travail_env
from .runner import run_job_search


def main() -> None:
    """Load local env/config, run the job search flow, and print a summary."""

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
    )
    print("Recherche terminee.")
    print(f"- Offres brutes: {summary['total_raw']}")
    print(f"- Offres normalisees: {summary['total_normalized']}")
    print(f"- Offres pertinentes: {summary['total_relevant']}")
    print(f"- Nouvelles offres exportees: {summary['total_new']}")
    print(f"- Export CSV: {summary['export_path'] or 'aucun'}")
    print(f"- IDs vus: {summary['seen_ids_path']}")


if __name__ == "__main__":
    main()
