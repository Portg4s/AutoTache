"""Build reusable targeted CV data before rendering it to a file format."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from autotache_jobs.cv.matcher import match_offer_to_profile
from autotache_jobs.cv.profile import CvProfile


HIGH_PRIORITY_SUMMARY_SKILLS = {
    "wordpress",
    "elementor",
    "divi",
    "woocommerce",
    "webdesign",
    "seo",
    "figma",
    "ui design",
    "ux design",
    "html",
    "css",
    "javascript",
    "identite visuelle",
    "graphisme",
    "maquette",
    "e-commerce",
    "ecommerce",
    "newsletter",
    "reseaux sociaux",
}
LOW_PRIORITY_SUMMARY_SKILLS = {
    "git",
    "github",
    "suite office",
    "canva",
    "suite adobe",
}
MAX_RECRUITER_SUMMARY_SKILLS = 4


@dataclass(frozen=True)
class CvOfferInfo:
    title: str
    company: str
    source: str
    location: str
    contract_type: str
    decision: str
    score: str
    url: str


@dataclass(frozen=True)
class CvIdentity:
    name: str
    title: str
    location: str
    email: str
    phone: str


@dataclass(frozen=True)
class CvSkills:
    confirmed: list[str]
    complementary: list[str]
    to_confirm: list[str]


@dataclass(frozen=True)
class CvExperience:
    heading: str
    bullets: list[str]


@dataclass(frozen=True)
class CvProject:
    name: str
    source: str
    url: str
    bullets: list[str]
    technologies: list[str]


@dataclass(frozen=True)
class CvAnalysis:
    keywords: list[str]
    oversell_points: list[str]
    caution_rules: list[str]


@dataclass(frozen=True)
class TargetedCvData:
    identity: CvIdentity
    offer_info: CvOfferInfo
    proposed_title: str
    targeted_summary: str
    recruiter_summary: str
    skills: CvSkills
    experiences: list[CvExperience]
    projects: list[CvProject]
    education: list[str]
    analysis: CvAnalysis


def build_targeted_cv_data(offer: dict[str, Any], profile: CvProfile) -> TargetedCvData:
    match = match_offer_to_profile(offer, profile)
    profile_summary = _profile_summary(profile.raw)
    skills = CvSkills(
        confirmed=match.strong_present,
        complementary=match.medium_present,
        to_confirm=match.to_confirm_present,
    )

    return TargetedCvData(
        identity=_identity_info(profile.raw),
        offer_info=_offer_info(offer),
        proposed_title=_proposed_title(offer, skills),
        targeted_summary=_targeted_summary(profile_summary, skills),
        recruiter_summary=_recruiter_summary(profile_summary, skills),
        skills=skills,
        experiences=_experiences(profile.raw),
        projects=_projects(profile.raw),
        education=_education(profile.raw),
        analysis=CvAnalysis(
            keywords=match.offer_keywords_not_in_profile,
            oversell_points=[
                f"{skill}: à confirmer, ne pas présenter comme maîtrisé."
                for skill in match.to_confirm_present
            ],
            caution_rules=[
                "Ne jamais inventer une expérience.",
                "Ne jamais inventer une compétence.",
                "Ne pas présenter une compétence à confirmer comme maîtrisée.",
                "Utiliser uniquement les données du profil maître et de l'offre Excel.",
                "Ne pas scraper l'URL de l'offre pour cette V1.",
            ],
        ),
    )


def _identity_info(raw: dict[str, Any]) -> CvIdentity:
    identity = raw.get("identity")
    if not isinstance(identity, dict):
        identity = {}

    return CvIdentity(
        name=_clean_text(identity.get("name")),
        title=_clean_text(identity.get("title")),
        location=_clean_text(identity.get("location")),
        email=_clean_text(identity.get("email")),
        phone=_clean_text(identity.get("phone")),
    )


def _offer_info(offer: dict[str, Any]) -> CvOfferInfo:
    return CvOfferInfo(
        title=str(offer.get("titre") or "Titre cible a definir"),
        company=str(offer.get("entreprise") or "Entreprise non renseignee"),
        source=str(offer.get("source") or "Non renseignee"),
        location=str(offer.get("localisation") or "Non renseignee"),
        contract_type=str(offer.get("type_contrat") or "Non renseigne"),
        decision=str(offer.get("decision") or "Non renseignee"),
        score=str(offer.get("score_total") or "Non renseigne"),
        url=str(offer.get("url_offre") or "Non renseignee"),
    )


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


def _proposed_title(offer: dict[str, Any], skills: CvSkills) -> str:
    confirmed = " ".join(skills.confirmed + skills.complementary)
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


def _targeted_summary(profile_summary: str, skills: CvSkills) -> str:
    if not profile_summary:
        profile_summary = "Accroche à rédiger depuis le profil maître, sans ajouter d'expérience non documentée."

    confirmed = skills.confirmed + skills.complementary
    if confirmed:
        return f"{profile_summary} À orienter vers l'offre avec: {_inline_list(confirmed)}."
    return profile_summary


def _recruiter_summary(profile_summary: str, skills: CvSkills) -> str:
    if not profile_summary:
        return ""

    summary_skills = _summary_skills(skills.confirmed + skills.complementary)
    if not summary_skills:
        return profile_summary

    return (
        f"{profile_summary} J'accompagne des projets web avec une approche orientée utilisateur, "
        f"en mettant en avant {_natural_skill_list(summary_skills)}."
    )


def _experiences(raw: dict[str, Any]) -> list[CvExperience]:
    experiences = [_format_experience(experience) for experience in _as_list(raw.get("experiences"))]
    return [experience for experience in experiences if experience]


def _projects(raw: dict[str, Any]) -> list[CvProject]:
    projects: list[CvProject] = []

    for experience in _as_list(raw.get("experiences")):
        if isinstance(experience, dict):
            for project in _as_list(experience.get("projects") or experience.get("projets")):
                formatted = _format_project(project, source="Projet d'expérience")
                if formatted:
                    projects.append(formatted)

    for key in ["projets", "projects"]:
        for project in _as_list(raw.get(key)):
            formatted = _format_project(project, source="Projet")
            if formatted:
                projects.append(formatted)

    portfolio = raw.get("portfolio")
    if isinstance(portfolio, dict):
        for project in _as_list(portfolio.get("public_projects")):
            formatted = _format_project(project, source="Portfolio public")
            if formatted:
                projects.append(formatted)

    return projects


def _education(raw: dict[str, Any]) -> list[str]:
    lines = [_format_education(item) for item in _as_list(raw.get("education"))]
    return [line for line in lines if line]


def _format_experience(experience: Any) -> CvExperience | None:
    if isinstance(experience, str):
        return CvExperience(heading=experience, bullets=[])
    if not isinstance(experience, dict):
        return None

    title = experience.get("title") or experience.get("titre")
    company = experience.get("company") or experience.get("entreprise")
    period = experience.get("period") or experience.get("periode") or experience.get("dates")
    summary = experience.get("summary") or experience.get("description") or experience.get("resume")
    heading = _join_values([title, company], separator=" - ") or "Expérience"
    if period:
        heading = f"{heading} ({period})"

    bullets = _clean_lines([summary, *_as_list(experience.get("achievements"))])
    return CvExperience(heading=heading, bullets=bullets)


def _format_project(project: Any, *, source: str) -> CvProject | None:
    if isinstance(project, str):
        return CvProject(name=project, source=source, url="", bullets=[], technologies=[])
    if not isinstance(project, dict):
        return None

    name = project.get("name") or project.get("title") or project.get("titre") or project.get("nom") or "Projet"
    return CvProject(
        name=str(name).strip(),
        source=source,
        url=str(project.get("url") or "").strip(),
        bullets=_clean_lines([*_as_list(project.get("highlights")), *_as_list(project.get("bullets"))]),
        technologies=_clean_lines(_as_list(project.get("technologies"))),
    )


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


def _clean_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _clean_lines(values: list[Any]) -> list[str]:
    lines: list[str] = []
    for value in values:
        text = _join_values(value)
        if text:
            lines.append(text)
    return lines


def _inline_list(items: list[str]) -> str:
    return ", ".join(items) if items else "Aucune"


def _natural_skill_list(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} et {items[1]}"
    return f"{', '.join(items[:-1])} et {items[-1]}"


def _summary_skills(skills: list[str]) -> list[str]:
    high_priority = [skill for skill in skills if _summary_priority(skill) == 0]
    candidates = high_priority if high_priority else skills
    return candidates[:MAX_RECRUITER_SUMMARY_SKILLS]


def _summary_priority(skill: str) -> int:
    normalized = _normalize_for_choice(skill)
    if normalized in HIGH_PRIORITY_SUMMARY_SKILLS:
        return 0
    if normalized in LOW_PRIORITY_SUMMARY_SKILLS:
        return 2
    return 1


def _normalize_for_choice(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents).strip()
