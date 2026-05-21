"""Markdown generation for local targeted CV drafts."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from autotache_jobs.cv.matcher import CvMatch, match_offer_to_profile
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

    match = match_offer_to_profile(offer, profile)
    output_path = target_dir / _safe_filename(offer)
    output_path.write_text(_render_markdown(offer, profile, match), encoding="utf-8")
    return output_path


def draft_summary(offer: dict[str, Any], match: CvMatch) -> str:
    title = str(offer.get("titre") or "Offre sans titre")
    company = str(offer.get("entreprise") or "Entreprise non renseignee")
    return (
        f"Ligne Excel {offer.get('row', '?')} - {company} - {title}. "
        f"Competences fortes: {len(match.strong_present)}, moyennes: {len(match.medium_present)}, "
        f"a confirmer: {len(match.to_confirm_present)}."
    )


def _render_markdown(offer: dict[str, Any], profile: CvProfile, match: CvMatch) -> str:
    offer_title = str(offer.get("titre") or "Titre cible a definir")
    company = str(offer.get("entreprise") or "Entreprise non renseignee")
    profile_summary = _profile_summary(profile.raw)

    return "\n\n".join(
        [
            f"# CV ciblé - {company} - {offer_title}",
            "## CV proposé\n"
            + "\n\n".join(
                [
                    "### Titre proposé\n" + _proposed_title(offer, match),
                    "### Accroche ciblée\n" + _targeted_summary(profile_summary, match),
                    "### Compétences clés\n" + _skills_section(match),
                    "### Expériences à valoriser\n" + _experiences_section(profile.raw),
                    "### Projets à valoriser\n" + _projects_section(profile.raw),
                    "### Formation\n" + _education_section(profile.raw),
                    "### Informations offre\n" + _offer_info_section(offer, company, offer_title),
                ]
            ),
            "## Analyse de correspondance\n"
            + "\n\n".join(
                [
                    "### Correspondance profil/offre\n"
                    + "\n".join(
                        [
                            "- Compétences fortes présentes: " + _inline_list(match.strong_present),
                            "- Compétences moyennes présentes: " + _inline_list(match.medium_present),
                            "- Compétences à confirmer présentes: " + _inline_list(match.to_confirm_present),
                        ]
                    ),
                    "### Mots-clés détectés dans l’offre\n"
                    + _bullet_section(
                        match.offer_keywords_not_in_profile,
                        empty="Aucun mot-clé utile hors profil détecté.",
                    ),
                    "### Points à ne pas sur-vendre\n"
                    + _bullet_section(
                        [f"{skill}: à confirmer, ne pas présenter comme maîtrisé." for skill in match.to_confirm_present],
                        empty="Aucune compétence à confirmer détectée dans l'offre.",
                    ),
                    "### Règles de prudence\n"
                    + "\n".join(
                        [
                            "- Ne jamais inventer une expérience.",
                            "- Ne jamais inventer une compétence.",
                            "- Ne pas présenter une compétence à confirmer comme maîtrisée.",
                            "- Utiliser uniquement les données du profil maître et de l'offre Excel.",
                            "- Ne pas scraper l'URL de l'offre pour cette V1.",
                        ]
                    ),
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


def _profile_summary(raw: dict[str, Any]) -> str:
    profile_summary = raw.get("profile_summary")
    if isinstance(profile_summary, dict):
        short = profile_summary.get("short")
        if isinstance(short, str) and short.strip():
            return short.strip()
    return _profile_text(raw, ["resume", "summary", "profil", "accroche"])


def _profile_text(raw: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _proposed_title(offer: dict[str, Any], match: CvMatch) -> str:
    confirmed = " ".join(match.strong_present + match.medium_present)
    offer_context = " ".join(
        str(offer.get(field) or "")
        for field in ["titre", "description", "technologies"]
    )
    text = _normalize_for_choice(f"{confirmed} {offer_context}")
    confirmed_text = _normalize_for_choice(confirmed)

    has_front = any(skill in text for skill in ["html", "css", "javascript", "front"])
    has_wordpress = "wordpress" in confirmed_text
    has_design = any(skill in text for skill in ["webdesign", "figma", "ux", "ui"])
    has_content = any(skill in text for skill in ["seo", "contenu", "cms", "e-commerce", "ecommerce"])

    if has_wordpress and has_front:
        return "Développeur front-end / Intégrateur WordPress"
    if has_front and has_design:
        return "Développeur web / Intégrateur web / Webdesigner"
    if has_design or has_content:
        return "Profil digital web / UX / contenu"
    if has_front:
        return "Développeur web / Intégrateur web"
    return "Profil web / digital"


def _targeted_summary(profile_summary: str, match: CvMatch) -> str:
    if not profile_summary:
        profile_summary = "Accroche à rédiger depuis le profil maître, sans ajouter d'expérience non documentée."

    confirmed = match.strong_present + match.medium_present
    if confirmed:
        return f"{profile_summary} À orienter vers l'offre avec: {_inline_list(confirmed)}."
    return profile_summary


def _skills_section(match: CvMatch) -> str:
    to_confirm = (
        "\n".join(f"- {skill} (à confirmer, ne pas présenter comme maîtrisé)" for skill in match.to_confirm_present)
        if match.to_confirm_present
        else "- Aucune compétence à confirmer détectée dans l'offre."
    )
    return "\n\n".join(
        [
            "#### Compétences confirmées pertinentes\n"
            + _bullet_section(
                match.strong_present,
                empty="Aucune compétence forte du profil détectée explicitement dans l'offre.",
            ),
            "#### Compétences complémentaires\n"
            + _bullet_section(
                match.medium_present,
                empty="Aucune compétence complémentaire du profil détectée explicitement dans l'offre.",
            ),
            "#### Compétences à confirmer\n" + to_confirm,
        ]
    )


def _experiences_section(raw: dict[str, Any]) -> str:
    blocks = [_format_experience(experience) for experience in _as_list(raw.get("experiences"))]
    blocks = [block for block in blocks if block]
    if not blocks:
        return "- Aucune expérience structurée détectée dans le profil maître."
    return "\n\n".join(blocks)


def _projects_section(raw: dict[str, Any]) -> str:
    blocks: list[str] = []

    for experience in _as_list(raw.get("experiences")):
        if isinstance(experience, dict):
            for project in _as_list(experience.get("projects") or experience.get("projets")):
                formatted = _format_project(project, source="Projet d'expérience")
                if formatted:
                    blocks.append(formatted)

    for key in ["projets", "projects"]:
        for project in _as_list(raw.get(key)):
            formatted = _format_project(project, source="Projet")
            if formatted:
                blocks.append(formatted)

    portfolio = raw.get("portfolio")
    if isinstance(portfolio, dict):
        for project in _as_list(portfolio.get("public_projects")):
            formatted = _format_project(project, source="Portfolio public")
            if formatted:
                blocks.append(formatted)

    if not blocks:
        return "- Aucun projet structuré détecté dans le profil maître."
    return "\n\n".join(blocks)


def _education_section(raw: dict[str, Any]) -> str:
    lines = [_format_education(item) for item in _as_list(raw.get("education"))]
    lines = [line for line in lines if line]
    if not lines:
        return "- Aucune formation structurée détectée dans le profil maître."
    return "\n".join(f"- {line}" for line in lines)


def _offer_info_section(offer: dict[str, Any], company: str, title: str) -> str:
    return "\n".join(
        [
            f"- Titre de l'offre: {title}",
            f"- Entreprise: {company}",
            f"- Source: {offer.get('source') or 'Non renseignee'}",
            f"- Localisation: {offer.get('localisation') or 'Non renseignee'}",
            f"- Type de contrat: {offer.get('type_contrat') or 'Non renseigne'}",
            f"- Decision AutoTache: {offer.get('decision') or 'Non renseignee'}",
            f"- Score: {offer.get('score_total') or 'Non renseigne'}",
            f"- URL: {offer.get('url_offre') or 'Non renseignee'}",
        ]
    )


def _format_experience(experience: Any) -> str:
    if isinstance(experience, str):
        return f"#### {experience}"
    if not isinstance(experience, dict):
        return ""

    title = experience.get("title") or experience.get("titre")
    company = experience.get("company") or experience.get("entreprise")
    period = experience.get("period") or experience.get("periode") or experience.get("dates")
    summary = experience.get("summary") or experience.get("description") or experience.get("resume")
    heading = _join_values([title, company], separator=" - ") or "Expérience"
    if period:
        heading = f"{heading} ({period})"

    bullets = _clean_lines([summary, *_as_list(experience.get("achievements"))])
    body = "\n".join(f"- {bullet}" for bullet in bullets)
    return f"#### {heading}" + (f"\n{body}" if body else "")


def _format_project(project: Any, *, source: str) -> str:
    if isinstance(project, str):
        return f"#### {project}\n- Source: {source}"
    if not isinstance(project, dict):
        return ""

    name = project.get("name") or project.get("title") or project.get("titre") or project.get("nom") or "Projet"
    url = project.get("url")
    bullets = _clean_lines([*_as_list(project.get("highlights")), *_as_list(project.get("bullets"))])
    technologies = _clean_lines(_as_list(project.get("technologies")))

    lines = [f"- Source: {source}"]
    if url:
        lines.append(f"- URL: {url}")
    lines.extend(f"- {bullet}" for bullet in bullets)
    if technologies:
        lines.append("- Technologies: " + _inline_list(technologies))
    return f"#### {name}\n" + "\n".join(lines)


def _format_education(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()
    if not isinstance(item, dict):
        return ""

    degree = item.get("degree") or item.get("diploma") or item.get("title") or item.get("formation")
    school = item.get("school") or item.get("institution") or item.get("etablissement")
    location = item.get("location") or item.get("lieu")
    period = item.get("period") or item.get("years") or item.get("dates")
    if not period:
        start = item.get("start") or item.get("from") or item.get("debut")
        end = item.get("end") or item.get("to") or item.get("fin")
        period = _join_values([start, end], separator=" -> ")

    return _join_values([degree, school, location, period], separator=" — ")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _join_values(value: Any, *, separator: str = ", ") -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return separator.join(
            str(item).strip()
            for item in value.values()
            if item is not None and str(item).strip()
        )
    if isinstance(value, list):
        return separator.join(
            str(item).strip()
            for item in value
            if item is not None and str(item).strip()
        )
    return str(value).strip()


def _clean_lines(values: list[Any]) -> list[str]:
    lines: list[str] = []
    for value in values:
        text = _join_values(value)
        if text:
            lines.append(text)
    return lines


def _bullet_section(items: list[str], *, empty: str) -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def _inline_list(items: list[str]) -> str:
    return ", ".join(items) if items else "Aucune"


def _normalize_for_choice(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents).strip()
