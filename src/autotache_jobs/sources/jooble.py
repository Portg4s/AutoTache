"""Jooble offer source."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ..filters import is_relevant_offer
from ..parsers import extract_technologies, parse_salary, parse_teletravail
from ..scoring import score_offer
from .base import JobSource, SourceResult, SourceStats


DEFAULT_JOOBLE_BASE_URL = "https://fr.jooble.org/api"


class JoobleSourceError(RuntimeError):
    """Raised when Jooble returns an invalid or failed response."""


class JoobleSource(JobSource):
    """Collect and normalize offers from Jooble."""

    name = "Jooble"

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_JOOBLE_BASE_URL,
        keywords: list[str] | None = None,
        location: str = "",
        max_pages: int = 1,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.keywords = _clean_terms(keywords or [])
        self.location = _clean(location)
        self.max_pages = max(max_pages, 1)
        self.timeout = timeout
        self._http_client = http_client or httpx.Client(timeout=timeout)

    def collect(self) -> SourceResult:
        raw_offers = self.collect_raw_offers()
        return SourceResult(
            source_name=self.name,
            raw_offers=raw_offers,
            normalized_offers=[normalize_jooble_offer(raw_offer) for raw_offer in raw_offers],
            stats=SourceStats(
                enabled=True,
                fetched=len(raw_offers),
                kept=len(raw_offers),
                filtered=0,
            ),
        )

    def collect_raw_offers(self) -> list[dict]:
        """Collect raw Jooble offers with conservative pagination."""

        offers: list[dict] = []
        search_terms = self.keywords or [""]

        for keyword in search_terms:
            for page in range(1, self.max_pages + 1):
                response = self._http_client.post(self._endpoint_url(), json=self._payload(keyword, page))
                _raise_for_status(response)
                payload = _json(response)
                page_offers = _jobs(payload)
                offers.extend(offer for offer in page_offers if isinstance(offer, dict))

        return offers

    def _endpoint_url(self) -> str:
        return f"{self.base_url}/{self.api_key}"

    def _payload(self, keyword: str, page: int) -> dict[str, Any]:
        payload: dict[str, Any] = {"keywords": keyword, "page": page}
        if self.location:
            payload["location"] = self.location
        return payload


def normalize_jooble_offer(raw_offer: dict) -> dict[str, Any]:
    """Normalize one Jooble offer dictionary into the AutoTache common format."""

    title = _clean(raw_offer.get("title"))
    description = _clean(raw_offer.get("snippet") or raw_offer.get("description"))
    company = _clean(raw_offer.get("company")) or "Non specifie"
    location = _clean(raw_offer.get("location"))
    salary_text = _clean(raw_offer.get("salary"))
    job_type = _clean(raw_offer.get("type") or raw_offer.get("job_type"))
    analysis_text = " ".join(value for value in (title, description, job_type) if value)

    teletravail = parse_teletravail(" ".join(value for value in (title, description, location) if value))
    salary = parse_salary(salary_text or description)
    technologies = extract_technologies(analysis_text)

    normalized = {
        "id_offre": _offer_id(raw_offer),
        "source": "Jooble",
        "titre": title,
        "description": description,
        "entreprise": company,
        "localisation": location,
        "code_postal": "",
        "type_contrat": job_type,
        "experience": "",
        "salaire_brut": salary_text,
        "salaire_min": salary["salaire_min"],
        "salaire_max": salary["salaire_max"],
        "salaire_moyen": salary["salaire_moyen"],
        "salaire_type": salary["salaire_type"],
        "teletravail_mention": teletravail["teletravail_mention"],
        "teletravail_jours": teletravail["teletravail_jours"],
        "technologies": technologies,
        "date_publication": _clean(raw_offer.get("updated") or raw_offer.get("date")),
        "date_actualisation": "",
        "url_offre": _clean(raw_offer.get("link")),
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

    message = response.text.strip().replace("\n", " ")[:160]
    if response.status_code == 403:
        hint = " La cle Jooble peut ne pas correspondre au domaine Jooble utilise."
    else:
        hint = ""
    raise JoobleSourceError(
        f"Erreur HTTP {response.status_code} pendant collecte Jooble.{hint} "
        f"Detail court: {message or 'aucun detail'}"
    )


def _json(response: httpx.Response) -> dict[str, Any]:
    if response.status_code == 204 or not response.text.strip():
        return {}

    try:
        data = response.json()
    except ValueError as exc:
        raise JoobleSourceError("Reponse JSON invalide pendant collecte Jooble.") from exc

    if not isinstance(data, dict):
        raise JoobleSourceError("Reponse inattendue pendant collecte Jooble: objet JSON attendu.")
    return data


def _jobs(payload: dict[str, Any]) -> list[dict]:
    for key in ("jobs", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _offer_id(raw_offer: dict) -> str:
    for key in ("id", "guid", "link"):
        value = _clean(raw_offer.get(key))
        if value:
            return value
    return ""


def _clean_terms(values: list[str]) -> list[str]:
    return [value.strip() for value in values if value and value.strip()]


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
