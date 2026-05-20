import httpx
import pytest

from autotache_jobs.sources.jsearch import JSearchSource, JSearchSourceError, normalize_jsearch_offer


def _source_with_transport(transport: httpx.MockTransport, **overrides) -> JSearchSource:
    values = {
        "api_key": "test-jsearch-key",
        "base_url": "https://example.test/jsearch",
        "host": "example.test",
        "queries": ["informatique Dijon"],
        "http_client": httpx.Client(transport=transport),
    }
    values.update(overrides)
    return JSearchSource(**values)


def _frontend_offer(**overrides) -> dict:
    values = {
        "job_id": "jsearch-front",
        "job_title": "Frontend Developer WordPress",
        "employer_name": "Studio Web",
        "job_description": (
            "Build WordPress interfaces with Elementor, HTML, CSS and JavaScript. "
            "Remote work possible."
        ),
        "job_apply_link": "https://example.test/apply/jsearch-front",
        "job_google_link": "https://google.test/jobs/jsearch-front",
        "job_city": "Dijon",
        "job_state": "Bourgogne-Franche-Comte",
        "job_country": "FR",
        "job_employment_type": "FULLTIME",
        "job_is_remote": True,
        "job_posted_at_datetime_utc": "2026-05-01T10:00:00.000Z",
        "job_min_salary": 35000,
        "job_max_salary": 45000,
        "job_salary_currency": "EUR",
        "job_salary_period": "YEAR",
    }
    values.update(overrides)
    return values


def test_collect_raw_offers_returns_result_from_mocked_response() -> None:
    seen_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, json={"data": [_frontend_offer()]})

    source = _source_with_transport(httpx.MockTransport(handler))

    assert source.collect_raw_offers() == [_frontend_offer()]
    assert len(seen_urls) == 1
    assert "https://example.test/jsearch" in seen_urls[0]


def test_collect_raw_offers_returns_multiple_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"job_id": "A1"}, {"job_id": "A2"}]})

    source = _source_with_transport(httpx.MockTransport(handler))

    assert source.collect_raw_offers() == [{"job_id": "A1"}, {"job_id": "A2"}]


def test_collect_raw_offers_accepts_search_v2_jobs_payload_without_following_cursor() -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, json={"data": {"jobs": [{"job_id": "A1"}, {"job_id": "A2"}], "cursor": "fake"}})

    source = _source_with_transport(httpx.MockTransport(handler))

    assert source.collect_raw_offers() == [{"job_id": "A1"}, {"job_id": "A2"}]
    assert len(calls) == 1


def test_normalize_jsearch_offer_handles_missing_fields() -> None:
    normalized = normalize_jsearch_offer({"job_id": "minimal"})

    assert normalized["id_offre"] == "minimal"
    assert normalized["source"] == "JSearch"
    assert normalized["entreprise"] == "Non specifie"
    assert normalized["localisation"] == ""
    assert normalized["url_offre"] == ""


def test_collect_raw_offers_handles_empty_and_missing_data() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    source = _source_with_transport(httpx.MockTransport(handler))

    assert source.collect_raw_offers() == []


def test_collect_raw_offers_handles_non_list_data() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"job_id": "bad-shape"}})

    source = _source_with_transport(httpx.MockTransport(handler))

    assert source.collect_raw_offers() == []


def test_collect_raw_offers_raises_clear_error_on_http_error_without_exposing_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="quota exceeded")

    source = _source_with_transport(httpx.MockTransport(handler))

    with pytest.raises(JSearchSourceError) as exc_info:
        source.collect_raw_offers()

    message = str(exc_info.value)
    assert "Erreur HTTP 429" in message
    assert "test-jsearch-key" not in message


def test_collect_raw_offers_raises_clear_error_on_request_error_without_exposing_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timeout", request=request)

    source = _source_with_transport(httpx.MockTransport(handler))

    with pytest.raises(JSearchSourceError) as exc_info:
        source.collect_raw_offers()

    message = str(exc_info.value)
    assert "Erreur reseau ou timeout" in message
    assert "test-jsearch-key" not in message


def test_collect_raw_offers_sends_rapidapi_headers_and_conservative_params() -> None:
    seen_headers = {}
    seen_params = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers["host"] = request.headers["x-rapidapi-host"]
        seen_headers["key"] = request.headers["x-rapidapi-key"]
        seen_params.update(dict(request.url.params))
        return httpx.Response(200, json={"data": []})

    source = _source_with_transport(
        httpx.MockTransport(handler),
        max_pages=2,
        country="fr",
        language="fr",
        location="Dijon",
        radius=50,
        date_posted="month",
        employment_types=["FULLTIME", "CONTRACT"],
    )

    source.collect_raw_offers()

    assert seen_headers == {"host": "example.test", "key": "test-jsearch-key"}
    assert seen_params["query"] == "informatique Dijon"
    assert seen_params["num_pages"] == "2"
    assert seen_params["country"] == "fr"
    assert seen_params["language"] == "fr"
    assert seen_params["location"] == "Dijon"
    assert seen_params["radius"] == "50"
    assert seen_params["date_posted"] == "month"
    assert seen_params["employment_types"] == "FULLTIME,CONTRACT"


def test_collect_raw_offers_makes_one_request_per_query() -> None:
    seen_queries = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_queries.append(request.url.params["query"])
        return httpx.Response(200, json={"data": []})

    source = _source_with_transport(httpx.MockTransport(handler), queries=["informatique Dijon", "frontend Lyon"])

    source.collect_raw_offers()

    assert seen_queries == ["informatique Dijon", "frontend Lyon"]


def test_normalize_jsearch_offer_marks_frontend_offer_relevant() -> None:
    normalized = normalize_jsearch_offer(_frontend_offer())

    assert normalized["id_offre"] == "jsearch-front"
    assert normalized["source"] == "JSearch"
    assert normalized["titre"] == "Frontend Developer WordPress"
    assert normalized["entreprise"] == "Studio Web"
    assert normalized["url_offre"] == "https://example.test/apply/jsearch-front"
    assert normalized["localisation"] == "Dijon, Bourgogne-Franche-Comte, FR"
    assert normalized["type_contrat"] == "FULLTIME"
    assert normalized["teletravail_mention"] in {"hybride", "100% teletravail"}
    assert normalized["date_publication"] == "2026-05-01T10:00:00.000Z"
    assert normalized["salaire_min"] == 35000
    assert normalized["salaire_max"] == 45000
    assert normalized["salaire_currency"] == "EUR"
    assert normalized["salaire_period"] == "YEAR"
    assert "WordPress" in normalized["matched_keywords"]
    assert normalized["is_relevant"] is True


def test_collect_adds_normalization_and_scoring_without_real_network() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [_frontend_offer()]})

    source = _source_with_transport(httpx.MockTransport(handler))
    result = source.collect()

    assert result.source_name == "JSearch"
    assert len(result.raw_offers) == 1
    assert len(result.normalized_offers) == 1
    assert result.stats.enabled is True
    assert result.stats.fetched == 1
    assert result.stats.kept == 1
    assert result.stats.filtered == 0
    assert isinstance(result.normalized_offers[0]["score_total"], int)
