import httpx
import pytest

from autotache_jobs.sources.remotive import (
    RemotiveSource,
    RemotiveSourceError,
    filter_raw_offers,
    matches_keywords,
    normalize_remotive_offer,
)


def _source_with_transport(transport: httpx.MockTransport, **overrides) -> RemotiveSource:
    return RemotiveSource(
        endpoint_url="https://example.test/remotive",
        http_client=httpx.Client(transport=transport),
        **overrides,
    )


def _frontend_offer(**overrides) -> dict:
    values = {
        "id": 123,
        "url": "https://remotive.com/remote-jobs/software-dev/frontend-wordpress-123",
        "title": "Frontend Developer WordPress",
        "company_name": "Remote Studio",
        "candidate_required_location": "Worldwide",
        "job_type": "full_time",
        "category": "Software Development",
        "description": (
            "Build WordPress interfaces with Elementor, HTML, CSS and JavaScript. "
            "Remote work possible."
        ),
        "salary": "$50k - $70k",
        "publication_date": "2026-05-01T10:00:00",
        "tags": ["WordPress", "Elementor", "React"],
    }
    values.update(overrides)
    return values


def test_collect_raw_offers_returns_jobs_from_mocked_response() -> None:
    seen_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, json={"jobs": [{"id": 1}, {"id": 2}]})

    source = _source_with_transport(httpx.MockTransport(handler))

    assert source.collect_raw_offers() == [{"id": 1}, {"id": 2}]
    assert seen_urls == ["https://example.test/remotive"]


def test_collect_raw_offers_handles_empty_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"jobs": []})

    source = _source_with_transport(httpx.MockTransport(handler))

    assert source.collect_raw_offers() == []


def test_collect_raw_offers_raises_clear_error_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="API unavailable")

    source = _source_with_transport(httpx.MockTransport(handler))

    with pytest.raises(RemotiveSourceError, match="Erreur HTTP 500"):
        source.collect_raw_offers()


def test_remotive_filter_keeps_offer_when_keyword_matches_title() -> None:
    assert matches_keywords(_frontend_offer(title="Senior Frontend Engineer"), ["frontend"]) is True


def test_remotive_filter_keeps_offer_when_keyword_matches_description() -> None:
    offer = _frontend_offer(title="Product Designer", description="Design web interfaces with Figma.")

    assert matches_keywords(offer, ["figma"]) is True


def test_remotive_filter_rejects_offer_when_no_keyword_matches() -> None:
    offer = _frontend_offer(title="Account Manager", description="Sales and partnerships.", tags=[])

    assert matches_keywords(offer, ["wordpress", "frontend"]) is False
    assert filter_raw_offers([offer], keywords=["wordpress", "frontend"]) == []


def test_remotive_filter_does_not_filter_when_keywords_empty() -> None:
    offer = _frontend_offer(title="Account Manager", description="Sales and partnerships.", tags=[])

    assert matches_keywords(offer, []) is True
    assert filter_raw_offers([offer], keywords=[]) == [offer]


def test_normalize_remotive_offer_marks_frontend_offer_relevant() -> None:
    normalized = normalize_remotive_offer(_frontend_offer())

    assert normalized["id_offre"] == "123"
    assert normalized["source"] == "Remotive"
    assert normalized["titre"] == "Frontend Developer WordPress"
    assert normalized["entreprise"] == "Remote Studio"
    assert normalized["url_offre"] == "https://remotive.com/remote-jobs/software-dev/frontend-wordpress-123"
    assert normalized["is_relevant"] is True
    assert "WordPress" in normalized["matched_keywords"]
    assert normalized["decision"] in {"Pertinent", "Ã€ vÃ©rifier"}


def test_normalize_remotive_offer_marks_non_relevant_offer_rejected() -> None:
    normalized = normalize_remotive_offer(
        {
            "id": 999,
            "title": "Data Analyst",
            "description": "SQL reporting and BI dashboards.",
            "company_name": "Data Corp",
            "url": "https://remotive.com/remote-jobs/data/data-analyst-999",
        }
    )

    assert normalized["source"] == "Remotive"
    assert normalized["is_relevant"] is False
    assert "data analyst" in normalized["excluded_by"]
    assert normalized["decision"].startswith("Rejet")


def test_normalize_remotive_offer_extracts_technologies_from_title_description_and_tags() -> None:
    normalized = normalize_remotive_offer(
        _frontend_offer(
            title="UI Designer",
            description="Create Figma mockups and HTML CSS interfaces.",
            tags=["React", "Tailwind", "JavaScript"],
        )
    )

    assert normalized["technologies"] == ["HTML", "CSS", "JavaScript", "React", "Tailwind", "Figma", "UI"]


def test_collect_adds_normalization_and_scoring_without_real_network() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"jobs": [_frontend_offer()]})

    source = _source_with_transport(httpx.MockTransport(handler))
    result = source.collect()

    assert result.source_name == "Remotive"
    assert len(result.raw_offers) == 1
    assert len(result.normalized_offers) == 1
    assert result.stats.enabled is True
    assert result.stats.fetched == 1
    assert result.stats.kept == 1
    assert result.stats.filtered == 0
    assert result.normalized_offers[0]["source"] == "Remotive"
    assert isinstance(result.normalized_offers[0]["score_total"], int)
    assert result.normalized_offers[0]["score_reason"]
    assert isinstance(result.normalized_offers[0]["score_details"], dict)


def test_collect_returns_filtered_source_stats_without_real_network() -> None:
    kept = _frontend_offer(id=1, title="Frontend Developer")
    rejected = _frontend_offer(id=2, title="Sales Manager", description="Sales.", tags=[])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"jobs": [kept, rejected]})

    source = _source_with_transport(httpx.MockTransport(handler), keywords=["frontend"])
    result = source.collect()

    assert result.raw_offers == [kept]
    assert result.stats.fetched == 2
    assert result.stats.kept == 1
    assert result.stats.filtered == 1
