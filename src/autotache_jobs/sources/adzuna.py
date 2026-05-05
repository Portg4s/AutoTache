"""Adzuna offer source."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ..filters import is_relevant_offer
from ..parsers import extract_technologies, parse_salary, parse_teletravail
from ..scoring import score_offer
from .base import JobSource, SourceResult, SourceStats


DEFAULT_ADZUNA_ENDPOINT_BASE = "https://api.adzuna.com/v1/api/jobs"


class AdzunaSourceError(RuntimeError):
    """Raised when Adzuna returns an invalid or failed response."""


class AdzunaSource(JobSource):
    """Collect and normalize offers from Adzuna."""

    name = "Adzuna"

    def __init__(
        self,
        app_id: str,
        app_key: str,
        endpoint_base_url: str = DEFAULT_ADZUNA_ENDPOINT_BASE,
        country: str = "fr",
        keywords: list[str] | None = None,
        location: str = "",
        results_per_page: int = 20,
        max_pages: int = 1,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.app_id = app_id
        self.app_key = app_key
        self.endpoint_base_url = endpoint_base_url.rstrip("/")
        self.country = (country or "fr").strip() or "fr"
        self.keywords = _clean_terms(keywords or [])
        self.location = _clean(location)
        self.results_per_page = max(results_per_page, 1)
        self.max_pages = max(max_pages, 1)
        self.timeout = timeout
        self._http_client = http_client or httpx.Client(timeout=timeout)

    def collect(self) -> SourceResult:
        fetched_offers = self.collect_fetched_offers()
        raw_offers = filter_raw_offers(fetched_offers, keywords=self.keywords)
        return SourceResult(
            source_name=self.name,
            raw_offers=raw_offers,
            normalized_offers=[normalize_adzuna_offer(raw_offer) for raw_offer in raw_offers],
            stats=SourceStats(
                enabled=True,
                fetched=len(fetched_offers),
                kept=len(raw_offers),
                filtered=len(fetched_offers) - len(raw_offers),
            ),
        )

    def collect_raw_offers(self) -> list[dict]:
        """Collect raw Adzuna offers after applying local source filters."""

        return filter_raw_offers(self.collect_fetched_offers(), keywords=self.keywords)

    def collect_fetched_offers(self) -> list[dict]:
        """Collect raw Adzuna offers from paginated API pages before local filters."""

        offers: list[dict] = []
        for page in range(1, self.max_pages + 1):
            response = self._http_client.get(self._page_url(page), params=self._params())
            _raise_for_status(response)
            payload = _json(response)
            page_offers = payload.get("results", [])
            if isinstance(page_offers, list):
                offers.extend(offer for offer in page_offers if isinstance(offer, dict))

        return offers

    def _page_url(self, page: int) -> str:
        return f"{self.endpoint_base_url}/{self.country}/search/{page}"

    def _params(self) -> dict[str, Any]:
        params: dict[str, Any] = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": self.results_per_page,
        }
        if self.keywords:
            params["what"] = " ".join(self.keywords)
        if self.location:
            params["where"] = self.location
        return params


def filter_raw_offers(raw_offers: list[dict], keywords: list[str] | None = None) -> list[dict]:
    """Return Adzuna offers matching optional local keyword filters."""

    keyword_terms = _clean_terms(keywords or [])
    return [offer for offer in raw_offers if matches_keywords(offer, keyword_terms)]


def matches_keywords(raw_offer: dict, keywords: list[str] | None = None) -> bool:
    """Return true when an Adzuna offer matches at least one configured keyword."""

    terms = _clean_terms(keywords or [])
    if not terms:
        return True

    text = _normalize_filter_text(_offer_search_text(raw_offer))
    return any(_normalize_filter_text(term) in text for term in terms)


def normalize_adzuna_offer(raw_offer: dict) -> dict[str, Any]:
    """Normalize one Adzuna offer dictionary into the AutoTache common format."""

    title = _clean(raw_offer.get("title"))
    description = _clean(raw_offer.get("description"))
    category = _clean(_nested(raw_offer, "category", "label"))
    contract_type = _clean(raw_offer.get("contract_type") or raw_offer.get("contract_time"))
    location = _location_text(raw_offer)
    company = _clean(_nested(raw_offer, "company", "display_name")) or "Non specifie"
    salary_text = _salary_text(raw_offer)
    analysis_text = " ".join(value for value in (title, description, category, contract_type) if value)

    teletravail = parse_teletravail(" ".join(value for value in (title, description, location) if value))
    salary = parse_salary(salary_text or description)
    technologies = extract_technologies(analysis_text)

    normalized = {
        "id_offre": _offer_id(raw_offer),
        "source": "Adzuna",
        "titre": title,
        "description": description,
        "entreprise": company,
        "localisation": location,
        "code_postal": "",
        "type_contrat": contract_type or category,
        "experience": "",
        "salaire_brut": salary_text,
        "salaire_min": salary["salaire_min"],
        "salaire_max": salary["salaire_max"],
        "salaire_moyen": salary["salaire_moyen"],
        "salaire_type": salary["salaire_type"],
        "teletravail_mention": teletravail["teletravail_mention"],
        "teletravail_jours": teletravail["teletravail_jours"],
        "technologies": technologies,
        "date_publication": _clean(raw_offer.get("created")),
        "date_actualisation": "",
        "url_offre": _clean(raw_offer.get("redirect_url")),
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
    raise AdzunaSourceError(f"Erreur HTTP {response.status_code} pendant collecte Adzuna: {message or 'aucun detail'}")


def _json(response: httpx.Response) -> dict[str, Any]:
    if response.status_code == 204 or not response.text.strip():
        return {}

    try:
        data = response.json()
    except ValueError as exc:
        raise AdzunaSourceError("Reponse JSON invalide pendant collecte Adzuna.") from exc

    if not isinstance(data, dict):
        raise AdzunaSourceError("Reponse inattendue pendant collecte Adzuna: objet JSON attendu.")
    return data


def _offer_id(raw_offer: dict) -> str:
    for key in ("id", "adref", "redirect_url"):
        value = _clean(raw_offer.get(key))
        if value:
            return value
    return ""


def _salary_text(raw_offer: dict) -> str:
    salary_min = raw_offer.get("salary_min")
    salary_max = raw_offer.get("salary_max")
    if salary_min is not None and salary_max is not None:
        return f"{salary_min} euros - {salary_max} euros annuel"
    if salary_min is not None:
        return f"{salary_min} euros annuel"
    if salary_max is not None:
        return f"{salary_max} euros annuel"
    return _clean(raw_offer.get("salary"))


def _location_text(raw_offer: dict) -> str:
    area = _nested(raw_offer, "location", "area")
    if isinstance(area, list):
        return ", ".join(_clean(item) for item in area if _clean(item))
    return _clean(_nested(raw_offer, "location", "display_name"))


def _nested(raw_offer: dict, parent_key: str, child_key: str) -> Any:
    parent = raw_offer.get(parent_key)
    if not isinstance(parent, dict):
        return ""
    return parent.get(child_key, "")


def _offer_search_text(raw_offer: dict) -> str:
    return " ".join(
        value
        for value in (
            _clean(raw_offer.get("title")),
            _clean(raw_offer.get("description")),
            _clean(_nested(raw_offer, "category", "label")),
            _clean(_nested(raw_offer, "company", "display_name")),
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
