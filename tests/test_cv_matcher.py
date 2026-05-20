from pathlib import Path

from autotache_jobs.cv.matcher import match_offer_to_profile
from autotache_jobs.cv.profile import load_profile


def test_detects_profile_skill_levels_without_overselling_to_confirm(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        """
competences_fortes:
  - HTML
competences_moyennes:
  - JavaScript
to_confirm:
  - React
""",
        encoding="utf-8",
    )
    profile = load_profile(profile_path)
    offer = {
        "titre": "Developpeur front-end React",
        "description": "Integration HTML avec JavaScript et React.",
        "technologies": "HTML, JavaScript, React, TypeScript",
        "score_reason": "Bon alignement frontend.",
        "type_contrat": "CDI",
    }

    match = match_offer_to_profile(offer, profile)

    assert match.strong_present == ["HTML"]
    assert match.medium_present == ["JavaScript"]
    assert match.to_confirm_present == ["React"]
    assert "React" not in match.strong_present
    assert "React" not in match.medium_present
    assert "TypeScript" in match.offer_keywords_not_in_profile

