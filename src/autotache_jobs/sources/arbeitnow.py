"""Arbeitnow offer source."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ..filters import is_relevant_offer
from ..parsers import extract_technologies, parse_salary, parse_teletravail
from ..scoring import score_offer
from .base import JobSource, SourceResult


DEFAULT_ARBEITNOW_ENDPOINT = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowSourceError(RuntimeError):
    """Raised when Arbeitnow returns an invalid or failed response."""


class ArbeitnowSource(JobSource):
    """Collect and normalize offers from Arbeitnow."""

    name = "Arbeitnow"

    def __init__(
        self,
        endpoint_url: str = DEFAULT_ARBEITNOW_ENDPOINT,
        max_pages: int = 1,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.max_pages = max(max_pages, 1)
        self.timeout = timeout
        self._http_client = http_client or httpx.Client(timeout=timeout)

    def collect(self) -> SourceResult:
        raw_offers = self.collect_raw_offers()
        return SourceResult(
            source_name=self.name,
            raw_offers=raw_offers,
            normalized_offers=[normalize_arbeitnow_offer(raw_offer) for raw_offer in raw_offers],
        )

    def collect_raw_offers(self) -> list[dict]:
        """Collect raw Arbeitnow offers from one or more paginated API pages."""

        offers: list[dict] = []
        next_url: str | None = self.endpoint_url

        for _ in range(self.max_pages):
            if not next_url:
                break

            response = self._http_client.get(next_url)
            _raise_for_status(response)
            payload = _json(response)
            page_offers = payload.get("data", [])
            if isinstance(page_offers, list):
                offers.extend(offer for offer in page_offers if isinstance(offer, dict))

            next_url = _next_page_url(payload)

        return offers


def normalize_arbeitnow_offer(raw_offer: dict) -> dict[str, Any]:
    """Normalize one Arbeitnow offer dictionary into the AutoTache common format."""

    title = _clean(raw_offer.get("title"))
    description = _clean(raw_offer.get("description"))
    tags_text = _values_text(raw_offer.get("tags"))
    job_types_text = _values_text(raw_offer.get("job_types"))
    salary_text = _clean(raw_offer.get("salary")) or description
    location = _clean(raw_offer.get("location"))
    analysis_text = " ".join(value for value in (title, description, tags_text, job_types_text) if value)

    teletravail = parse_teletravail(_remote_text(raw_offer, title, description))
    salary = parse_salary(salary_text)
    technologies = extract_technologies(analysis_text)

    normalized = {
        "id_offre": _offer_id(raw_offer),
        "source": "Arbeitnow",
        "titre": title,
        "description": description,
        "entreprise": _clean(raw_offer.get("company_name")) or "Non specifie",
        "localisation": location,
        "code_postal": "",
        "type_contrat": job_types_text,
        "experience": "",
        "salaire_brut": _clean(raw_offer.get("salary")),
        "salaire_min": salary["salaire_min"],
        "salaire_max": salary["salaire_max"],
        "salaire_moyen": salary["salaire_moyen"],
        "salaire_type": salary["salaire_type"],
        "teletravail_mention": teletravail["teletravail_mention"],
        "teletravail_jours": teletravail["teletravail_jours"],
        "technologies": technologies,
        "date_publication": _clean(raw_offer.get("created_at")),
        "date_actualisation": _clean(raw_offer.get("updated_at")),
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
    raise ArbeitnowSourceError(f"Erreur HTTP {response.status_code} pendant collecte Arbeitnow: {message or 'aucun detail'}")


def _json(response: httpx.Response) -> dict[str, Any]:
    if response.status_code == 204 or not response.text.strip():
        return {}

    try:
        data = response.json()
    except ValueError as exc:
        raise ArbeitnowSourceError("Reponse JSON invalide pendant collecte Arbeitnow.") from exc

    if not isinstance(data, dict):
        raise ArbeitnowSourceError("Reponse inattendue pendant collecte Arbeitnow: objet JSON attendu.")
    return data


def _next_page_url(payload: dict[str, Any]) -> str | None:
    links = payload.get("links", {})
    if not isinstance(links, dict):
        return None
    next_url = links.get("next")
    return next_url if isinstance(next_url, str) and next_url.strip() else None


def _offer_id(raw_offer: dict) -> str:
    for key in ("id", "slug", "url"):
        value = _clean(raw_offer.get(key))
        if value:
            return value
    return ""


def _remote_text(raw_offer: dict, title: str, description: str) -> str:
    remote_value = raw_offer.get("remote")
    remote_label = "remote" if remote_value is True else ""
    return " ".join(value for value in (title, description, remote_label) if value)


def _values_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(_clean(item) for item in value if _clean(item))
    return _clean(value)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
