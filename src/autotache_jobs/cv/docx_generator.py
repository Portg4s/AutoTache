"""DOCX generation for local targeted CV drafts."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from docx import Document
from docx.shared import Inches, Pt

from autotache_jobs.cv.builder import CvExperience, CvProject, TargetedCvData, build_targeted_cv_data
from autotache_jobs.cv.profile import CvProfile


def generate_cv_docx(
    *,
    offer: dict[str, Any],
    profile: CvProfile,
    output_dir: str | Path = "generated_cv",
) -> Path:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    cv_data = build_targeted_cv_data(offer, profile)
    output_path = target_dir / _safe_filename(cv_data)
    document = _build_document(cv_data)
    document.save(output_path)
    return output_path


def _build_document(cv_data: TargetedCvData) -> Document:
    document = Document()
    _set_base_style(document)

    offer = cv_data.offer_info
    document.add_paragraph(f"CV ciblé - {offer.company} - {offer.title}", style="Title")

    document.add_heading("CV proposé", level=1)
    document.add_heading("Titre proposé", level=2)
    document.add_paragraph(cv_data.proposed_title)
    document.add_heading("Accroche ciblée", level=2)
    document.add_paragraph(cv_data.targeted_summary)
    document.add_heading("Compétences clés", level=2)
    _add_skills(document, cv_data)
    document.add_heading("Expériences à valoriser", level=2)
    _add_experiences(document, cv_data.experiences)
    document.add_heading("Projets à valoriser", level=2)
    _add_projects(document, cv_data.projects)
    document.add_heading("Formation", level=2)
    _add_bullets(document, cv_data.education, empty="Aucune formation structurée détectée dans le profil maître.")

    document.add_heading("Informations offre", level=1)
    _add_bullets(
        document,
        [
            f"Titre de l'offre: {offer.title}",
            f"Entreprise: {offer.company}",
            f"Source: {offer.source}",
            f"Localisation: {offer.location}",
            f"Type de contrat: {offer.contract_type}",
            f"Decision AutoTache: {offer.decision}",
            f"Score: {offer.score}",
            f"URL: {offer.url}",
        ],
    )

    document.add_heading("Analyse de correspondance", level=1)
    document.add_heading("Correspondance profil/offre", level=2)
    _add_bullets(
        document,
        [
            "Compétences fortes présentes: " + _inline_list(cv_data.skills.confirmed),
            "Compétences moyennes présentes: " + _inline_list(cv_data.skills.complementary),
            "Compétences à confirmer présentes: " + _inline_list(cv_data.skills.to_confirm),
        ],
    )
    document.add_heading("Mots-clés détectés dans l’offre", level=2)
    _add_bullets(document, cv_data.analysis.keywords, empty="Aucun mot-clé utile hors profil détecté.")
    document.add_heading("Points à ne pas sur-vendre", level=2)
    _add_bullets(
        document,
        cv_data.analysis.oversell_points,
        empty="Aucune compétence à confirmer détectée dans l'offre.",
    )
    document.add_heading("Règles de prudence", level=2)
    _add_bullets(document, cv_data.analysis.caution_rules)

    return document


def _set_base_style(document: Document) -> None:
    for section in document.sections:
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    normal = document.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)


def _add_skills(document: Document, cv_data: TargetedCvData) -> None:
    document.add_heading("Compétences confirmées pertinentes", level=3)
    _add_bullets(
        document,
        cv_data.skills.confirmed,
        empty="Aucune compétence forte du profil détectée explicitement dans l'offre.",
    )
    document.add_heading("Compétences complémentaires", level=3)
    _add_bullets(
        document,
        cv_data.skills.complementary,
        empty="Aucune compétence complémentaire du profil détectée explicitement dans l'offre.",
    )
    document.add_heading("Compétences à confirmer", level=3)
    if cv_data.skills.to_confirm:
        _add_bullets(
            document,
            [
                f"{skill} (à confirmer, ne pas présenter comme maîtrisé)"
                for skill in cv_data.skills.to_confirm
            ],
        )
    else:
        _add_bullets(document, [], empty="Aucune compétence à confirmer détectée dans l'offre.")


def _add_experiences(document: Document, experiences: list[CvExperience]) -> None:
    if not experiences:
        _add_bullets(document, [], empty="Aucune expérience structurée détectée dans le profil maître.")
        return

    for experience in experiences:
        document.add_heading(experience.heading, level=3)
        _add_bullets(document, experience.bullets)


def _add_projects(document: Document, projects: list[CvProject]) -> None:
    if not projects:
        _add_bullets(document, [], empty="Aucun projet structuré détecté dans le profil maître.")
        return

    for project in projects:
        document.add_heading(project.name, level=3)
        lines = [f"Source: {project.source}"]
        if project.url:
            lines.append(f"URL: {project.url}")
        lines.extend(project.bullets)
        if project.technologies:
            lines.append("Technologies: " + _inline_list(project.technologies))
        _add_bullets(document, lines)


def _add_bullets(document: Document, items: list[str], *, empty: str | None = None) -> None:
    if not items:
        if empty is not None:
            document.add_paragraph(empty, style="List Bullet")
        return

    for item in items:
        document.add_paragraph(item, style="List Bullet")


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
    return ", ".join(items) if items else "Aucune"
