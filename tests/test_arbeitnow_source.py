import httpx
import pytest

from autotache_jobs.sources.arbeitnow import ArbeitnowSource, ArbeitnowSourceError, normalize_arbeitnow_offer


def _source_with_transport(transport: httpx.MockTransport, **overrides) -> ArbeitnowSource:
    return ArbeitnowSource(
        endpoint_url="https://example.test/arbeitnow",
        http_client=httpx.Client(transport=transport),
        **overrides,
    )


def _frontend_offer(**overrides) -> dict:
    values = {
        "slug": "frontend-wordpress",
        "title": "Frontend Developer WordPress",
        "description": (
            "Build responsive interfaces with WordPress, Elementor, HTML, CSS and JavaScript. "
            "Remote work possible."
        ),
        "company_name": "Studio Web",
        "location": "Remote",
        "remote": True,
        "job_types": ["Full-time"],
        "tags": ["WordPress", "Elementor", "React"],
        "created_at": "2026-05-01T10:00:00Z",
        "url": "https://www.arbeitnow.com/jobs/frontend-wordpress",
    }
    values.update(overrides)
    return values


def test_collect_raw_offers_returns_data_from_mocked_response() -> None:
    seen_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(
            200,
            json={
                "data": [{"slug": "A1"}, {"slug": "A2"}],
                "links": {"next": None},
                "meta": {"current_page": 1},
            },
        )

    source = _source_with_transport(httpx.MockTransport(handler))

    assert source.collect_raw_offers() == [{"slug": "A1"}, {"slug": "A2"}]
    assert seen_urls == ["https://example.test/arbeitnow"]


def test_collect_raw_offers_handles_empty_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [], "links": {"next": None}, "meta": {}})

    source = _source_with_transport(httpx.MockTransport(handler))

    assert source.collect_raw_offers() == []


def test_collect_raw_offers_raises_clear_error_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="API unavailable")

    source = _source_with_transport(httpx.MockTransport(handler))

    with pytest.raises(ArbeitnowSourceError, match="Erreur HTTP 500"):
        source.collect_raw_offers()


def test_collect_raw_offers_follows_pagination_up_to_max_pages() -> None:
    seen_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        if str(request.url) == "https://example.test/arbeitnow":
            return httpx.Response(
                200,
                json={
                    "data": [{"slug": "A1"}],
                    "links": {"next": "https://example.test/arbeitnow?page=2"},
                    "meta": {"current_page": 1},
                },
            )
        return httpx.Response(
            200,
            json={"data": [{"slug": "A2"}], "links": {"next": None}, "meta": {"current_page": 2}},
        )

    source = _source_with_transport(httpx.MockTransport(handler), max_pages=2)

    assert source.collect_raw_offers() == [{"slug": "A1"}, {"slug": "A2"}]
    assert seen_urls == ["https://example.test/arbeitnow", "https://example.test/arbeitnow?page=2"]


def test_normalize_arbeitnow_offer_marks_frontend_offer_relevant() -> None:
    normalized = normalize_arbeitnow_offer(_frontend_offer())

    assert normalized["id_offre"] == "frontend-wordpress"
    assert normalized["source"] == "Arbeitnow"
    assert normalized["titre"] == "Frontend Developer WordPress"
    assert normalized["entreprise"] == "Studio Web"
    assert normalized["is_relevant"] is True
    assert "WordPress" in normalized["matched_keywords"]
    assert normalized["decision"] in {"Pertinent", "Ã€ vÃ©rifier"}


def test_normalize_arbeitnow_offer_marks_non_relevant_offer_rejected() -> None:
    normalized = normalize_arbeitnow_offer(
        {
            "slug": "data-analyst",
            "title": "Data Analyst",
            "description": "SQL reporting and BI dashboards.",
            "company_name": "Data Corp",
            "url": "https://www.arbeitnow.com/jobs/data-analyst",
        }
    )

    assert normalized["is_relevant"] is False
    assert "data analyst" in normalized["excluded_by"]
    assert normalized["decision"].startswith("Rejet")


def test_normalize_arbeitnow_offer_extracts_technologies_from_title_description_and_tags() -> None:
    normalized = normalize_arbeitnow_offer(
        _frontend_offer(
            title="UI Designer",
            description="Create Figma mockups and HTML CSS interfaces.",
            tags=["React", "Tailwind", "JavaScript"],
        )
    )

    assert normalized["technologies"] == ["HTML", "CSS", "JavaScript", "React", "Tailwind", "Figma", "UI"]


def test_collect_adds_normalization_and_scoring_without_real_network() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [_frontend_offer()], "links": {"next": None}, "meta": {}})

    source = _source_with_transport(httpx.MockTransport(handler))
    result = source.collect()

    assert result.source_name == "Arbeitnow"
    assert len(result.raw_offers) == 1
    assert len(result.normalized_offers) == 1
    assert isinstance(result.normalized_offers[0]["score_total"], int)
    assert result.normalized_offers[0]["score_reason"]
    assert isinstance(result.normalized_offers[0]["score_details"], dict)
