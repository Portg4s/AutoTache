"""Configuration loading and validation for the local application."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .models import AppConfig


class ConfigFileNotFoundError(FileNotFoundError):
    """Raised when config.yaml does not exist."""


class ConfigValidationError(RuntimeError):
    """Raised when config.yaml exists but is invalid."""


def load_config(config_path: Path = Path("config.yaml")) -> AppConfig:
    """Load and validate the local YAML configuration file."""

    if not config_path.exists():
        raise ConfigFileNotFoundError(
            "Configuration introuvable. Copiez config.example.yaml vers config.yaml, "
            "puis adaptez les mots-cles, communes et filtres."
        )

    with config_path.open("r", encoding="utf-8") as file:
        raw_config: Any = yaml.safe_load(file)

    if not isinstance(raw_config, dict):
        raise ConfigValidationError("config.yaml doit contenir un objet YAML a la racine.")

    try:
        return AppConfig(**raw_config)
    except ValidationError as exc:
        raise ConfigValidationError(f"config.yaml est invalide: {exc}") from exc


def summarize_config(config: AppConfig) -> str:
    """Return a terminal-friendly summary of the loaded configuration."""

    return "\n".join(
        [
            "Configuration chargee avec succes.",
            f"- Mots-cles: {len(config.keywords)}",
            f"- Communes: {', '.join(config.communes)}",
            f"- Distance: {config.distance_km} km",
            f"- Types de contrat: {', '.join(config.contract_types)}",
            f"- Jours analyses: {config.days_back}",
            f"- Stage autorise: {'oui' if config.allow_internship else 'non'}",
            f"- Alternance autorisee: {'oui' if config.allow_apprenticeship else 'non'}",
            f"- Delai API: {config.api.request_delay_seconds} s",
            f"- Retries API: {config.api.max_retries}",
            f"- Source France Travail activee: {'oui' if config.sources.france_travail.enabled else 'non'}",
            f"- Source Arbeitnow activee: {'oui' if config.sources.arbeitnow.enabled else 'non'}",
            f"- Pages max Arbeitnow: {config.sources.arbeitnow.max_pages}",
            f"- Keywords Arbeitnow: {len(config.sources.arbeitnow.keywords)}",
            f"- Localisations Arbeitnow: {len(config.sources.arbeitnow.allowed_locations)}",
            f"- Source Remotive activee: {'oui' if config.sources.remotive.enabled else 'non'}",
            f"- Keywords Remotive: {len(config.sources.remotive.keywords)}",
            f"- Source Adzuna activee: {'oui' if config.sources.adzuna.enabled else 'non'}",
            f"- Pays Adzuna: {config.sources.adzuna.country}",
            f"- Pages max Adzuna: {config.sources.adzuna.max_pages}",
            f"- Resultats par page Adzuna: {config.sources.adzuna.results_per_page}",
            f"- Keywords Adzuna: {len(config.sources.adzuna.keywords)}",
            f"- Location Adzuna: {config.sources.adzuna.location or 'aucune'}",
            f"- Source Jooble activee: {'oui' if config.sources.jooble.enabled else 'non'}",
            f"- Base URL Jooble: {config.sources.jooble.base_url}",
            f"- Pages max Jooble: {config.sources.jooble.max_pages}",
            f"- Keywords Jooble: {len(config.sources.jooble.keywords)}",
            f"- Location Jooble: {config.sources.jooble.location or 'aucune'}",
            f"- Source The Muse activee: {'oui' if config.sources.themuse.enabled else 'non'}",
            f"- Base URL The Muse: {config.sources.themuse.base_url}",
            f"- Pages max The Muse: {config.sources.themuse.max_pages}",
            f"- Resultats par page The Muse: {config.sources.themuse.page_size}",
            f"- Keywords The Muse: {len(config.sources.themuse.keywords)}",
            f"- Location The Muse: {config.sources.themuse.location or 'aucune'}",
            f"- Source JSearch activee: {'oui' if config.sources.jsearch.enabled else 'non'}",
            f"- Base URL JSearch: {config.sources.jsearch.base_url}",
            f"- Host JSearch: {config.sources.jsearch.host}",
            f"- Pages max JSearch: {config.sources.jsearch.max_pages}",
            f"- Queries JSearch: {len(config.sources.jsearch.queries)}",
            f"- Location JSearch: {config.sources.jsearch.location or 'aucune'}",
            f"- Discord active: {'oui' if config.notifications.discord_enabled else 'non'}",
            f"- Notification sans resultat: {'oui' if config.notifications.notify_when_no_results else 'non'}",
            f"- Termes inclus: {len(config.filters.include_terms)}",
            f"- Termes exclus: {len(config.filters.exclude_terms)}",
        ]
    )
