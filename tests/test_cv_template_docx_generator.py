from pathlib import Path

from docx import Document

from scripts.create_cv_template import create_template

from autotache_jobs.cv.profile import load_profile
from autotache_jobs.cv.template_docx_generator import generate_cv_docx_from_template


def test_generates_recruiter_docx_from_template_without_internal_analysis(tmp_path: Path) -> None:
    template_path = create_template(tmp_path / "cv_template.docx")
    profile_path = _write_profile(tmp_path)
    profile_before = profile_path.read_bytes()
    profile = load_profile(profile_path)
    offer = _offer()

    output_path = generate_cv_docx_from_template(
        offer=offer,
        profile=profile,
        template_path=template_path,
        output_dir=tmp_path / "generated",
    )

    assert output_path.exists()
    assert output_path.name == "CV_Bastien_agence_test_integrateur_front_react.docx"
    assert output_path.stat().st_size > 0

    content = _docx_text(output_path)
    assert "Bastien Test" in content
    assert "Profil" in content
    assert "Compétences clés" in content
    assert "HTML" in content
    assert "CSS" in content
    assert "JavaScript" in content
    assert "Expériences" in content
    assert "Projets" in content
    assert "Formation" in content
    assert "Analyse de correspondance" not in content
    assert "Points de prudence" not in content
    assert "Score" not in content
    assert "Decision AutoTache" not in content
    assert "https://example.test/job" not in content
    assert "React (à confirmer" not in content
    assert "Compétences à confirmer" not in content
    assert profile_path.read_bytes() == profile_before


def _write_profile(tmp_path: Path) -> Path:
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        """
profile_summary:
  short: Resume court issu de profile_summary.
identity:
  name: Bastien Test
  title: Developpeur web
  location: Dijon
  email: bastien@example.test
  phone: "0102030405"
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
    return profile_path


def _offer() -> dict[str, object]:
    return {
        "titre": "Integrateur front React",
        "entreprise": "Agence Test",
        "description": "HTML CSS JavaScript React TypeScript",
        "technologies": "HTML, CSS, JavaScript, React, TypeScript",
        "decision": "Pertinent",
        "score_total": 90,
        "localisation": "Dijon",
        "type_contrat": "CDI",
        "source": "France Travail",
        "url_offre": "https://example.test/job",
    }


def _docx_text(path: Path) -> str:
    document = Document(path)
    return "\n".join(paragraph.text for paragraph in document.paragraphs)
