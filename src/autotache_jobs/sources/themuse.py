"""The Muse offer source."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ..filters import is_relevant_offer
from ..parsers import extract_technologies, parse_salary, parse_teletravail
from ..scoring import score_offer
from .base import JobSource, SourceResult, SourceStats


DEFAULT_THEMUSE_BASE_URL = "https://www.themuse.com/api/public/jobs"


class TheMuseSourceError(RuntimeError):
    """Raised when The Muse returns an invalid or failed response."""


class TheMuseSource(JobSource):
    """Collect and normalize offers from The Muse."""

    name = "The Muse"

    def __init__(
        self,
        base_url: str = DEFAULT_THEMUSE_BASE_URL,
        keywords: list[str] | None = None,
        location: str = "",
        max_pages: int = 1,
        page_size: int = 20,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.strip() or DEFAULT_THEMUSE_BASE_URL
        self.keywords = _clean_terms(keywords or [])
        self.location = _clean(location)
        self.max_pages = max(max_pages, 1)
        self.page_size = max(page_size, 1)
        self.timeout = timeout
        self._http_client = http_client or httpx.Client(timeout=timeout)

    def collect(self) -> SourceResult:
        fetched_offers = self.collect_fetched_offers()
        raw_offers = filter_raw_offers(fetched_offers, keywords=self.keywords)
        return SourceResult(
            source_name=self.name,
            raw_offers=raw_offers,
            normalized_offers=[normalize_themuse_offer(raw_offer) for raw_offer in raw_offers],
            stats=SourceStats(
                enabled=True,
                fetched=len(fetched_offers),
                kept=len(raw_offers),
                filtered=len(fetched_offers) - len(raw_offers),
            ),
        )

    def collect_raw_offers(self) -> list[dict]:
        """Collect raw The Muse offers after applying local source filters."""

        return filter_raw_offers(self.collect_fetched_offers(), keywords=self.keywords)

    def collect_fetched_offers(self) -> list[dict]:
        """Collect raw The Muse offers with conservative page-based pagination."""

        offers: list[dict] = []

        for page in range(1, self.max_pages + 1):
            try:
                response = self._http_client.get(self.base_url, params=self._params(page))
            except httpx.RequestError as exc:
                raise TheMuseSourceError("Erreur reseau pendant collecte The Muse.") from exc

            _raise_for_status(response)
            payload = _json(response)
            page_offers = payload.get("results", [])
            if not isinstance(page_offers, list) or not page_offers:
                break

            offers.extend(offer for offer in page_offers if isinstance(offer, dict))

            page_count = payload.get("page_count")
            if isinstance(page_count, int) and page >= page_count:
                break

        return offers

    def _params(self, page: int) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "per_page": self.page_size}
        if self.location:
            params["location"] = self.location
        return params


def filter_raw_offers(raw_offers: list[dict], keywords: list[str] | None = None) -> list[dict]:
    """Return The Muse offers matching optional local keyword filters."""

    keyword_terms = _clean_terms(keywords or [])
    return [offer for offer in raw_offers if matches_keywords(offer, keyword_terms)]


def matches_keywords(raw_offer: dict, keywords: list[str] | None = None) -> bool:
    """Return true when a The Muse offer matches at least one configured keyword."""

    terms = _clean_terms(keywords or [])
    if not terms:
        return True

    text = _normalize_filter_text(_offer_search_text(raw_offer))
    return any(_normalize_filter_text(term) in text for term in terms)


def normalize_themuse_offer(raw_offer: dict) -> dict[str, Any]:
    """Normalize one The Muse offer dictionary into the AutoTache common format."""

    title = _clean(raw_offer.get("name"))
    description = _clean(raw_offer.get("contents"))
    company = _clean(_nested(raw_offer, "company", "name")) or "Non specifie"
    location = _named_values_text(raw_offer.get("locations"))
    categories_text = _named_values_text(raw_offer.get("categories"))
    levels_text = _named_values_text(raw_offer.get("levels"))
    job_type = _clean(raw_offer.get("type"))
    analysis_text = " ".join(
        value for value in (title, description, categories_text, levels_text, job_type) if value
    )

    teletravail = parse_teletravail(" ".join(value for value in (title, description, location) if value))
    salary = parse_salary(description)
    technologies = extract_technologies(analysis_text)

    normalized = {
        "id_offre": _offer_id(raw_offer),
        "source": "The Muse",
        "titre": title,
        "description": description,
        "entreprise": company,
        "localisation": location,
        "code_postal": "",
        "type_contrat": job_type or categories_text,
        "experience": levels_text,
        "salaire_brut": "",
        "salaire_min": salary["salaire_min"],
        "salaire_max": salary["salaire_max"],
        "salaire_moyen": salary["salaire_moyen"],
        "salaire_type": salary["salaire_type"],
        "teletravail_mention": teletravail["teletravail_mention"],
        "teletravail_jours": teletravail["teletravail_jours"],
        "technologies": technologies,
        "date_publication": _clean(raw_offer.get("publication_date")),
        "date_actualisation": "",
        "url_offre": _clean(_nested(raw_offer, "refs", "landing_page")),
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
    raise TheMuseSourceError(
        f"Erreur HTTP {response.status_code} pendant collecte The Muse: {message or 'aucun detail'}"
    )


def _json(response: httpx.Response) -> dict[str, Any]:
    if response.status_code == 204 or not response.text.strip():
        return {}

    try:
        data = response.json()
    except ValueError as exc:
        raise TheMuseSourceError("Reponse JSON invalide pendant collecte The Muse.") from exc

    if not isinstance(data, dict):
        raise TheMuseSourceError("Reponse inattendue pendant collecte The Muse: objet JSON attendu.")
    return data


def _offer_id(raw_offer: dict) -> str:
    for key in ("id", "short_name"):
        value = _clean(raw_offer.get(key))
        if value:
            return value
    return _clean(_nested(raw_offer, "refs", "landing_page"))


def _named_values_text(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    return ", ".join(
        _clean(item.get("name") if isinstance(item, dict) else item)
        for item in value
        if _clean(item.get("name") if isinstance(item, dict) else item)
    )


def _nested(raw_offer: dict, parent_key: str, child_key: str) -> Any:
    parent = raw_offer.get(parent_key)
    if not isinstance(parent, dict):
        return ""
    return parent.get(child_key, "")


def _offer_search_text(raw_offer: dict) -> str:
    return " ".join(
        value
        for value in (
            _clean(raw_offer.get("name")),
            _clean(raw_offer.get("contents")),
            _clean(_nested(raw_offer, "company", "name")),
            _named_values_text(raw_offer.get("locations")),
            _named_values_text(raw_offer.get("categories")),
            _named_values_text(raw_offer.get("levels")),
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
