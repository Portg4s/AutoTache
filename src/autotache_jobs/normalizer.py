"""Normalize simulated France Travail offers into the AutoTache format."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .filters import is_relevant_offer
from .parsers import extract_technologies, parse_salary, parse_teletravail


FRANCE_TRAVAIL_DETAIL_URL = "https://candidat.francetravail.fr/offres/recherche/detail/{offer_id}"


def normalize_france_travail_offer(
    raw_offer: dict,
    allow_stage: bool = False,
    allow_alternance: bool = False,
) -> dict[str, Any]:
    """Normalize one France Travail offer dictionary without performing any API call."""

    offer_id = _clean(raw_offer.get("id"))
    title = _clean(raw_offer.get("intitule"))
    description = _clean(raw_offer.get("description"))
    salary_label = _clean(_nested_get(raw_offer, "salaire", "libelle"))
    analysis_text = " ".join(
        value
        for value in (
            title,
            description,
            _competences_text(raw_offer),
        )
        if value
    )

    teletravail = parse_teletravail(f"{title} {description}")
    salary = parse_salary(salary_label or description)
    technologies = extract_technologies(analysis_text)

    normalized = {
        "id_offre": offer_id,
        "source": "France Travail",
        "titre": title,
        "description": description,
        "entreprise": _clean(_nested_get(raw_offer, "entreprise", "nom")) or "Non specifie",
        "localisation": _clean(_nested_get(raw_offer, "lieuTravail", "libelle")),
        "code_postal": _clean(_nested_get(raw_offer, "lieuTravail", "codePostal")),
        "type_contrat": _clean(raw_offer.get("typeContratLibelle") or raw_offer.get("typeContrat")),
        "experience": _clean(raw_offer.get("experienceLibelle")),
        "salaire_brut": salary_label,
        "salaire_min": salary["salaire_min"],
        "salaire_max": salary["salaire_max"],
        "salaire_moyen": salary["salaire_moyen"],
        "salaire_type": salary["salaire_type"],
        "teletravail_mention": teletravail["teletravail_mention"],
        "teletravail_jours": teletravail["teletravail_jours"],
        "technologies": technologies,
        "date_publication": _clean(raw_offer.get("dateCreation")),
        "date_actualisation": _clean(raw_offer.get("dateActualisation")),
        "url_offre": FRANCE_TRAVAIL_DETAIL_URL.format(offer_id=offer_id),
        "date_detection": datetime.now().isoformat(timespec="seconds"),
    }

    relevance = is_relevant_offer(
        normalized,
        allow_stage=allow_stage,
        allow_alternance=allow_alternance,
    )
    normalized.update(
        {
            "is_relevant": relevance["is_relevant"],
            "relevance_reason": relevance["reason"],
            "matched_keywords": relevance["matched_keywords"],
            "excluded_by": relevance["excluded_by"],
        }
    )

    return normalized


def _nested_get(data: dict, *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _competences_text(raw_offer: dict) -> str:
    competences = raw_offer.get("competences", [])
    if not isinstance(competences, list):
        return ""

    labels = []
    for competence in competences:
        if isinstance(competence, dict):
            label = _clean(competence.get("libelle"))
            if label:
                labels.append(label)

    return " ".join(labels)
