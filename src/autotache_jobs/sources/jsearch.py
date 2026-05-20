"""JSearch offer source through RapidAPI."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ..filters import is_relevant_offer
from ..parsers import extract_technologies, parse_salary, parse_teletravail
from ..scoring import score_offer
from .base import JobSource, SourceResult, SourceStats


DEFAULT_JSEARCH_ENDPOINT = "https://jsearch.p.rapidapi.com/search-v2"
DEFAULT_JSEARCH_HOST = "jsearch.p.rapidapi.com"


class JSearchSourceError(RuntimeError):
    """Raised when JSearch returns an invalid or failed response."""


class JSearchSource(JobSource):
    """Collect and normalize offers from JSearch."""

    name = "JSearch"

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_JSEARCH_ENDPOINT,
        host: str = DEFAULT_JSEARCH_HOST,
        max_pages: int = 1,
        queries: list[str] | None = None,
        country: str = "fr",
        language: str = "fr",
        location: str = "",
        radius: int | None = None,
        date_posted: str = "",
        work_from_home: bool | None = None,
        employment_types: list[str] | None = None,
        fields: str = "",
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.api_key = _clean(api_key)
        self.base_url = _clean(base_url) or DEFAULT_JSEARCH_ENDPOINT
        self.host = _clean(host) or DEFAULT_JSEARCH_HOST
        self.max_pages = min(max(max_pages, 1), 20)
        self.queries = _clean_terms(queries or [])
        self.country = _clean(country)
        self.language = _clean(language)
        self.location = _clean(location)
        self.radius = radius
        self.date_posted = _clean(date_posted)
        self.work_from_home = work_from_home
        self.employment_types = _clean_terms(employment_types or [])
        self.fields = _clean(fields)
        self.timeout = timeout
        self._http_client = http_client or httpx.Client(timeout=timeout)

    def collect(self) -> SourceResult:
        raw_offers = self.collect_raw_offers()
        return SourceResult(
            source_name=self.name,
            raw_offers=raw_offers,
            normalized_offers=[normalize_jsearch_offer(raw_offer) for raw_offer in raw_offers],
            stats=SourceStats(
                enabled=True,
                fetched=len(raw_offers),
                kept=len(raw_offers),
                filtered=0,
            ),
        )

    def collect_raw_offers(self) -> list[dict]:
        """Collect raw JSearch offers with one HTTP request per configured query."""

        offers: list[dict] = []
        for query in self.queries:
            try:
                response = self._http_client.get(
                    self.base_url,
                    headers=self._headers(),
                    params=self._params(query),
                )
            except httpx.RequestError as exc:
                raise JSearchSourceError("Erreur reseau ou timeout pendant collecte JSearch.") from exc

            _raise_for_status(response)
            payload = _json(response)
            offers.extend(_data(payload))

        return offers

    def _headers(self) -> dict[str, str]:
        return {
            "x-rapidapi-host": self.host,
            "x-rapidapi-key": self.api_key,
        }

    def _params(self, query: str) -> dict[str, Any]:
        params: dict[str, Any] = {
            "query": query,
            "num_pages": self.max_pages,
        }
        if self.country:
            params["country"] = self.country
        if self.language:
            params["language"] = self.language
        if self.location:
            params["location"] = self.location
        if self.radius is not None:
            params["radius"] = self.radius
        if self.date_posted:
            params["date_posted"] = self.date_posted
        if self.work_from_home is not None:
            params["work_from_home"] = self.work_from_home
        if self.employment_types:
            params["employment_types"] = ",".join(self.employment_types)
        if self.fields:
            params["fields"] = self.fields
        return params


def normalize_jsearch_offer(raw_offer: dict) -> dict[str, Any]:
    """Normalize one JSearch offer dictionary into the AutoTache common format."""

    title = _clean(raw_offer.get("job_title"))
    description = _clean(raw_offer.get("job_description"))
    company = _clean(raw_offer.get("employer_name")) or "Non specifie"
    location = _location_text(raw_offer)
    job_type = _clean(raw_offer.get("job_employment_type"))
    salary_text = _salary_text(raw_offer)
    analysis_text = " ".join(value for value in (title, description, job_type) if value)

    remote_label = "remote" if raw_offer.get("job_is_remote") is True else ""
    teletravail = parse_teletravail(" ".join(value for value in (remote_label, description) if value))
    salary = _salary(raw_offer, salary_text or description)
    technologies = extract_technologies(analysis_text)

    normalized = {
        "id_offre": _clean(raw_offer.get("job_id")),
        "source": "JSearch",
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
        "salaire_currency": _clean(raw_offer.get("job_salary_currency")),
        "salaire_period": _clean(raw_offer.get("job_salary_period")),
        "teletravail_mention": teletravail["teletravail_mention"],
        "teletravail_jours": teletravail["teletravail_jours"],
        "technologies": technologies,
        "date_publication": _clean(raw_offer.get("job_posted_at_datetime_utc")),
        "date_actualisation": "",
        "url_offre": _clean(raw_offer.get("job_apply_link") or raw_offer.get("job_google_link")),
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
    raise JSearchSourceError(
        f"Erreur HTTP {response.status_code} pendant collecte JSearch. Detail court: {message or 'aucun detail'}"
    )


def _json(response: httpx.Response) -> dict[str, Any]:
    if response.status_code == 204 or not response.text.strip():
        return {}

    try:
        data = response.json()
    except ValueError as exc:
        raise JSearchSourceError("Reponse JSON invalide pendant collecte JSearch.") from exc

    if not isinstance(data, dict):
        raise JSearchSourceError("Reponse inattendue pendant collecte JSearch: objet JSON attendu.")
    return data


def _data(payload: dict[str, Any]) -> list[dict]:
    data = payload.get("data", [])
    if isinstance(data, list):
        return [offer for offer in data if isinstance(offer, dict)]
    if isinstance(data, dict):
        jobs = data.get("jobs", [])
        if isinstance(jobs, list):
            return [offer for offer in jobs if isinstance(offer, dict)]
    return []


def _location_text(raw_offer: dict) -> str:
    parts = [
        _clean(raw_offer.get("job_city")),
        _clean(raw_offer.get("job_state")),
        _clean(raw_offer.get("job_country")),
    ]
    return ", ".join(part for part in parts if part)


def _salary(raw_offer: dict, fallback_text: str) -> dict[str, Any]:
    salary = parse_salary(fallback_text)
    salary_min = raw_offer.get("job_min_salary")
    salary_max = raw_offer.get("job_max_salary")

    if salary_min is not None:
        salary["salaire_min"] = salary_min
    if salary_max is not None:
        salary["salaire_max"] = salary_max
    if salary["salaire_min"] is not None and salary["salaire_max"] is not None:
        salary["salaire_moyen"] = round((salary["salaire_min"] + salary["salaire_max"]) / 2, 2)
    elif salary["salaire_min"] is not None:
        salary["salaire_moyen"] = salary["salaire_min"]

    period = _clean(raw_offer.get("job_salary_period"))
    if period:
        salary["salaire_type"] = period

    return salary


def _salary_text(raw_offer: dict) -> str:
    salary_min = raw_offer.get("job_min_salary")
    salary_max = raw_offer.get("job_max_salary")
    currency = _clean(raw_offer.get("job_salary_currency"))
    period = _clean(raw_offer.get("job_salary_period"))
    suffix = " ".join(value for value in (currency, period) if value)
    if salary_min is not None and salary_max is not None:
        return f"{salary_min} - {salary_max} {suffix}".strip()
    if salary_min is not None:
        return f"{salary_min} {suffix}".strip()
    if salary_max is not None:
        return f"{salary_max} {suffix}".strip()
    return _clean(raw_offer.get("job_salary"))


def _clean_terms(values: list[str]) -> list[str]:
    return [value.strip() for value in values if value and value.strip()]


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
