import httpx
import pytest

from autotache_jobs.sources.themuse import (
    TheMuseSource,
    TheMuseSourceError,
    normalize_themuse_offer,
)


def _source_with_transport(transport: httpx.MockTransport, **overrides) -> TheMuseSource:
    return TheMuseSource(
        base_url="https://example.test/themuse",
        http_client=httpx.Client(transport=transport),
        **overrides,
    )


def _frontend_offer(**overrides) -> dict:
    values = {
        "id": 12345,
        "name": "Frontend Developer WordPress",
        "contents": "Build HTML, CSS and JavaScript interfaces with React and WordPress.",
        "type": "external",
        "publication_date": "2026-05-01T10:00:00Z",
        "locations": [{"name": "Paris, France"}, {"name": "Remote"}],
        "categories": [{"name": "Software Engineering"}, {"name": "Design and UX"}],
        "levels": [{"name": "Mid Level"}],
        "refs": {"landing_page": "https://www.themuse.com/jobs/example/frontend-developer"},
        "company": {"name": "Studio Web"},
    }
    values.update(overrides)
    return values


def test_collect_raw_offers_returns_standard_themuse_response_without_real_network() -> None:
    seen_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_requests.append(request)
        return httpx.Response(
            200,
            json={"page": 1, "page_count": 1, "items_per_page": 20, "total": 1, "results": [_frontend_offer()]},
        )

    source = _source_with_transport(
        httpx.MockTransport(handler),
        keywords=[],
        location="France",
        page_size=20,
    )

    assert source.collect_raw_offers() == [_frontend_offer()]
    assert len(seen_requests) == 1
    assert seen_requests[0].url.params["page"] == "1"
    assert seen_requests[0].url.params["per_page"] == "20"
    assert seen_requests[0].url.params["location"] == "France"


def test_collect_raw_offers_returns_multiple_results() -> None:
    first = _frontend_offer(id=1, name="Frontend Developer")
    second = _frontend_offer(id=2, name="UI Designer")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"page": 1, "page_count": 1, "results": [first, second]})

    source = _source_with_transport(httpx.MockTransport(handler), keywords=[])

    assert source.collect_raw_offers() == [first, second]


def test_collect_raw_offers_handles_empty_response_and_missing_results_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"page": 1, "page_count": 1})

    source = _source_with_transport(httpx.MockTransport(handler))

    assert source.collect_raw_offers() == []


def test_normalize_themuse_offer_converts_standard_fields() -> None:
    normalized = normalize_themuse_offer(_frontend_offer())

    assert normalized["id_offre"] == "12345"
    assert normalized["source"] == "The Muse"
    assert normalized["titre"] == "Frontend Developer WordPress"
    assert normalized["entreprise"] == "Studio Web"
    assert normalized["url_offre"] == "https://www.themuse.com/jobs/example/frontend-developer"
    assert normalized["description"].startswith("Build HTML")
    assert normalized["localisation"] == "Paris, France, Remote"
    assert normalized["date_publication"] == "2026-05-01T10:00:00Z"
    assert normalized["type_contrat"] == "external"
    assert normalized["experience"] == "Mid Level"
    assert "JavaScript" in normalized["technologies"]


def test_normalize_themuse_offer_handles_missing_fields() -> None:
    normalized = normalize_themuse_offer({"id": "missing-fields"})

    assert normalized["id_offre"] == "missing-fields"
    assert normalized["source"] == "The Muse"
    assert normalized["titre"] == ""
    assert normalized["entreprise"] == "Non specifie"
    assert normalized["url_offre"] == ""
    assert normalized["localisation"] == ""
    assert normalized["date_publication"] == ""


def test_collect_raw_offers_raises_clear_error_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="API unavailable")

    source = _source_with_transport(httpx.MockTransport(handler))

    with pytest.raises(TheMuseSourceError, match="Erreur HTTP 500"):
        source.collect_raw_offers()


def test_collect_raw_offers_wraps_network_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out")

    source = _source_with_transport(httpx.MockTransport(handler))

    with pytest.raises(TheMuseSourceError, match="Erreur reseau"):
        source.collect_raw_offers()


def test_collect_raw_offers_respects_max_pages_limit() -> None:
    seen_pages = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_pages.append(request.url.params["page"])
        page = int(request.url.params["page"])
        return httpx.Response(
            200,
            json={
                "page": page,
                "page_count": 10,
                "results": [_frontend_offer(id=page, name=f"Frontend Developer {page}")],
            },
        )

    source = _source_with_transport(httpx.MockTransport(handler), max_pages=2, keywords=[])

    offers = source.collect_raw_offers()

    assert [offer["id"] for offer in offers] == [1, 2]
    assert seen_pages == ["1", "2"]


def test_collect_does_not_require_secret_and_adds_stats_without_real_network() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"page": 1, "page_count": 1, "results": [_frontend_offer()]})

    source = _source_with_transport(httpx.MockTransport(handler), keywords=["wordpress"])
    result = source.collect()

    assert result.source_name == "The Muse"
    assert len(result.raw_offers) == 1
    assert len(result.normalized_offers) == 1
    assert result.stats.enabled is True
    assert result.stats.fetched == 1
    assert result.stats.kept == 1
    assert result.stats.filtered == 0
    assert result.normalized_offers[0]["source"] == "The Muse"
