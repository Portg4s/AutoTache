"""Local parsers for offer descriptions."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable


TECHNOLOGY_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("WordPress", (r"\bwordpress\b",)),
    ("WooCommerce", (r"\bwoocommerce\b",)),
    ("Elementor", (r"\belementor\b",)),
    ("HTML", (r"\bhtml5?\b",)),
    ("CSS", (r"\bcss3?\b",)),
    ("JavaScript", (r"\bjavascript\b", r"\bjs\b")),
    ("TypeScript", (r"\btypescript\b", r"\bts\b")),
    ("React", (r"\breact(?:\.js|js)?\b",)),
    ("Vue.js", (r"\bvue(?:\.js|js)?\b",)),
    ("Tailwind", (r"\btailwind(?:\s*css)?\b",)),
    ("Bootstrap", (r"\bbootstrap\b",)),
    ("Figma", (r"\bfigma\b",)),
    ("Photoshop", (r"\bphotoshop\b",)),
    ("Illustrator", (r"\billustrator\b",)),
    ("UI", (r"\bui\b", r"\binterface utilisateur\b")),
    ("UX", (r"\bux\b", r"\bexperience utilisateur\b")),
)


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return without_accents.lower().replace("’", "'")


def _parse_number(raw_value: str) -> float:
    digits = re.sub(r"[^\d,.kK]", "", raw_value).replace(",", ".")
    if "k" in digits.lower():
        return float(digits.lower().replace("k", "")) * 1000
    return float(digits)


def _salary_dict(
    salaire_min: float | None = None,
    salaire_max: float | None = None,
    salaire_type: str | None = None,
    salaire_brut: bool = False,
) -> dict[str, float | str | bool | None]:
    salaire_moyen = None
    if salaire_min is not None and salaire_max is not None:
        salaire_moyen = round((salaire_min + salaire_max) / 2, 2)
    elif salaire_min is not None:
        salaire_moyen = salaire_min

    return {
        "salaire_min": salaire_min,
        "salaire_max": salaire_max,
        "salaire_moyen": salaire_moyen,
        "salaire_type": salaire_type,
        "salaire_brut": salaire_brut,
    }


def parse_teletravail(text: str) -> dict[str, int | str | None]:
    """Detect remote-work mentions in an offer text."""

    normalized = _normalize_text(text)

    if not normalized.strip():
        return {"teletravail_mention": None, "teletravail_jours": None}

    if re.search(r"\b(presentiel uniquement|100\s*%\s*presentiel|pas de teletravail)\b", normalized):
        return {"teletravail_mention": "presentiel uniquement", "teletravail_jours": 0}

    if re.search(r"\b(100\s*%\s*teletravail|full remote|remote full|teletravail complet)\b", normalized):
        return {"teletravail_mention": "100% teletravail", "teletravail_jours": 5}

    days_patterns = (
        r"teletravail\s+(?:jusqu'a\s+)?(\d+)\s+jours?",
        r"jusqu'a\s+(\d+)\s+jours?\s+de\s+teletravail",
        r"(\d+)\s+jours?\s+(?:par\s+semaine\s+)?(?:de\s+)?teletravail",
    )
    for pattern in days_patterns:
        match = re.search(pattern, normalized)
        if match:
            return {
                "teletravail_mention": "teletravail partiel",
                "teletravail_jours": int(match.group(1)),
            }

    if re.search(r"\b(hybride|teletravail|remote)\b", normalized):
        return {"teletravail_mention": "hybride", "teletravail_jours": None}

    return {"teletravail_mention": None, "teletravail_jours": None}


def parse_salary(text: str) -> dict[str, float | str | bool | None]:
    """Parse common French salary mentions from free text."""

    normalized = _normalize_text(text)
    if not normalized.strip():
        return _salary_dict()

    salaire_brut = "brut" in normalized
    salaire_type = None
    if re.search(r"\b(annuel|an|annee|k)\b", normalized):
        salaire_type = "annuel"
    elif re.search(r"\b(mensuel|mois)\b", normalized):
        salaire_type = "mensuel"

    range_patterns = (
        r"(?:annuel\s+)?de\s+([\d\s,.]+k?)\s*(?:euros?|eur|€)?\s+(?:a|-)\s+([\d\s,.]+k?)\s*(?:euros?|eur|€)?",
        r"([\d\s,.]+k)\s*(?:a|-)\s*([\d\s,.]+k)",
        r"([\d\s,.]+)\s*(?:€|euros?|eur)\s*(?:-|a)\s*([\d\s,.]+)\s*(?:€|euros?|eur)",
    )

    for pattern in range_patterns:
        match = re.search(pattern, normalized)
        if match:
            salaire_min = _parse_number(match.group(1))
            salaire_max = _parse_number(match.group(2))
            if salaire_type is None and max(salaire_min, salaire_max) >= 10000:
                salaire_type = "annuel"
            return _salary_dict(salaire_min, salaire_max, salaire_type, salaire_brut)

    single_patterns = (
        r"([\d\s,.]+k)\s*(?:€|euros?|eur)?",
        r"([\d\s,.]+)\s*(?:€|euros?|eur)",
    )
    for pattern in single_patterns:
        match = re.search(pattern, normalized)
        if match:
            salaire_min = _parse_number(match.group(1))
            return _salary_dict(salaire_min, None, salaire_type, salaire_brut)

    return _salary_dict()


def extract_technologies(text: str) -> list[str]:
    """Extract known web/design technologies from a text."""

    normalized = _normalize_text(text)
    found: list[str] = []

    for label, patterns in TECHNOLOGY_PATTERNS:
        if _matches_any(normalized, patterns):
            found.append(label)

    return found


def _matches_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)
