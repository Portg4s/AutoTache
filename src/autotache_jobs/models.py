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


class NotificationConfig(BaseModel):
    """Optional notification settings loaded from the local config file."""

    discord_enabled: bool = False
    notify_when_no_results: bool = False


class SourceToggleConfig(BaseModel):
    """Enable or disable one offer source."""

    enabled: bool = True


class ArbeitnowSourceConfig(BaseModel):
    """Arbeitnow source settings."""

    enabled: bool = False
    max_pages: int = Field(default=1, ge=1)
    keywords: list[str] = Field(default_factory=list)
    allowed_locations: list[str] = Field(default_factory=list)

    @field_validator("keywords", "allowed_locations")
    @classmethod
    def clean_terms(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value and value.strip()]


class RemotiveSourceConfig(BaseModel):
    """Remotive source settings."""

    enabled: bool = False
    keywords: list[str] = Field(default_factory=list)

    @field_validator("keywords")
    @classmethod
    def clean_terms(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value and value.strip()]


class AdzunaSourceConfig(BaseModel):
    """Adzuna source settings."""

    enabled: bool = False
    country: str = "fr"
    max_pages: int = Field(default=1, ge=1)
    results_per_page: int = Field(default=20, ge=1)
    keywords: list[str] = Field(default_factory=list)
    location: str = ""

    @field_validator("keywords")
    @classmethod
    def clean_terms(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value and value.strip()]

    @field_validator("country", "location")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return value.strip() if value else ""


class SourcesConfig(BaseModel):
    """Offer sources loaded from the local config file."""

    france_travail: SourceToggleConfig = Field(default_factory=SourceToggleConfig)
    arbeitnow: ArbeitnowSourceConfig = Field(default_factory=ArbeitnowSourceConfig)
    remotive: RemotiveSourceConfig = Field(default_factory=RemotiveSourceConfig)
    adzuna: AdzunaSourceConfig = Field(default_factory=AdzunaSourceConfig)


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
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    filters: ConfigFilters = Field(default_factory=ConfigFilters)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)

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
    discord_webhook_url: str = ""
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""

    @field_validator("client_id", "client_secret")
    @classmethod
    def required_secret_placeholder(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("valeur requise")
        return value.strip()

    @field_validator("discord_webhook_url", "adzuna_app_id", "adzuna_app_key")
    @classmethod
    def clean_optional_secret(cls, value: str) -> str:
        return value.strip() if value else ""


class RuntimePaths(BaseModel):
    """Important local paths used by the application."""

    project_root: Path
    config_path: Path
    env_path: Path
