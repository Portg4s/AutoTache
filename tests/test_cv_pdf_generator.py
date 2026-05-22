from __future__ import annotations

from pathlib import Path

from autotache_jobs.cv.builder import build_targeted_cv_data
from autotache_jobs.cv.pdf_generator import generate_cv_pdf, render_cv_html
from autotache_jobs.cv.profile import load_profile


def test_renders_recruiter_html_without_internal_analysis(tmp_path: Path) -> None:
    profile = load_profile(_write_profile(tmp_path))
    cv_data = build_targeted_cv_data(_offer(), profile)

    html = render_cv_html(cv_data=cv_data)

    assert "Bastien Test" in html
    assert "Permis B" in html
    assert "Profil" in html
    assert "Expériences" in html
    assert "Projets sélectionnés" in html
    assert "Compétences clés" in html
    assert "Formation" in html
    assert "Liens" in html
    assert "Resume court issu de profile_summary." in html
    assert "HTML" in html
    assert "CSS" in html
    assert "JavaScript" in html
    assert "Portfolio public test" in html
    assert "https://example.test/portfolio" in html
    assert "Decision AutoTache" not in html
    assert "Pertinent" not in html
    assert "Score" not in html
    assert "score" not in html
    assert "France Travail" not in html
    assert "https://example.test/job" not in html
    assert "React" not in html
    assert "à confirmer" not in html
    assert "Analyse" not in html
    assert "&#34;" not in html
    assert "font-family: Arial, \"Segoe UI\", \"Liberation Sans\", sans-serif;" in html


def test_generate_cv_pdf_writes_expected_pdf_and_keeps_html_when_requested(tmp_path: Path, monkeypatch) -> None:
    profile = load_profile(_write_profile(tmp_path))
    calls = []

    def fake_render_pdf(html: str, output_path: Path) -> None:
        calls.append((html, output_path))
        output_path.write_bytes(b"%PDF fake")

    monkeypatch.setattr("autotache_jobs.cv.pdf_generator._render_pdf_with_playwright", fake_render_pdf)

    output_path = generate_cv_pdf(
        offer=_offer(),
        profile=profile,
        output_dir=tmp_path / "generated",
        keep_html=True,
    )

    assert output_path == tmp_path / "generated" / "CV_Bastien_agence_test_integrateur_front_react.pdf"
    assert output_path.read_bytes() == b"%PDF fake"
    assert output_path.with_suffix(".html").exists()
    assert "Bastien Test" in output_path.with_suffix(".html").read_text(encoding="utf-8")
    assert calls[0][1] == output_path


def test_generate_cv_pdf_removes_html_by_default(tmp_path: Path, monkeypatch) -> None:
    profile = load_profile(_write_profile(tmp_path))

    def fake_render_pdf(html: str, output_path: Path) -> None:
        output_path.write_bytes(b"%PDF fake")

    monkeypatch.setattr("autotache_jobs.cv.pdf_generator._render_pdf_with_playwright", fake_render_pdf)

    output_path = generate_cv_pdf(offer=_offer(), profile=profile, output_dir=tmp_path / "generated")

    assert output_path.exists()
    assert not output_path.with_suffix(".html").exists()


def test_generate_cv_pdf_uses_safe_filename(tmp_path: Path, monkeypatch) -> None:
    profile = load_profile(_write_profile(tmp_path))
    offer = {
        **_offer(),
        "titre": "Intégrateur Web / UI UX",
        "entreprise": "Agence Côte-d'Or & Co",
    }

    def fake_render_pdf(html: str, output_path: Path) -> None:
        output_path.write_bytes(b"%PDF fake")

    monkeypatch.setattr("autotache_jobs.cv.pdf_generator._render_pdf_with_playwright", fake_render_pdf)

    output_path = generate_cv_pdf(offer=offer, profile=profile, output_dir=tmp_path / "generated")

    assert output_path.name == "CV_Bastien_agence_cote_d_or_co_integrateur_web_ui_ux.pdf"


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
  permis: Permis B
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
