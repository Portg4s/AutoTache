import httpx
import pytest

from autotache_jobs.france_travail_client import FranceTravailClient, FranceTravailClientError


def _client_with_transport(transport: httpx.MockTransport) -> FranceTravailClient:
    return FranceTravailClient(
        client_id="fake-client-id",
        client_secret="fake-client-secret",
        scope="fake-scope",
        token_url="https://example.test/token",
        api_base_url="https://example.test/api",
        http_client=httpx.Client(transport=transport),
    )


def test_get_access_token_returns_formatted_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"access_token": "abc123", "token_type": "Bearer"})

    client = _client_with_transport(httpx.MockTransport(handler))

    assert client.get_access_token() == "Bearer abc123"


def test_get_access_token_uses_memory_cache() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"access_token": "cached", "token_type": "Bearer"})

    client = _client_with_transport(httpx.MockTransport(handler))

    assert client.get_access_token() == "Bearer cached"
    assert client.get_access_token() == "Bearer cached"
    assert calls == 1


def test_get_access_token_raises_when_access_token_is_missing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"token_type": "Bearer"})

    client = _client_with_transport(httpx.MockTransport(handler))

    with pytest.raises(FranceTravailClientError, match="access_token absent"):
        client.get_access_token()


def test_search_offers_calls_expected_endpoint() -> None:
    seen_paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "abc123", "token_type": "Bearer"})
        return httpx.Response(200, json={"resultats": [{"id": "A1"}]})

    client = _client_with_transport(httpx.MockTransport(handler))

    client.search_offers("wordpress")

    assert seen_paths == ["/token", "/api/offres/search"]


def test_search_offers_sends_expected_query_params() -> None:
    captured_query: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_query
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "abc123", "token_type": "Bearer"})
        captured_query = dict(request.url.params)
        return httpx.Response(200, json={"resultats": []})

    client = _client_with_transport(httpx.MockTransport(handler))

    client.search_offers(
        keyword="front-end",
        commune="75056",
        distance=20,
        type_contrat="CDI",
        min_creation_date="2026-04-01T00:00:00Z",
        range_value="0-49",
    )

    assert captured_query == {
        "motsCles": "front-end",
        "commune": "75056",
        "distance": "20",
        "typeContrat": "CDI",
        "minCreationDate": "2026-04-01T00:00:00Z",
        "range": "0-49",
    }


def test_search_offers_sends_authorization_header() -> None:
    authorization_headers = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "abc123", "token_type": "Bearer"})
        authorization_headers.append(request.headers.get("Authorization"))
        return httpx.Response(200, json={"resultats": []})

    client = _client_with_transport(httpx.MockTransport(handler))

    client.search_offers("wordpress")

    assert authorization_headers == ["Bearer abc123"]


def test_search_offers_returns_resultats() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "abc123", "token_type": "Bearer"})
        return httpx.Response(200, json={"resultats": [{"id": "A1"}, {"id": "B2"}]})

    client = _client_with_transport(httpx.MockTransport(handler))

    assert client.search_offers("wordpress") == [{"id": "A1"}, {"id": "B2"}]


def test_search_offers_returns_empty_list_when_resultats_missing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "abc123", "token_type": "Bearer"})
        return httpx.Response(200, json={"unexpected": []})

    client = _client_with_transport(httpx.MockTransport(handler))

    assert client.search_offers("wordpress") == []


@pytest.mark.parametrize("status_code", [401, 500])
def test_search_offers_raises_clear_error_on_http_error(status_code: int) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "abc123", "token_type": "Bearer"})
        return httpx.Response(status_code, text="Erreur API simulee")

    client = _client_with_transport(httpx.MockTransport(handler))

    with pytest.raises(FranceTravailClientError, match=f"Erreur HTTP {status_code}"):
        client.search_offers("wordpress")
