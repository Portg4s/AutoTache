"""Local rule-based scoring for normalized job offers."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


DECISION_RELEVANT = "Pertinent"
DECISION_REVIEW = "À vérifier"
DECISION_REJECTED = "Rejeté"

MAX_SCORE = 100

STRONG_SIGNALS = [
    "wordpress",
    "woocommerce",
    "elementor",
    "integrateur web",
    "integrateur front-end",
    "integrateur front end",
    "developpeur front-end",
    "developpeur front end",
    "front-end",
    "front end",
    "frontend",
    "ui designer",
    "ux designer",
    "ui/ux",
    "webdesigner",
    "designer web",
    "graphiste web",
    "figma",
    "html",
    "css",
    "javascript",
    "react",
    "vue.js",
    "vuejs",
    "tailwind",
    "bootstrap",
]

MEDIUM_SIGNALS = [
    "photoshop",
    "illustrator",
    "digital",
    "design",
    "design system",
    "web",
    "interface",
    "maquette",
    "responsive",
    "accessibilite",
    "seo",
]

TITLE_SIGNALS = [
    "developpeur wordpress",
    "wordpress",
    "integrateur web",
    "integrateur front-end",
    "integrateur front end",
    "developpeur front-end",
    "developpeur front end",
    "front-end",
    "front end",
    "frontend",
    "ui designer",
    "ux designer",
    "ui/ux",
    "webdesigner",
    "designer web",
    "graphiste web",
    "designer",
]

BUSINESS_DOMAIN_SIGNALS = [
    "wordpress",
    "woocommerce",
    "elementor",
    "frontend",
    "front-end",
    "front end",
    "ui",
    "ux",
    "design",
    "webdesign",
    "graphisme",
    "maquette",
    "interface",
]

FRONTEND_OR_DESIGN_SIGNALS = [
    "wordpress",
    "woocommerce",
    "elementor",
    "front-end",
    "front end",
    "frontend",
    "html",
    "css",
    "javascript",
    "react",
    "vue",
    "ui",
    "ux",
    "figma",
    "design",
    "webdesigner",
    "graphiste",
]

STRICT_ELIMINATORY_PATTERNS = {
    "stage": ["stage", "stagiaire"],
    "alternance": ["alternance", "alternant", "apprentissage"],
    "commercial pur": ["commercial", "business developer", "charge d'affaires"],
    "data pur": ["data analyst", "data engineer", "data scientist", "machine learning", "bi "],
}

BACKEND_PATTERNS = ["backend", "back-end", "back end", "node", "python", "django", "java", "php", "api"]
SOFT_PENALTY_TERMS = [
    "chef de projet",
    "scrum master",
    "product owner",
    "devops",
    "sre",
    "cloud engineer",
    "administrateur systeme",
    "backend",
    "back-end",
    "back end",
    "support informatique",
    "technicien informatique",
    "helpdesk",
    "hotline",
    "ingenieur mecanique",
    "ingenieur btp",
    "ingenieur qualite",
    "ingenieur methodes",
    "maintenance",
    "qualite",
    "methode",
    "methodes",
    "calcul scientifique",
]


def score_offer(offer: dict) -> dict:
    """Score an offer with local rules only."""

    safe_offer = offer if isinstance(offer, dict) else {}
    title = _normalize_text(safe_offer.get("titre"))
    description = _normalize_text(safe_offer.get("description"))
    technologies = _normalize_text(safe_offer.get("technologies"))
    location = _normalize_text(safe_offer.get("localisation"))
    contract = _normalize_text(safe_offer.get("type_contrat"))
    remote_text = _normalize_text(
        " ".join(
            [
                str(safe_offer.get("teletravail_mention") or ""),
                str(safe_offer.get("teletravail_jours") or ""),
            ]
        )
    )
    matched_keywords = _normalize_text(safe_offer.get("matched_keywords"))
    excluded_by = _normalize_text(safe_offer.get("excluded_by"))
    relevance_reason = _normalize_text(safe_offer.get("relevance_reason"))

    full_text = " ".join(
        [
            title,
            description,
            technologies,
            location,
            contract,
            remote_text,
            matched_keywords,
            excluded_by,
            relevance_reason,
        ]
    )

    details = {
        "technologies": _score_technology_signals(technologies + " " + description + " " + matched_keywords),
        "titre": _score_terms(title, TITLE_SIGNALS, 15, 25),
        "domaine_metier": _score_terms(full_text, BUSINESS_DOMAIN_SIGNALS, 6, 15),
        "localisation": _score_location(location),
        "teletravail": _score_remote(remote_text),
        "contrat": _score_contract(contract),
        "penalties": _score_penalties(full_text, is_backend_only=_is_backend_only(full_text)),
        "eliminatory_reason": _find_strict_eliminatory_reason(full_text),
    }

    positive_total = (
        details["technologies"]["score"]
        + details["titre"]["score"]
        + details["domaine_metier"]["score"]
        + details["localisation"]["score"]
        + details["teletravail"]["score"]
        + details["contrat"]["score"]
    )
    score_total = max(0, min(MAX_SCORE, positive_total - details["penalties"]["score"]))

    if details["eliminatory_reason"]:
        decision = DECISION_REJECTED
    elif score_total >= 80:
        decision = DECISION_RELEVANT
    elif score_total >= 45:
        decision = DECISION_REVIEW
    else:
        decision = DECISION_REJECTED

    return {
        "score_total": int(score_total),
        "decision": decision,
        "score_reason": _build_reason(decision, score_total, details),
        "score_details": details,
    }


def _score_terms(text: str, terms: list[str], points_per_match: int, cap: int) -> dict[str, Any]:
    matches = _matched_terms(text, terms)
    return {"score": min(len(matches) * points_per_match, cap), "matches": matches}


def _score_technology_signals(text: str) -> dict[str, Any]:
    strong_matches = _matched_terms(text, STRONG_SIGNALS)
    medium_matches = _matched_terms(text, MEDIUM_SIGNALS)
    score = min((len(strong_matches) * 15) + (len(medium_matches) * 8), 35)
    return {
        "score": score,
        "matches": strong_matches + medium_matches,
        "strong_matches": strong_matches,
        "medium_matches": medium_matches,
    }


def _score_location(location: str) -> dict[str, Any]:
    local_patterns = ["dijon", "cote d or", "cote-d-or", "bourgogne", "21000", "21"]
    matches = _matched_terms(location, local_patterns)
    return {"score": 10 if matches else 0, "matches": matches}


def _score_remote(remote_text: str) -> dict[str, Any]:
    if not remote_text:
        return {"score": 0, "matches": []}
    positive_patterns = ["teletravail", "remote", "hybride", "distance"]
    matches = _matched_terms(remote_text, positive_patterns)
    has_days = bool(re.search(r"\b[1-5]\b", remote_text))
    score = 10 if matches or has_days else 0
    return {"score": score, "matches": matches + (["jours_teletravail"] if has_days else [])}


def _score_contract(contract: str) -> dict[str, Any]:
    matches = _matched_terms(contract, ["cdi", "cdd"])
    return {"score": 5 if matches else 0, "matches": matches}


def _score_penalties(text: str, is_backend_only: bool = False) -> dict[str, Any]:
    matches = _matched_terms(text, SOFT_PENALTY_TERMS)
    if is_backend_only and "backend pur" not in matches:
        matches.append("backend pur")
    return {"score": min(len(matches) * 12, 35), "matches": matches}


def _find_strict_eliminatory_reason(text: str) -> str | None:
    for reason, patterns in STRICT_ELIMINATORY_PATTERNS.items():
        if _matched_terms(text, patterns):
            return reason
    return None


def _is_backend_only(text: str) -> bool:
    has_backend = bool(_matched_terms(text, BACKEND_PATTERNS))
    has_frontend_or_design = bool(_matched_terms(text, FRONTEND_OR_DESIGN_SIGNALS))
    return has_backend and not has_frontend_or_design


def _build_reason(decision: str, score_total: int, details: dict[str, Any]) -> str:
    eliminatory_reason = details.get("eliminatory_reason")
    if eliminatory_reason:
        return f"{decision}: règle éliminatoire ({eliminatory_reason}), score calculé {score_total}/100."

    positive_parts = []
    for key in ["technologies", "titre", "domaine_metier", "localisation", "teletravail", "contrat"]:
        matches = details[key]["matches"]
        if matches:
            positive_parts.append(f"{key}: {', '.join(matches)}")

    if not positive_parts:
        return f"{decision}: signaux insuffisants, score {score_total}/100."

    return f"{decision}: score {score_total}/100 grâce à " + "; ".join(positive_parts) + "."


def _matched_terms(text: str, terms: list[str]) -> list[str]:
    matches: list[str] = []
    for term in terms:
        normalized_term = _normalize_text(term)
        if normalized_term and _contains_term(text, normalized_term):
            matches.append(term)
    return matches


def _contains_term(text: str, term: str) -> bool:
    if not term:
        return False
    if len(term) <= 3 and term.isalnum():
        return bool(re.search(rf"\b{re.escape(term)}\b", text))
    return term in text


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    normalized = unicodedata.normalize("NFKD", str(value))
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return normalized.lower()
