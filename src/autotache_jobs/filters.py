"""Local business filtering for job offers."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .parsers import _normalize_text, extract_technologies


INCLUSION_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("WordPress", (r"\bwordpress\b",)),
    ("WooCommerce", (r"\bwoocommerce\b",)),
    ("Elementor", (r"\belementor\b",)),
    ("integrateur web", (r"\bintegrateur web\b",)),
    ("integrateur front-end", (r"\bintegrateur front(?:-| )?end\b",)),
    ("developpeur front-end", (r"\bdeveloppeur front(?:-| )?end\b",)),
    ("frontend developer", (r"\bfrontend developer\b", r"\bfront(?:-| )?end developer\b")),
    ("webdesigner", (r"\bwebdesigner\b",)),
    ("designer web", (r"\bdesigner web\b", r"\bweb designer\b")),
    ("UI designer", (r"\bui designer\b",)),
    ("UX designer", (r"\bux designer\b",)),
    ("UI/UX designer", (r"\bui\s*/\s*ux designer\b", r"\bui ux designer\b")),
    ("graphiste web", (r"\bgraphiste web\b",)),
    ("graphiste digital", (r"\bgraphiste\b.*\b(web|ui|ux|digital|numerique)\b",)),
    ("HTML", (r"\bhtml5?\b",)),
    ("CSS", (r"\bcss3?\b",)),
    ("JavaScript", (r"\bjavascript\b", r"\bjs\b")),
    ("React", (r"\breact(?:\.js|js)?\b",)),
    ("Vue.js", (r"\bvue(?:\.js|js)?\b",)),
    ("Tailwind", (r"\btailwind(?:\s*css)?\b",)),
    ("Bootstrap", (r"\bbootstrap\b",)),
    ("Figma", (r"\bfigma\b",)),
    ("Photoshop", (r"\bphotoshop\b",)),
    ("Illustrator", (r"\billustrator\b",)),
)

EXCLUSION_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("data scientist", (r"\bdata scientist\b",)),
    ("data engineer", (r"\bdata engineer\b",)),
    ("data analyst", (r"\bdata analyst\b",)),
    ("machine learning", (r"\bmachine learning\b",)),
    ("AI engineer", (r"\b(ai|ia) engineer\b", r"\bingenieur (ia|ai)\b")),
    ("devops pur", (r"\bdevops\b", r"\bsre\b")),
    ("administrateur systeme", (r"\badministrateur systeme\b", r"\badmin systeme\b")),
    ("support informatique", (r"\bsupport informatique\b",)),
    ("technicien informatique", (r"\btechnicien informatique\b",)),
    ("commercial", (r"\bcommercial\b",)),
    ("business developer", (r"\bbusiness developer\b", r"\bbizdev\b")),
    ("product owner", (r"\bproduct owner\b",)),
    ("scrum master", (r"\bscrum master\b",)),
    ("chef de projet hors web/design", (r"\bchef de projet\b",)),
    ("ingenieur mecanique", (r"\bingenieur mecanique\b",)),
    ("ingenieur btp", (r"\bingenieur btp\b", r"\bbtp\b")),
    ("ingenieur qualite", (r"\bingenieur qualite\b",)),
    ("ingenieur methodes", (r"\bingenieur methodes\b",)),
    ("ingenieur maintenance", (r"\bingenieur maintenance\b",)),
    ("calcul scientifique", (r"\bcalcul scientifique\b",)),
)

BACKEND_PATTERNS: tuple[str, ...] = (
    r"\bbackend\b",
    r"\bback(?:-| )?end\b",
    r"\bjava\b",
    r"\bphp symfony\b",
    r"\bsymfony\b",
    r"\blaravel\b",
    r"\bnode(?:\.js|js)?\b",
    r"\bapi rest\b",
)

PRINT_ONLY_PATTERNS: tuple[str, ...] = (
    r"\bprint\b",
    r"\bimprime\b",
    r"\bimprimerie\b",
    r"\bpre(?:-| )?presse\b",
    r"\bpackaging\b",
)


def is_relevant_offer(
    offer: dict,
    allow_stage: bool = False,
    allow_alternance: bool = False,
) -> dict[str, bool | str | list[str]]:
    """Decide whether a local offer dictionary matches the V1 target."""

    text = _offer_text(offer)
    normalized = _normalize_text(text)
    matched_keywords = _match_patterns(normalized, INCLUSION_PATTERNS)
    excluded_by = _match_patterns(normalized, EXCLUSION_PATTERNS)

    if _is_stage(normalized) and not allow_stage:
        excluded_by.append("stage")

    if _is_alternance(normalized) and not allow_alternance:
        excluded_by.append("alternance")

    if _is_backend_only(normalized, matched_keywords):
        excluded_by.append("backend pur")

    if _is_print_only_graphiste(normalized, matched_keywords):
        excluded_by.append("graphiste print uniquement")

    blocking_exclusions = _blocking_exclusions(excluded_by, matched_keywords, normalized)
    if blocking_exclusions:
        return {
            "is_relevant": False,
            "reason": f"Offre rejetee: {', '.join(blocking_exclusions)}.",
            "matched_keywords": matched_keywords,
            "excluded_by": blocking_exclusions,
        }

    if matched_keywords:
        return {
            "is_relevant": True,
            "reason": "Offre conservee: cible front-end, WordPress, webdesign, UI/UX ou graphisme web.",
            "matched_keywords": matched_keywords,
            "excluded_by": [],
        }

    return {
        "is_relevant": False,
        "reason": "Offre rejetee: aucun signal cible detecte.",
        "matched_keywords": [],
        "excluded_by": [],
    }


def _offer_text(offer: dict) -> str:
    technologies = offer.get("technologies", [])
    if isinstance(technologies, str):
        technologies_text = technologies
    elif isinstance(technologies, Iterable):
        technologies_text = " ".join(str(value) for value in technologies)
    else:
        technologies_text = ""

    raw_text = " ".join(
        str(offer.get(field, ""))
        for field in ("titre", "description", "type_contrat", "entreprise", "localisation")
    )
    extracted = " ".join(extract_technologies(raw_text))
    return f"{raw_text} {technologies_text} {extracted}"


def _match_patterns(text: str, patterns: tuple[tuple[str, tuple[str, ...]], ...]) -> list[str]:
    matches: list[str] = []
    for label, label_patterns in patterns:
        if any(re.search(pattern, text) for pattern in label_patterns):
            matches.append(label)
    return matches


def _has_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _is_stage(text: str) -> bool:
    return bool(re.search(r"\b(stage|stagiaire|internship)\b", text))


def _is_alternance(text: str) -> bool:
    return bool(re.search(r"\b(alternance|alternant|apprentissage|contrat pro)\b", text))


def _is_backend_only(text: str, matched_keywords: list[str]) -> bool:
    if not _has_any(text, BACKEND_PATTERNS):
        return False

    front_signals = {
        "WordPress",
        "WooCommerce",
        "Elementor",
        "integrateur web",
        "integrateur front-end",
        "developpeur front-end",
        "frontend developer",
        "HTML",
        "CSS",
        "JavaScript",
        "React",
        "Vue.js",
        "Tailwind",
        "Bootstrap",
    }
    return not any(keyword in front_signals for keyword in matched_keywords)


def _is_print_only_graphiste(text: str, matched_keywords: list[str]) -> bool:
    if "graphiste digital" in matched_keywords or "graphiste web" in matched_keywords:
        return False

    is_graphiste = bool(re.search(r"\bgraphiste\b", text))
    has_print_signal = _has_any(text, PRINT_ONLY_PATTERNS)
    has_web_design_signal = any(
        keyword in matched_keywords
        for keyword in ("Figma", "UI designer", "UX designer", "UI/UX designer", "designer web", "webdesigner")
    )
    return is_graphiste and has_print_signal and not has_web_design_signal


def _blocking_exclusions(excluded_by: list[str], matched_keywords: list[str], text: str) -> list[str]:
    if not excluded_by:
        return []

    tolerated_with_front = {"devops pur"}
    if _mentions_fullstack_with_front(text, matched_keywords):
        return [reason for reason in excluded_by if reason not in tolerated_with_front]

    return excluded_by


def _mentions_fullstack_with_front(text: str, matched_keywords: list[str]) -> bool:
    if not re.search(r"\bfullstack\b|\bfull stack\b", text):
        return False
    front_keywords = {"React", "Vue.js", "developpeur front-end", "frontend developer", "WordPress"}
    return any(keyword in front_keywords for keyword in matched_keywords)
