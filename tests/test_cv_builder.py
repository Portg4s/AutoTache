from pathlib import Path

from autotache_jobs.cv.builder import build_targeted_cv_data
from autotache_jobs.cv.profile import load_profile


def test_build_targeted_cv_data_exposes_reusable_cv_sections(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        """
profile_summary:
  short: Resume court issu de profile_summary.
competences_fortes:
  - HTML
  - CSS
competences_moyennes:
  - JavaScript
to_confirm:
  - React
experiences:
  - title: Integrateur web
    company: Studio Local
    period: 2021 -> 2024
    summary: Integration responsive documentee dans le profil.
    achievements:
      - Livraison de pages accessibles
    projects:
      - name: Refonte vitrine
        bullets:
          - Composants HTML CSS
        technologies:
          - HTML
          - CSS
education:
  - degree: DUT Informatique
    school: IUT
    location: Dijon
    period: 2018 -> 2020
portfolio:
  public_projects:
    - name: Portfolio public test
      url: https://example.test/portfolio
      highlights:
        - Interface responsive
      technologies:
        - WordPress
""",
        encoding="utf-8",
    )
    profile = load_profile(profile_path)
    offer = {
        "titre": "Integrateur front React",
        "entreprise": "Agence Test",
        "description": "HTML CSS JavaScript React TypeScript",
        "technologies": "HTML, CSS, JavaScript, React, TypeScript",
        "decision": "Pertinent",
        "score_total": 90,
        "localisation": "Dijon",
        "type_contrat": "CDI",
        "url_offre": "https://example.test/job",
    }

    cv_data = build_targeted_cv_data(offer, profile)

    assert cv_data.proposed_title
    assert "Resume court issu de profile_summary." in cv_data.targeted_summary
    assert "À orienter vers l'offre avec" in cv_data.targeted_summary
    assert "Resume court issu de profile_summary." in cv_data.recruiter_summary
    assert "approche orientée utilisateur" in cv_data.recruiter_summary
    assert "HTML, CSS et JavaScript" in cv_data.recruiter_summary
    assert "React" not in cv_data.recruiter_summary
    assert "À orienter vers l'offre avec" not in cv_data.recruiter_summary
    assert cv_data.skills.confirmed == ["HTML", "CSS"]
    assert cv_data.skills.complementary == ["JavaScript"]
    assert cv_data.skills.to_confirm == ["React"]
    assert cv_data.experiences[0].heading == "Integrateur web - Studio Local (2021 -> 2024)"
    assert "Livraison de pages accessibles" in cv_data.experiences[0].bullets
    assert cv_data.projects[0].name == "Refonte vitrine"
    assert cv_data.projects[0].technologies == ["HTML", "CSS"]
    assert cv_data.projects[1].name == "Portfolio public test"
    assert cv_data.projects[1].url == "https://example.test/portfolio"
    assert cv_data.education == ["DUT Informatique — IUT — Dijon — 2018 -> 2020"]
    assert cv_data.offer_info.company == "Agence Test"
    assert cv_data.offer_info.title == "Integrateur front React"
    assert cv_data.offer_info.url == "https://example.test/job"
    assert "TypeScript" in cv_data.analysis.keywords
    assert cv_data.analysis.oversell_points == [
        "React: à confirmer, ne pas présenter comme maîtrisé."
    ]
    assert "Ne jamais inventer une expérience." in cv_data.analysis.caution_rules
