from pathlib import Path

import pytest

from autotache_jobs.cv.profile import ProfileError, load_profile


def test_loads_minimal_yaml_profile(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        """
resume: Integrateur web oriente interfaces.
competences_fortes:
  - HTML
  - CSS
competences_moyennes:
  - JavaScript
to_confirm:
  - React
""",
        encoding="utf-8",
    )

    profile = load_profile(profile_path)

    assert profile.strong_skills == ["HTML", "CSS"]
    assert profile.medium_skills == ["JavaScript"]
    assert profile.to_confirm == ["React"]
    assert profile.raw["resume"] == "Integrateur web oriente interfaces."


def test_missing_profile_has_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ProfileError, match="Profil introuvable"):
        load_profile(tmp_path / "absent.yaml")

