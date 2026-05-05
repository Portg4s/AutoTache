"""Remotive offer source."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ..filters import is_relevant_offer
from ..parsers import extract_technologies, parse_salary, parse_teletravail
from ..scoring import score_offer
from .base import JobSource, SourceResult, SourceStats


DEFAULT_REMOTIVE_ENDPOINT = "https://remotive.com/api/remote-jobs"


class RemotiveSourceError(RuntimeError):
    """Raised when Remotive returns an invalid or failed response."""


class RemotiveSource(JobSource):
    """Collect and normalize offers from Remotive."""

    name = "Remotive"

    def __init__(
        self,
        endpoint_url: str = DEFAULT_REMOTIVE_ENDPOINT,
        keywords: list[str] | None = None,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.keywords = _clean_terms(keywords or [])
        self.timeout = timeout
        self._http_client = http_client or httpx.Client(timeout=timeout)

    def collect(self) -> SourceResult:
        fetched_offers = self.collect_fetched_offers()
        raw_offers = filter_raw_offers(fetched_offers, keywords=self.keywords)
        return SourceResult(
            source_name=self.name,
            raw_offers=raw_offers,
            normalized_offers=[normalize_remotive_offer(raw_offer) for raw_offer in raw_offers],
            stats=SourceStats(
                enabled=True,
                fetched=len(fetched_offers),
                kept=len(raw_offers),
                filtered=len(fetched_offers) - len(raw_offers),
            ),
        )

    def collect_raw_offers(self) -> list[dict]:
        """Collect raw Remotive offers after applying local source filters."""

        return filter_raw_offers(self.collect_fetched_offers(), keywords=self.keywords)

    def collect_fetched_offers(self) -> list[dict]:
        """Collect raw Remotive offers before local filters."""

        response = self._http_client.get(self.endpoint_url)
        _raise_for_status(response)
        payload = _json(response)
        jobs = payload.get("jobs", [])
        if not isinstance(jobs, list):
            return []
        return [job for job in jobs if isinstance(job, dict)]


def filter_raw_offers(raw_offers: list[dict], keywords: list[str] | None = None) -> list[dict]:
    """Return Remotive offers matching optional local keyword filters."""

    keyword_terms = _clean_terms(keywords or [])
    return [offer for offer in raw_offers if matches_keywords(offer, keyword_terms)]


def matches_keywords(raw_offer: dict, keywords: list[str] | None = None) -> bool:
    """Return true when a Remotive offer matches at least one configured keyword."""

    terms = _clean_terms(keywords or [])
    if not terms:
        return True

    text = _normalize_filter_text(_offer_search_text(raw_offer))
    return any(_normalize_filter_text(term) in text for term in terms)


def normalize_remotive_offer(raw_offer: dict) -> dict[str, Any]:
    """Normalize one Remotive offer dictionary into the AutoTache common format."""

    title = _clean(raw_offer.get("title"))
    description = _clean(raw_offer.get("description"))
    tags_text = _values_text(raw_offer.get("tags") or raw_offer.get("job_tags"))
    category = _clean(raw_offer.get("category"))
    job_type = _clean(raw_offer.get("job_type"))
    salary_text = _clean(raw_offer.get("salary")) or description
    location = _clean(raw_offer.get("candidate_required_location"))
    analysis_text = " ".join(value for value in (title, description, tags_text, category, job_type) if value)

    teletravail = parse_teletravail(_remote_text(raw_offer, title, description, location))
    salary = parse_salary(salary_text)
    technologies = extract_technologies(analysis_text)

    normalized = {
        "id_offre": _offer_id(raw_offer),
        "source": "Remotive",
        "titre": title,
        "description": description,
        "entreprise": _clean(raw_offer.get("company_name")) or "Non specifie",
        "localisation": location,
        "code_postal": "",
        "type_contrat": job_type or category,
        "experience": "",
        "salaire_brut": _clean(raw_offer.get("salary")),
        "salaire_min": salary["salaire_min"],
        "salaire_max": salary["salaire_max"],
        "salaire_moyen": salary["salaire_moyen"],
        "salaire_type": salary["salaire_type"],
        "teletravail_mention": teletravail["teletravail_mention"],
        "teletravail_jours": teletravail["teletravail_jours"],
        "technologies": technologies,
        "date_publication": _clean(raw_offer.get("publication_date")),
        "date_actualisation": "",
        "url_offre": _clean(raw_offer.get("url")),
        "date_detection": datetime.now().isoformat(timespec="seconds"),
    }

    relevance = is_relevant_offer(normalized)
    normalized.update(
        {
            "is_relevant": relevance["is_relevant"],
            "relevance_reason": relevance["reason"],
            "matched_keywords": relevance["matched_keywords"],
            "excluded_by": relevance["excluded_by"],
        }
    )
    normalized.update(score_offer(normalized))

    return normalized


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code < 400:
        return

    message = response.text.strip().replace("\n", " ")[:300]
    raise RemotiveSourceError(f"Erreur HTTP {response.status_code} pendant collecte Remotive: {message or 'aucun detail'}")


def _json(response: httpx.Response) -> dict[str, Any]:
    if response.status_code == 204 or not response.text.strip():
        return {}

    try:
        data = response.json()
    except ValueError as exc:
        raise RemotiveSourceError("Reponse JSON invalide pendant collecte Remotive.") from exc

    if not isinstance(data, dict):
        raise RemotiveSourceError("Reponse inattendue pendant collecte Remotive: objet JSON attendu.")
    return data


def _offer_id(raw_offer: dict) -> str:
    for key in ("id", "slug", "url"):
        value = _clean(raw_offer.get(key))
        if value:
            return value
    return ""


def _remote_text(raw_offer: dict, title: str, description: str, location: str) -> str:
    remote_value = raw_offer.get("remote")
    remote_label = "remote" if remote_value is True else ""
    return " ".join(value for value in (title, description, location, remote_label) if value)


def _values_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(_clean(item) for item in value if _clean(item))
    return _clean(value)


def _offer_search_text(raw_offer: dict) -> str:
    return " ".join(
        value
        for value in (
            _clean(raw_offer.get("title")),
            _clean(raw_offer.get("description")),
            _values_text(raw_offer.get("tags") or raw_offer.get("job_tags")),
            _clean(raw_offer.get("category")),
            _clean(raw_offer.get("company_name")),
        )
        if value
    )


def _clean_terms(values: list[str]) -> list[str]:
    return [value.strip() for value in values if value and value.strip()]


def _normalize_filter_text(value: Any) -> str:
    return _clean(value).casefold()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
