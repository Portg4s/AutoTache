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
