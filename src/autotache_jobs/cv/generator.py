"""Markdown generation for local targeted CV drafts."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from autotache_jobs.cv.builder import (
    CvExperience,
    CvProject,
    TargetedCvData,
    build_targeted_cv_data,
)
from autotache_jobs.cv.matcher import CvMatch
from autotache_jobs.cv.profile import CvProfile


SECTIONS = [
    "CV proposé",
    "Analyse de correspondance",
]


def generate_cv_draft(
    *,
    offer: dict[str, Any],
    profile: CvProfile,
    output_dir: str | Path = "generated_cv",
) -> Path:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    cv_data = build_targeted_cv_data(offer, profile)
    output_path = target_dir / _safe_filename(offer)
    output_path.write_text(_render_markdown(cv_data), encoding="utf-8")
    return output_path


def draft_summary(offer: dict[str, Any], match: CvMatch) -> str:
    title = str(offer.get("titre") or "Offre sans titre")
    company = str(offer.get("entreprise") or "Entreprise non renseignee")
    return (
        f"Ligne Excel {offer.get('row', '?')} - {company} - {title}. "
        f"Competences fortes: {len(match.strong_present)}, moyennes: {len(match.medium_present)}, "
        f"a confirmer: {len(match.to_confirm_present)}."
    )


def _render_markdown(cv_data: TargetedCvData) -> str:
    offer = cv_data.offer_info

    return "\n\n".join(
        [
            f"# CV ciblé - {offer.company} - {offer.title}",
            "## CV proposé\n"
            + "\n\n".join(
                [
                    "### Titre proposé\n" + cv_data.proposed_title,
                    "### Accroche ciblée\n" + cv_data.targeted_summary,
                    "### Compétences clés\n" + _skills_section(cv_data),
                    "### Expériences à valoriser\n" + _experiences_section(cv_data.experiences),
                    "### Projets à valoriser\n" + _projects_section(cv_data.projects),
                    "### Formation\n" + _education_section(cv_data.education),
                    "### Informations offre\n" + _offer_info_section(cv_data),
                ]
            ),
            "## Analyse de correspondance\n"
            + "\n\n".join(
                [
                    "### Correspondance profil/offre\n"
                    + "\n".join(
                        [
                            "- Compétences fortes présentes: " + _inline_list(cv_data.skills.confirmed),
                            "- Compétences moyennes présentes: " + _inline_list(cv_data.skills.complementary),
                            "- Compétences à confirmer présentes: " + _inline_list(cv_data.skills.to_confirm),
                        ]
                    ),
                    "### Mots-clés détectés dans l’offre\n"
                    + _bullet_section(
                        cv_data.analysis.keywords,
                        empty="Aucun mot-clé utile hors profil détecté.",
                    ),
                    "### Points à ne pas sur-vendre\n"
                    + _bullet_section(
                        cv_data.analysis.oversell_points,
                        empty="Aucune compétence à confirmer détectée dans l'offre.",
                    ),
                    "### Règles de prudence\n" + _bullet_section(cv_data.analysis.caution_rules, empty=""),
                ]
            ),
        ]
    ) + "\n"


def _safe_filename(offer: dict[str, Any]) -> str:
    company = _slug(offer.get("entreprise") or "entreprise")
    title = _slug(offer.get("titre") or "offre")
    return f"cv_draft_{company}_{title}.md"


def _slug(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value).strip().lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:80] or "non_renseigne"


def _skills_section(cv_data: TargetedCvData) -> str:
    to_confirm = (
        "\n".join(
            f"- {skill} (à confirmer, ne pas présenter comme maîtrisé)"
            for skill in cv_data.skills.to_confirm
        )
        if cv_data.skills.to_confirm
        else "- Aucune compétence à confirmer détectée dans l'offre."
    )
    return "\n\n".join(
        [
            "#### Compétences confirmées pertinentes\n"
            + _bullet_section(
                cv_data.skills.confirmed,
                empty="Aucune compétence forte du profil détectée explicitement dans l'offre.",
            ),
            "#### Compétences complémentaires\n"
            + _bullet_section(
                cv_data.skills.complementary,
                empty="Aucune compétence complémentaire du profil détectée explicitement dans l'offre.",
            ),
            "#### Compétences à confirmer\n" + to_confirm,
        ]
    )


def _experiences_section(experiences: list[CvExperience]) -> str:
    blocks = [_format_experience(experience) for experience in experiences]
    if not blocks:
        return "- Aucune expérience structurée détectée dans le profil maître."
    return "\n\n".join(blocks)


def _projects_section(projects: list[CvProject]) -> str:
    blocks = [_format_project(project) for project in projects]
    if not blocks:
        return "- Aucun projet structuré détecté dans le profil maître."
    return "\n\n".join(blocks)


def _education_section(education: list[str]) -> str:
    if not education:
        return "- Aucune formation structurée détectée dans le profil maître."
    return "\n".join(f"- {line}" for line in education)


def _offer_info_section(cv_data: TargetedCvData) -> str:
    offer = cv_data.offer_info
    return "\n".join(
        [
            f"- Titre de l'offre: {offer.title}",
            f"- Entreprise: {offer.company}",
            f"- Source: {offer.source}",
            f"- Localisation: {offer.location}",
            f"- Type de contrat: {offer.contract_type}",
            f"- Decision AutoTache: {offer.decision}",
            f"- Score: {offer.score}",
            f"- URL: {offer.url}",
        ]
    )


def _format_experience(experience: CvExperience) -> str:
    body = "\n".join(f"- {bullet}" for bullet in experience.bullets)
    return f"#### {experience.heading}" + (f"\n{body}" if body else "")


def _format_project(project: CvProject) -> str:
    lines = [f"- Source: {project.source}"]
    if project.url:
        lines.append(f"- URL: {project.url}")
    lines.extend(f"- {bullet}" for bullet in project.bullets)
    if project.technologies:
        lines.append("- Technologies: " + _inline_list(project.technologies))
    return f"#### {project.name}\n" + "\n".join(lines)


def _bullet_section(items: list[str], *, empty: str) -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def _inline_list(items: list[str]) -> str:
    return ", ".join(items) if items else "Aucune"
