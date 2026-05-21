"""DOCX generation from a local docxtpl recruiter template."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate

from autotache_jobs.cv.builder import TargetedCvData, build_targeted_cv_data
from autotache_jobs.cv.profile import CvProfile


def generate_cv_docx_from_template(
    *,
    offer: dict[str, Any],
    profile: CvProfile,
    template_path: str | Path,
    output_dir: str | Path = "generated_cv",
) -> Path:
    cv_data = build_targeted_cv_data(offer, profile)
    return render_cv_docx_template(
        cv_data=cv_data,
        template_path=template_path,
        output_dir=output_dir,
    )


def render_cv_docx_template(
    *,
    cv_data: TargetedCvData,
    template_path: str | Path,
    output_dir: str | Path = "generated_cv",
) -> Path:
    template_file = Path(template_path)
    if not template_file.exists():
        raise ValueError(f"Template DOCX introuvable: {template_file}")

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    output_path = target_dir / _safe_filename(cv_data)
    template = DocxTemplate(template_file)
    template.render(build_template_context(cv_data))
    template.save(output_path)
    return output_path


def build_template_context(cv_data: TargetedCvData) -> dict[str, Any]:
    projects = [
        {
            "name": project.name,
            "url": project.url,
            "bullets": project.bullets,
            "technologies": _inline_list(project.technologies),
        }
        for project in cv_data.projects
    ]
    return {
        "identity": {
            "name": cv_data.identity.name,
            "title": cv_data.identity.title,
            "location": cv_data.identity.location,
            "email": cv_data.identity.email,
            "phone": cv_data.identity.phone,
        },
        "proposed_title": cv_data.proposed_title,
        "targeted_summary": cv_data.recruiter_summary,
        "skills": cv_data.skills.confirmed + cv_data.skills.complementary,
        "experiences": [
            {"heading": experience.heading, "bullets": experience.bullets}
            for experience in cv_data.experiences
        ],
        "projects": projects,
        "education": cv_data.education,
    }


def _safe_filename(cv_data: TargetedCvData) -> str:
    company = _slug(cv_data.offer_info.company)
    title = _slug(cv_data.offer_info.title)
    return f"CV_Bastien_{company}_{title}.docx"


def _slug(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value).strip().lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:80] or "non_renseigne"


def _inline_list(items: list[str]) -> str:
    return ", ".join(items) if items else ""
