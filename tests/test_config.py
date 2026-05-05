from pathlib import Path

import pytest

from autotache_jobs.config import ConfigFileNotFoundError, load_config, summarize_config


def test_load_config_requires_existing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigFileNotFoundError):
        load_config(tmp_path / "config.yaml")


def test_load_config_validates_example_shape(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
keywords:
  - wordpress
communes:
  - "75056"
distance_km: 20
contract_types:
  - CDI
days_back: 7
allow_internship: false
allow_apprenticeship: false
filters:
  exclude_terms:
    - data scientist
  include_terms:
    - wordpress
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.keywords == ["wordpress"]
    assert config.communes == ["75056"]
    assert config.api.request_delay_seconds == 0.8
    assert config.api.max_retries == 3
    assert config.sources.france_travail.enabled is True
    assert config.sources.arbeitnow.enabled is False
    assert config.sources.arbeitnow.max_pages == 1
    assert config.sources.remotive.enabled is False
    assert config.sources.remotive.keywords == []
    assert config.sources.adzuna.enabled is False
    assert config.sources.adzuna.country == "fr"
    assert config.sources.adzuna.max_pages == 1
    assert config.sources.adzuna.results_per_page == 20
    assert config.sources.adzuna.keywords == []
    assert config.sources.adzuna.location == ""
    assert config.sources.jooble.enabled is False
    assert config.sources.jooble.base_url == "https://fr.jooble.org/api"
    assert config.sources.jooble.max_pages == 1
    assert config.sources.jooble.keywords == []
    assert config.sources.jooble.location == ""
    assert "Configuration chargee avec succes." in summarize_config(config)


def test_load_config_reads_api_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
keywords:
  - wordpress
communes:
  - "75056"
distance_km: 20
contract_types:
  - CDI
days_back: 7
api:
  request_delay_seconds: 1.2
  max_retries: 2
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.api.request_delay_seconds == 1.2
    assert config.api.max_retries == 2


def test_load_config_reads_sources_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
keywords:
  - wordpress
communes:
  - "75056"
distance_km: 20
contract_types:
  - CDI
days_back: 7
sources:
  france_travail:
    enabled: false
  arbeitnow:
    enabled: true
    max_pages: 2
    keywords:
      - frontend
      - " "
      - wordpress
    allowed_locations:
      - France
      - Remote
  remotive:
    enabled: true
    keywords:
      - figma
      - " "
      - frontend
  adzuna:
    enabled: true
    country: fr
    max_pages: 3
    results_per_page: 15
    keywords:
      - wordpress
      - " "
      - frontend
    location: Dijon
  jooble:
    enabled: true
    base_url: "https://fr.jooble.org/api"
    max_pages: 2
    keywords:
      - web
      - " "
      - developpeur
    location: Dijon
""",
        encoding="utf-8",
    )

    config = load_config(config_path)
    summary = summarize_config(config)

    assert config.sources.france_travail.enabled is False
    assert config.sources.arbeitnow.enabled is True
    assert config.sources.arbeitnow.max_pages == 2
    assert config.sources.arbeitnow.keywords == ["frontend", "wordpress"]
    assert config.sources.arbeitnow.allowed_locations == ["France", "Remote"]
    assert config.sources.remotive.enabled is True
    assert config.sources.remotive.keywords == ["figma", "frontend"]
    assert config.sources.adzuna.enabled is True
    assert config.sources.adzuna.country == "fr"
    assert config.sources.adzuna.max_pages == 3
    assert config.sources.adzuna.results_per_page == 15
    assert config.sources.adzuna.keywords == ["wordpress", "frontend"]
    assert config.sources.adzuna.location == "Dijon"
    assert config.sources.jooble.enabled is True
    assert config.sources.jooble.base_url == "https://fr.jooble.org/api"
    assert config.sources.jooble.max_pages == 2
    assert config.sources.jooble.keywords == ["web", "developpeur"]
    assert config.sources.jooble.location == "Dijon"
    assert "- Source France Travail activee: non" in summary
    assert "- Source Arbeitnow activee: oui" in summary
    assert "- Pages max Arbeitnow: 2" in summary
    assert "- Keywords Arbeitnow: 2" in summary
    assert "- Localisations Arbeitnow: 2" in summary
    assert "- Source Remotive activee: oui" in summary
    assert "- Keywords Remotive: 2" in summary
    assert "- Source Adzuna activee: oui" in summary
    assert "- Pays Adzuna: fr" in summary
    assert "- Pages max Adzuna: 3" in summary
    assert "- Resultats par page Adzuna: 15" in summary
    assert "- Keywords Adzuna: 2" in summary
    assert "- Location Adzuna: Dijon" in summary
    assert "- Source Jooble activee: oui" in summary
    assert "- Base URL Jooble: https://fr.jooble.org/api" in summary
    assert "- Pages max Jooble: 2" in summary
    assert "- Keywords Jooble: 2" in summary
    assert "- Location Jooble: Dijon" in summary
