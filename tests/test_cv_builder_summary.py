from pathlib import Path

from autotache_jobs.cv.builder import build_targeted_cv_data
from autotache_jobs.cv.profile import load_profile


def test_recruiter_summary_prioritizes_business_skills_over_secondary_tools(tmp_path: Path) -> None:
    cv_data = _build_cv_data_for_skills(
        tmp_path,
        strong_skills=["Webdesign", "SEO", "Git"],
        offer_text="Webdesign SEO Git",
    )

    assert "Webdesign et SEO" in cv_data.recruiter_summary
    assert "Git" not in cv_data.recruiter_summary


def test_recruiter_summary_limits_business_skills_and_avoids_git_when_possible(tmp_path: Path) -> None:
    cv_data = _build_cv_data_for_skills(
        tmp_path,
        strong_skills=["WordPress", "JavaScript", "Webdesign", "Git"],
        offer_text="WordPress JavaScript Webdesign Git",
    )

    assert "WordPress, JavaScript et Webdesign" in cv_data.recruiter_summary
    assert "Git" not in cv_data.recruiter_summary


def test_recruiter_summary_can_use_git_when_no_business_skill_is_available(tmp_path: Path) -> None:
    cv_data = _build_cv_data_for_skills(
        tmp_path,
        strong_skills=["Git"],
        offer_text="Git",
    )

    assert "Git" in cv_data.recruiter_summary


def test_recruiter_summary_never_uses_to_confirm_skills(tmp_path: Path) -> None:
    cv_data = _build_cv_data_for_skills(
        tmp_path,
        strong_skills=["Webdesign"],
        to_confirm=["React"],
        offer_text="Webdesign React",
    )

    assert "Webdesign" in cv_data.recruiter_summary
    assert "React" not in cv_data.recruiter_summary


def _build_cv_data_for_skills(
    tmp_path: Path,
    *,
    strong_skills: list[str],
    offer_text: str,
    to_confirm: list[str] | None = None,
):
    profile_path = tmp_path / ("profile_" + "_".join(str(len(skill)) for skill in strong_skills) + ".yaml")
    profile_path.write_text(
        "\n".join(
            [
                "profile_summary:",
                "  short: Resume court issu de profile_summary.",
                "competences_fortes:",
                *[f"  - {skill}" for skill in strong_skills],
                "to_confirm:",
                *[f"  - {skill}" for skill in (to_confirm or [])],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    profile = load_profile(profile_path)
    offer = {
        "titre": offer_text,
        "description": offer_text,
        "technologies": offer_text,
        "entreprise": "Agence Test",
    }
    return build_targeted_cv_data(offer, profile)
