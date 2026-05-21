"""Match an Excel offer against the local master profile."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from autotache_jobs.cv.profile import CvProfile


OFFER_MATCH_FIELDS = ["titre", "description", "technologies", "score_reason", "type_contrat"]
STOP_WORDS = {
    "100",
    "avec",
    "candidat",
    "candidats",
    "cdi",
    "dans",
    "des",
    "dijon",
    "domaine",
    "entreprise",
    "france",
    "grace",
    "grâce",
    "localisation",
    "metier",
    "métier",
    "une",
    "pour",
    "les",
    "sur",
    "score",
    "technologies",
    "teletravail",
    "télétravail",
    "verifier",
    "vérifier",
    "vous",
    "nous",
    "notre",
    "votre",
    "poste",
    "offre",
    "profil",
    "contrat",
    "mission",
    "missions",
}


@dataclass(frozen=True)
class CvMatch:
    strong_present: list[str]
    medium_present: list[str]
    to_confirm_present: list[str]
    offer_keywords_not_in_profile: list[str]


def match_offer_to_profile(offer: dict[str, Any], profile: CvProfile) -> CvMatch:
    offer_text = _offer_text(offer)
    profile_skills = profile.strong_skills + profile.medium_skills + profile.to_confirm

    strong_present = _present_skills(profile.strong_skills, offer_text)
    medium_present = _present_skills(profile.medium_skills, offer_text)
    to_confirm_present = _present_skills(profile.to_confirm, offer_text)

    profile_text = " ".join(_normalize(skill) for skill in profile_skills)
    unknown_keywords = [
        keyword
        for keyword in _offer_keywords(offer)
        if _normalize(keyword) not in profile_text
        and _normalize(keyword) not in [_normalize(skill) for skill in profile_skills]
    ]

    return CvMatch(
        strong_present=strong_present,
        medium_present=medium_present,
        to_confirm_present=to_confirm_present,
        offer_keywords_not_in_profile=unknown_keywords,
    )


def _present_skills(skills: list[str], offer_text: str) -> list[str]:
    normalized_offer = _normalize(offer_text)
    return [skill for skill in skills if _normalize(skill) and _normalize(skill) in normalized_offer]


def _offer_text(offer: dict[str, Any]) -> str:
    return " ".join(str(offer.get(field) or "") for field in OFFER_MATCH_FIELDS)


def _offer_keywords(offer: dict[str, Any]) -> list[str]:
    values: list[str] = []
    technologies = offer.get("technologies")
    if technologies:
        values.extend(
            technology
            for technology in _split_technologies(str(technologies))
            if _is_useful_keyword(technology, offer)
        )

    text = _offer_text(offer)
    values.extend(
        token
        for token in re.findall(r"[A-Za-zÀ-ÿ0-9+#.-]{3,}", text)
        if _is_useful_keyword(token, offer)
    )
    return _dedupe(values)[:40]


def _split_technologies(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,;/|]", value) if part.strip()]


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    cleaned = re.sub(r"^[^\w+#]+|[^\w+#]+$", "", without_accents)
    return re.sub(r"\s+", " ", cleaned).strip()


def _is_useful_keyword(token: str, offer: dict[str, Any]) -> bool:
    normalized = _normalize(token)
    if normalized in STOP_WORDS:
        return False
    if normalized.isdigit():
        return False

    localisation = _normalize(str(offer.get("localisation") or ""))
    if normalized and normalized in localisation:
        return False

    return True


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = _normalize(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result
