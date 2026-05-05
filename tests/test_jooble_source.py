import httpx
import pytest

from autotache_jobs.sources.jooble import JoobleSource, JoobleSourceError, normalize_jooble_offer


def _source_with_transport(transport: httpx.MockTransport, **overrides) -> JoobleSource:
    values = {
        "api_key": "test-jooble-key",
        "base_url": "https://example.test/jooble",
        "http_client": httpx.Client(transport=transport),
    }
    values.update(overrides)
    return JoobleSource(**values)


def _frontend_offer(**overrides) -> dict:
    values = {
        "id": "jooble-front",
        "title": "Frontend Developer WordPress",
        "snippet": (
            "Build WordPress interfaces with Elementor, HTML, CSS and JavaScript. "
            "Remote work possible."
        ),
        "company": "Studio Web",
        "location": "Paris, France",
        "type": "CDI",
        "salary": "35000 euros - 45000 euros annuel",
        "updated": "2026-05-01T10:00:00Z",
        "link": "https://jooble.org/jdp/jooble-front",
    }
    values.update(overrides)
    return values


def test_collect_raw_offers_returns_jobs_from_mocked_response() -> None:
    seen_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, json={"jobs": [{"id": "A1"}, {"id": "A2"}]})

    source = _source_with_transport(httpx.MockTransport(handler), keywords=["frontend"])

    assert source.collect_raw_offers() == [{"id": "A1"}, {"id": "A2"}]
    assert seen_urls == ["https://example.test/jooble/test-jooble-key"]


def test_collect_raw_offers_uses_default_french_base_url() -> None:
    seen_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, json={"jobs": []})

    source = JoobleSource(
        api_key="test-jooble-key",
        keywords=["frontend"],
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    source.collect_raw_offers()

    assert seen_urls == ["https://fr.jooble.org/api/test-jooble-key"]


def test_collect_raw_offers_handles_empty_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"jobs": []})

    source = _source_with_transport(httpx.MockTransport(handler), keywords=["frontend"])

    assert source.collect_raw_offers() == []


def test_collect_raw_offers_raises_clear_error_on_http_error_without_exposing_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="API unavailable")

    source = _source_with_transport(httpx.MockTransport(handler), keywords=["frontend"])

    with pytest.raises(JoobleSourceError) as exc_info:
        source.collect_raw_offers()

    message = str(exc_info.value)
    assert "Erreur HTTP 500" in message
    assert "test-jooble-key" not in message


def test_collect_raw_offers_403_mentions_domain_without_full_html_or_key() -> None:
    html = "<html><body>Error 403 " + ("x" * 400) + "</body></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text=html)

    source = _source_with_transport(httpx.MockTransport(handler), keywords=["frontend"])

    with pytest.raises(JoobleSourceError) as exc_info:
        source.collect_raw_offers()

    message = str(exc_info.value)
    assert "Erreur HTTP 403" in message
    assert "domaine Jooble utilise" in message
    assert "test-jooble-key" not in message
    assert len(message) < 320


def test_collect_raw_offers_sends_keyword_and_location_without_real_network() -> None:
    seen_payloads = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_payloads.append(request.read().decode("utf-8"))
        return httpx.Response(200, json={"jobs": []})

    source = _source_with_transport(
        httpx.MockTransport(handler),
        keywords=["frontend"],
        location="Dijon",
    )

    source.collect_raw_offers()

    assert len(seen_payloads) == 1
    assert '"keywords":"frontend"' in seen_payloads[0]
    assert '"location":"Dijon"' in seen_payloads[0]


def test_collect_raw_offers_uses_api_key_without_exposing_it_in_errors() -> None:
    seen_paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        return httpx.Response(200, json={"jobs": []})

    source = _source_with_transport(httpx.MockTransport(handler), keywords=["frontend"])

    source.collect_raw_offers()

    assert seen_paths == ["/jooble/test-jooble-key"]


def test_collect_raw_offers_max_pages_limits_calls() -> None:
    seen_payloads = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_payloads.append(request.read().decode("utf-8"))
        return httpx.Response(200, json={"jobs": [{"id": str(len(seen_payloads))}]})

    source = _source_with_transport(httpx.MockTransport(handler), keywords=["frontend"], max_pages=2)

    assert source.collect_raw_offers() == [{"id": "1"}, {"id": "2"}]
    assert len(seen_payloads) == 2
    assert '"page":1' in seen_payloads[0]
    assert '"page":2' in seen_payloads[1]


def test_normalize_jooble_offer_marks_frontend_offer_relevant() -> None:
    normalized = normalize_jooble_offer(_frontend_offer())

    assert normalized["id_offre"] == "jooble-front"
    assert normalized["source"] == "Jooble"
    assert normalized["titre"] == "Frontend Developer WordPress"
    assert normalized["entreprise"] == "Studio Web"
    assert normalized["url_offre"] == "https://jooble.org/jdp/jooble-front"
    assert normalized["is_relevant"] is True
    assert "WordPress" in normalized["matched_keywords"]
    assert normalized["decision"] in {"Pertinent", "À vérifier"}


def test_normalize_jooble_offer_marks_non_relevant_offer_rejected() -> None:
    normalized = normalize_jooble_offer(
        {
            "id": "data-analyst",
            "title": "Data Analyst",
            "snippet": "SQL reporting and BI dashboards.",
            "company": "Data Corp",
            "link": "https://jooble.org/jdp/data-analyst",
        }
    )

    assert normalized["source"] == "Jooble"
    assert normalized["is_relevant"] is False
    assert "data analyst" in normalized["excluded_by"]
    assert normalized["decision"].startswith("Rejet")


def test_normalize_jooble_offer_extracts_technologies_from_title_and_description() -> None:
    normalized = normalize_jooble_offer(
        _frontend_offer(
            title="UI Designer",
            snippet="Create Figma mockups and HTML CSS JavaScript React interfaces.",
        )
    )

    assert normalized["technologies"] == ["HTML", "CSS", "JavaScript", "React", "Figma", "UI"]


def test_normalize_jooble_offer_extracts_salary_when_present() -> None:
    normalized = normalize_jooble_offer(_frontend_offer(salary="32000 euros - 42000 euros annuel"))

    assert normalized["salaire_brut"] == "32000 euros - 42000 euros annuel"
    assert normalized["salaire_min"] == 32000
    assert normalized["salaire_max"] == 42000
    assert normalized["salaire_moyen"] == 37000
    assert normalized["salaire_type"] == "annuel"


def test_collect_adds_normalization_and_scoring_without_real_network() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"jobs": [_frontend_offer()]})

    source = _source_with_transport(httpx.MockTransport(handler), keywords=["frontend"])
    result = source.collect()

    assert result.source_name == "Jooble"
    assert len(result.raw_offers) == 1
    assert len(result.normalized_offers) == 1
    assert result.stats.enabled is True
    assert result.stats.fetched == 1
    assert result.stats.kept == 1
    assert result.stats.filtered == 0
    assert result.normalized_offers[0]["source"] == "Jooble"
    assert isinstance(result.normalized_offers[0]["score_total"], int)
    assert result.normalized_offers[0]["score_reason"]
    assert isinstance(result.normalized_offers[0]["score_details"], dict)
