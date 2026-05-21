from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import subprocess
import sys

from docx import Document

from autotache_jobs.cv.docx_generator import generate_cv_docx
from autotache_jobs.cv.profile import load_profile


def test_generates_draft_docx_with_internal_analysis_by_default(tmp_path: Path) -> None:
    profile_path = _write_profile(tmp_path)
    offer = _offer()

    profile_before = profile_path.read_bytes()
    offer_before = deepcopy(offer)
    profile = load_profile(profile_path)

    output_path = generate_cv_docx(offer=offer, profile=profile, output_dir=tmp_path / "generated")

    assert output_path.exists()
    assert output_path.parent == tmp_path / "generated"
    assert output_path.name == "CV_Draft_Bastien_agence_test_integrateur_front_react.docx"
    assert output_path.stat().st_size > 0

    content = _docx_text(output_path)
    assert "Bastien Test" in content
    assert "Developpeur web | Dijon | bastien@example.test | 0102030405" in content
    assert "CV ciblé" in content
    assert "À orienter vers l'offre avec" in content
    assert "Profil ciblé" in content
    assert "Compétences clés" in content
    assert "Compétences à confirmer" in content
    assert "React (à confirmer, ne pas présenter comme maîtrisé)" in content
    assert "Expériences" in content
    assert "Projets" in content
    assert "Formation" in content
    assert "Informations offre" in content
    assert "Analyse de correspondance" in content
    assert "Points de prudence" in content
    assert "Dijon | CDI | France Travail | Score 90" in content
    assert "Decision AutoTache: Pertinent" in content
    assert "URL: https://example.test/job" in content

    assert profile_path.read_bytes() == profile_before
    assert offer == offer_before


def test_generates_recruiter_docx_without_internal_analysis(tmp_path: Path) -> None:
    profile_path = _write_profile(tmp_path)
    offer = _offer()
    profile = load_profile(profile_path)

    output_path = generate_cv_docx(
        offer=offer,
        profile=profile,
        output_dir=tmp_path / "generated",
        mode="recruiter",
    )

    assert output_path.exists()
    assert output_path.name == "CV_Bastien_agence_test_integrateur_front_react.docx"
    assert output_path.stat().st_size > 0

    content = _docx_text(output_path)
    assert "CV - Bastien Test" in content
    assert "Resume court issu de profile_summary." in content
    assert "approche orientée utilisateur" in content
    assert "HTML, CSS et JavaScript" in content
    assert "À orienter vers l'offre avec" not in content
    assert "Aucune compétence complémentaire" not in content
    assert "Aucune compétence à confirmer" not in content
    assert "Profil" in content
    assert "Profil ciblé" not in content
    assert "Compétences clés" in content
    assert "HTML • CSS • JavaScript" in content
    assert "Compétences confirmées pertinentes" not in content
    assert "Compétences complémentaires" not in content
    assert "Expériences" in content
    assert "Projets" in content
    assert "Formation" in content
    assert "Analyse de correspondance" not in content
    assert "Points de prudence" not in content
    assert "Règles de prudence" not in content
    assert "Mots-clés détectés" not in content
    assert "à ne pas sur-vendre" not in content
    assert "Score 90" not in content
    assert "Decision AutoTache" not in content
    assert "France Travail" not in content
    assert "https://example.test/job" not in content
    assert "React (à confirmer" not in content
    assert "Compétences à confirmer" not in content


def test_generate_cv_docx_rejects_invalid_mode(tmp_path: Path) -> None:
    profile = load_profile(_write_profile(tmp_path))

    try:
        generate_cv_docx(offer=_offer(), profile=profile, output_dir=tmp_path / "generated", mode="invalid")
    except ValueError as exc:
        assert "--mode doit etre 'draft' ou 'recruiter'." in str(exc)
    else:
        raise AssertionError("generate_cv_docx should reject invalid modes")


def test_generate_cv_docx_cli_rejects_invalid_mode() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_cv_docx.py",
            "--debug-xlsx",
            "missing.xlsx",
            "--top",
            "1",
            "--mode",
            "invalid",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "invalid choice" in result.stderr


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
