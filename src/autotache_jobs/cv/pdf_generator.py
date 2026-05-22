"""PDF generation for recruiter-ready targeted CVs."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from autotache_jobs.cv.builder import TargetedCvData, build_targeted_cv_data
from autotache_jobs.cv.profile import CvProfile


DEFAULT_TEMPLATE_PATH = Path("templates/cv/recruiter_cv.html.j2")
DEFAULT_CSS_PATH = Path("templates/cv/recruiter_cv.css")


def generate_cv_pdf(
    *,
    offer: dict[str, Any],
    profile: CvProfile,
    output_dir: str | Path = "generated_cv",
    template_path: str | Path = DEFAULT_TEMPLATE_PATH,
    css_path: str | Path = DEFAULT_CSS_PATH,
    keep_html: bool = False,
) -> Path:
    """Render a recruiter CV PDF from a normalized offer and local profile."""

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    cv_data = build_targeted_cv_data(offer, profile)
    output_path = target_dir / _safe_filename(cv_data)
    html = render_cv_html(cv_data=cv_data, template_path=template_path, css_path=css_path)

    if keep_html:
        output_path.with_suffix(".html").write_text(html, encoding="utf-8")

    _render_pdf_with_playwright(html, output_path)
    return output_path


def render_cv_html(
    *,
    cv_data: TargetedCvData,
    template_path: str | Path = DEFAULT_TEMPLATE_PATH,
    css_path: str | Path = DEFAULT_CSS_PATH,
) -> str:
    """Render the recruiter HTML document without writing personal data to disk."""

    template_file = Path(template_path)
    css = Path(css_path).read_text(encoding="utf-8")
    environment = Environment(
        loader=FileSystemLoader(str(template_file.parent or Path("."))),
        autoescape=select_autoescape(("html", "xml", "j2")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = environment.get_template(template_file.name)
    return template.render(cv=cv_data, css=css, skills=_visible_skills(cv_data), project_links=_project_links(cv_data))


def _render_pdf_with_playwright(html: str, output_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    browser = None
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.emulate_media(media="print")
            page.set_content(html, wait_until="networkidle")
            page.pdf(
                path=str(output_path),
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
            )
        finally:
            if browser is not None:
                browser.close()


def _visible_skills(cv_data: TargetedCvData) -> list[str]:
    return _dedupe(cv_data.skills.confirmed + cv_data.skills.complementary)[:16]


def _project_links(cv_data: TargetedCvData) -> list[tuple[str, str]]:
    links = [(project.name, project.url) for project in cv_data.projects if project.url]
    return links[:5]


def _safe_filename(cv_data: TargetedCvData) -> str:
    company = _slug(cv_data.offer_info.company)
    title = _slug(cv_data.offer_info.title)
    return f"CV_Bastien_{company}_{title}.pdf"


def _slug(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value).strip().lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:80] or "non_renseigne"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = " ".join(str(value).strip().split())
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result
