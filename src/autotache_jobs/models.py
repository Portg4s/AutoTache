"""Internal data models for local configuration and environment."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class ConfigFilters(BaseModel):
    """Filtering terms loaded from the local config file."""

    exclude_terms: list[str] = Field(default_factory=list)
    include_terms: list[str] = Field(default_factory=list)

    @field_validator("exclude_terms", "include_terms")
    @classmethod
    def clean_terms(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value and value.strip()]


class ApiConfig(BaseModel):
    """API pacing settings loaded from the local config file."""

    request_delay_seconds: float = Field(default=0.8, ge=0)
    max_retries: int = Field(default=3, ge=0)


class AppConfig(BaseModel):
    """Validated local application configuration."""

    keywords: list[str]
    communes: list[str]
    distance_km: int = Field(ge=0)
    contract_types: list[str] = Field(default_factory=list)
    days_back: int = Field(gt=0)
    allow_internship: bool = False
    allow_apprenticeship: bool = False
    api: ApiConfig = Field(default_factory=ApiConfig)
    filters: ConfigFilters = Field(default_factory=ConfigFilters)

    @field_validator("keywords", "communes", "contract_types")
    @classmethod
    def clean_non_empty_list(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value and value.strip()]
        if not cleaned:
            raise ValueError("la liste ne doit pas etre vide")
        return cleaned


class FranceTravailEnv(BaseModel):
    """France Travail credentials and endpoint settings loaded from the environment."""

    client_id: str
    client_secret: str
    scope: str = "api_offresdemploiv2 o2dsoffre"
    token_url: str = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
    api_base_url: str = "https://api.francetravail.io/partenaire/offresdemploi/v2"

    @field_validator("client_id", "client_secret")
    @classmethod
    def required_secret_placeholder(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("valeur requise")
        return value.strip()


class RuntimePaths(BaseModel):
    """Important local paths used by the application."""

    project_root: Path
    config_path: Path
    env_path: Path
