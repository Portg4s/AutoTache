"""Environment variable loading for the local application."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from .models import FranceTravailEnv


class EnvValidationError(RuntimeError):
    """Raised when required France Travail variables are missing."""


def load_france_travail_env(env_path: Path = Path(".env")) -> FranceTravailEnv:
    """Load and validate France Travail environment variables.

    This does not contact France Travail. It only reads local environment values.
    """

    load_dotenv(env_path)

    raw_values = {
        "client_id": os.getenv("FRANCE_TRAVAIL_CLIENT_ID", ""),
        "client_secret": os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET", ""),
        "scope": os.getenv("FRANCE_TRAVAIL_SCOPE", "api_offresdemploiv2 o2dsoffre"),
        "token_url": os.getenv(
            "FRANCE_TRAVAIL_TOKEN_URL",
            "https://entreprise.francetravail.fr/connexion/oauth2/access_token",
        ),
        "api_base_url": os.getenv(
            "FRANCE_TRAVAIL_API_BASE_URL",
            "https://api.francetravail.io/partenaire/offresdemploi/v2",
        ),
        "discord_webhook_url": os.getenv("DISCORD_WEBHOOK_URL", ""),
        "adzuna_app_id": os.getenv("ADZUNA_APP_ID", ""),
        "adzuna_app_key": os.getenv("ADZUNA_APP_KEY", ""),
    }

    try:
        return FranceTravailEnv(**raw_values)
    except ValidationError as exc:
        raise EnvValidationError(
            "Variables France Travail manquantes ou invalides. "
            "Verifiez FRANCE_TRAVAIL_CLIENT_ID et FRANCE_TRAVAIL_CLIENT_SECRET "
            "dans votre fichier .env local."
        ) from exc
