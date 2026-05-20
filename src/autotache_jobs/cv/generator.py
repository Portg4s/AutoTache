"""Markdown generation for local targeted CV drafts."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from autotache_jobs.cv.matcher import CvMatch, match_offer_to_profile
from autotache_jobs.cv.profile import CvProfile


SECTIONS = [
    "Titre ciblé",
    "Offre ciblée",
    "Résumé professionnel adapté",
    "Compétences à mettre en avant",
    "Expériences/projets à prioriser",
    "Mots-clés détectés dans l’offre",
    "Correspondance profil/offre",
    "Points à ne pas sur-vendre",
    "Règles de prudence",
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
    title = str(offer.get("titre") or "Titre cible a definir")
    company = str(offer.get("entreprise") or "Entreprise non renseignee")
    profile_summary = _profile_summary(profile.raw)
    experiences = _profile_items(profile.raw)

    return "\n\n".join(
        [
            f"# Brouillon CV ciblé - {company} - {title}",
            "## Titre ciblé\n" + title,
            "## Offre ciblée\n"
            + "\n".join(
                [
                    f"- Entreprise: {company}",
                    f"- Source: {offer.get('source') or 'Non renseignee'}",
                    f"- Localisation: {offer.get('localisation') or 'Non renseignee'}",
                    f"- Type de contrat: {offer.get('type_contrat') or 'Non renseigne'}",
                    f"- Decision AutoTache: {offer.get('decision') or 'Non renseignee'}",
                    f"- Score: {offer.get('score_total') or 'Non renseigne'}",
                    f"- URL: {offer.get('url_offre') or 'Non renseignee'}",
                ]
            ),
            "## Résumé professionnel adapté\n"
            + (
                profile_summary
                if profile_summary
                else "Résumé à rédiger depuis le profil maître, sans ajouter d'expérience non documentée."
            ),
            "## Compétences à mettre en avant\n"
            + _bullet_section(
                match.strong_present + match.medium_present,
                empty="Aucune compétence du profil détectée explicitement dans l'offre.",
            ),
            "## Expériences/projets à prioriser\n"
            + _bullet_section(
                experiences,
                empty="Aucune expérience/projet structuré détecté dans le profil maître.",
            ),
            "## Mots-clés détectés dans l’offre\n"
            + _bullet_section(
                match.offer_keywords_not_in_profile,
                empty="Aucun mot-clé hors profil détecté.",
            ),
            "## Correspondance profil/offre\n"
            + "\n".join(
                [
                    "- Compétences fortes présentes: " + _inline_list(match.strong_present),
                    "- Compétences moyennes présentes: " + _inline_list(match.medium_present),
                    "- Compétences à confirmer présentes: " + _inline_list(match.to_confirm_present),
                ]
            ),
            "## Points à ne pas sur-vendre\n"
            + _bullet_section(
                [f"{skill}: à confirmer, ne pas présenter comme maîtrisé." for skill in match.to_confirm_present],
                empty="Aucune compétence à confirmer détectée dans l'offre.",
            ),
            "## Règles de prudence\n"
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


def _profile_items(raw: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for experience in _as_list(raw.get("experiences")):
        items.extend(_format_experience(experience))

    for key in ["projets", "projects"]:
        for project in _as_list(raw.get(key)):
            formatted = _format_project(project, prefix="Projet")
            if formatted:
                items.append(formatted)

    portfolio = raw.get("portfolio")
    if isinstance(portfolio, dict):
        for project in _as_list(portfolio.get("public_projects")):
            formatted = _format_project(project, prefix="Portfolio")
            if formatted:
                items.append(formatted)

    return items


def _format_experience(experience: Any) -> list[str]:
    if isinstance(experience, str):
        return [experience]
    if not isinstance(experience, dict):
        return []

    items: list[str] = []
    title = experience.get("title") or experience.get("titre")
    company = experience.get("company") or experience.get("entreprise")
    summary = experience.get("summary") or experience.get("description") or experience.get("resume")
    achievements = _join_values(experience.get("achievements"))

    experience_text = _join_values(
        [
            _join_values([title, company], separator=" - "),
            summary,
            achievements,
        ],
        separator=": ",
    )
    if experience_text:
        items.append(experience_text)

    for project in _as_list(experience.get("projects") or experience.get("projets")):
        formatted = _format_project(project, prefix="Projet associé")
        if formatted:
            items.append(formatted)

    return items


def _format_project(project: Any, *, prefix: str) -> str:
    if isinstance(project, str):
        return project
    if not isinstance(project, dict):
        return ""

    name = project.get("name") or project.get("title") or project.get("titre") or project.get("nom")
    parts = [
        _join_values([prefix, name], separator=": "),
        project.get("url"),
        _join_values(project.get("highlights")),
        _join_values(project.get("bullets")),
        _join_values(project.get("technologies")),
    ]
    return _join_values(parts, separator=" | ")


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


def _bullet_section(items: list[str], *, empty: str) -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def _inline_list(items: list[str]) -> str:
    return ", ".join(items) if items else "Aucune"
