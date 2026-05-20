from pathlib import Path

from openpyxl import Workbook, load_workbook

from autotache_jobs.cv.generator import SECTIONS, generate_cv_draft
from autotache_jobs.cv.offer_reader import read_offer_from_xlsx
from autotache_jobs.cv.profile import load_profile


def test_generates_markdown_without_modifying_sources(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        """
profile_summary:
  short: Resume court issu de profile_summary.
competences_fortes:
  - HTML
  - CSS
to_confirm:
  - React
experiences:
  - title: Integrateur web
    company: Studio Local
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
    xlsx_path = tmp_path / "debug.xlsx"
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["titre", "entreprise", "description", "technologies", "decision", "score_total"])
    worksheet.append(["Integrateur front React", "Agence Test", "HTML CSS React", "HTML, CSS, React", "Pertinent", 90])
    workbook.save(xlsx_path)

    profile_before = profile_path.read_bytes()
    xlsx_before_rows = load_workbook(xlsx_path).active.max_row
    profile = load_profile(profile_path)
    offer = read_offer_from_xlsx(xlsx_path, 2)

    output_path = generate_cv_draft(offer=offer, profile=profile, output_dir=tmp_path / "generated")

    content = output_path.read_text(encoding="utf-8")
    assert output_path.parent == tmp_path / "generated"
    assert "Agence Test" in content
    assert "Integrateur front React" in content
    for section in SECTIONS:
        assert f"## {section}" in content
    assert "Resume court issu de profile_summary." in content
    assert "Integrateur web - Studio Local" in content
    assert "Livraison de pages accessibles" in content
    assert "Refonte vitrine" in content
    assert "Portfolio public test" in content
    assert "https://example.test/portfolio" in content
    assert "React: à confirmer, ne pas présenter comme maîtrisé." in content
    assert "Ne jamais inventer une expérience." in content
    assert profile_path.read_bytes() == profile_before
    assert load_workbook(xlsx_path).active.max_row == xlsx_before_rows
