from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from docx import Document

from autotache_jobs.cv.docx_generator import generate_cv_docx
from autotache_jobs.cv.profile import load_profile


def test_generates_docx_from_targeted_cv_data_without_modifying_sources(tmp_path: Path) -> None:
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

    profile_before = profile_path.read_bytes()
    offer_before = deepcopy(offer)
    profile = load_profile(profile_path)

    output_path = generate_cv_docx(offer=offer, profile=profile, output_dir=tmp_path / "generated")

    assert output_path.exists()
    assert output_path.parent == tmp_path / "generated"
    assert output_path.name == "CV_Bastien_agence_test_integrateur_front_react.docx"
    assert output_path.stat().st_size > 0

    document = Document(output_path)
    content = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert "Bastien Test" in content
    assert "Developpeur web | Dijon | bastien@example.test | 0102030405" in content
    assert "CV ciblé" in content
    assert "Profil ciblé" in content
    assert "Titre proposé" in content
    assert "Accroche ciblée" in content
    assert "Compétences clés" in content
    assert "Compétences confirmées pertinentes" in content
    assert "Compétences complémentaires" in content
    assert "Compétences à confirmer" in content
    assert "React (à confirmer, ne pas présenter comme maîtrisé)" in content
    assert "Expériences" in content
    assert "Projets" in content
    assert "Formation" in content
    assert "Analyse de correspondance" in content
    assert "Points de prudence" in content
    assert "Agence Test" in content
    assert "Dijon | CDI | Non renseignee | Score 90" in content
    assert "URL: https://example.test/job" in content

    assert profile_path.read_bytes() == profile_before
    assert offer == offer_before
