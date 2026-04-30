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
    assert "Configuration chargee avec succes." in summarize_config(config)
