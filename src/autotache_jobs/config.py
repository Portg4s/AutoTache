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
            f"- Termes inclus: {len(config.filters.include_terms)}",
            f"- Termes exclus: {len(config.filters.exclude_terms)}",
        ]
    )
