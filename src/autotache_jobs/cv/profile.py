"""Profile loading helpers for targeted CV drafts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ProfileError(ValueError):
    """Raised when a CV profile cannot be loaded."""


@dataclass(frozen=True)
class CvProfile:
    path: Path
    raw: dict[str, Any]
    strong_skills: list[str]
    medium_skills: list[str]
    to_confirm: list[str]


def load_profile(path: str | Path) -> CvProfile:
    profile_path = Path(path)
    if not profile_path.exists():
        raise ProfileError(f"Profil introuvable: {profile_path}")

    with profile_path.open("r", encoding="utf-8") as profile_file:
        data = yaml.safe_load(profile_file) or {}

    if not isinstance(data, dict):
        raise ProfileError(f"Profil invalide: {profile_path} doit contenir un objet YAML.")

    return CvProfile(
        path=profile_path,
        raw=data,
        strong_skills=_extract_skills(
            data,
            [
                ("competences_fortes",),
                ("strong_skills",),
                ("skills", "strong"),
                ("skills", "fortes"),
                ("competences", "fortes"),
                ("competences", "fort"),
            ],
        ),
        medium_skills=_extract_skills(
            data,
            [
                ("competences_moyennes",),
                ("medium_skills",),
                ("skills", "medium"),
                ("skills", "moyennes"),
                ("competences", "moyennes"),
                ("competences", "intermediaires"),
            ],
        ),
        to_confirm=_extract_skills(
            data,
            [
                ("to_confirm",),
                ("a_confirmer",),
                ("competences_a_confirmer",),
                ("skills", "to_confirm"),
                ("skills", "a_confirmer"),
                ("competences", "a_confirmer"),
            ],
        ),
    )


def _extract_skills(data: dict[str, Any], paths: list[tuple[str, ...]]) -> list[str]:
    values: list[str] = []
    for path in paths:
        current: Any = data
        for part in path:
            if not isinstance(current, dict) or part not in current:
                current = None
                break
            current = current[part]
        values.extend(_flatten_skill_values(current))
    return _dedupe(values)


def _flatten_skill_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            items.extend(_flatten_skill_values(item))
        return items
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if isinstance(item, bool):
                if item:
                    items.append(str(key))
            elif isinstance(item, (list, tuple, dict)):
                items.extend(_flatten_skill_values(item))
            elif item:
                items.append(str(item))
        return items
    return [str(value)]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = " ".join(str(value).strip().split())
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result

