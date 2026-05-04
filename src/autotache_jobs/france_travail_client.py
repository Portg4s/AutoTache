"""Isolated France Travail API client."""

from __future__ import annotations

import time
from typing import Any

import httpx


class FranceTravailClientError(RuntimeError):
    """Raised when the France Travail client receives an invalid or failed response."""


class FranceTravailClient:
    """Small client for France Travail OAuth and offer search endpoints."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scope: str,
        token_url: str,
        api_base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay_seconds: float = 3.0,
        http_client: httpx.Client | None = None,
        sleep_func: Any = time.sleep,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.token_url = token_url
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self._http_client = http_client or httpx.Client(timeout=timeout)
        self._cached_authorization: str | None = None
        self._sleep_func = sleep_func

    def get_access_token(self) -> str:
        """Return a cached Authorization header value, requesting one if needed."""

        if self._cached_authorization:
            return self._cached_authorization

        response = self._http_client.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": self.scope,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self._raise_for_status(response, "authentification France Travail")

        data = self._json(response, "authentification France Travail")
        access_token = data.get("access_token")
        token_type = data.get("token_type", "Bearer")
        if not access_token:
            raise FranceTravailClientError(
                "Reponse d'authentification France Travail invalide: access_token absent."
            )

        self._cached_authorization = f"{token_type} {access_token}".strip()
        return self._cached_authorization

    def search_offers(
        self,
        keyword: str,
        commune: str | None = None,
        distance: int | None = None,
        type_contrat: str | None = None,
        min_creation_date: str | None = None,
        max_creation_date: str | None = None,
        range_value: str = "0-149",
    ) -> list[dict]:
        """Search France Travail offers for one keyword and optional filters."""

        params: dict[str, str | int] = {
            "motsCles": keyword,
            "range": range_value,
        }
        if commune:
            params["commune"] = commune
        if distance is not None:
            params["distance"] = distance
        if type_contrat:
            params["typeContrat"] = type_contrat
        if min_creation_date:
            params["minCreationDate"] = min_creation_date
        if max_creation_date:
            params["maxCreationDate"] = max_creation_date

        response = self._get_with_rate_limit_retry(
            f"{self.api_base_url}/offres/search",
            params=params,
            headers={"Authorization": self.get_access_token()},
            context="recherche d'offres France Travail",
        )
        self._raise_for_status(response, "recherche d'offres France Travail")

        if response.status_code == 204 or not response.text.strip():
            return []

        data = self._search_json(response, "recherche d'offres France Travail")
        results = data.get("resultats", [])
        if not isinstance(results, list):
            return []
        return results

    def _get_with_rate_limit_retry(
        self,
        url: str,
        params: dict[str, str | int],
        headers: dict[str, str],
        context: str,
    ) -> httpx.Response:
        for attempt in range(self.max_retries + 1):
            response = self._http_client.get(url, params=params, headers=headers)
            if response.status_code != 429:
                return response

            if attempt >= self.max_retries:
                raise self._rate_limit_error(response, context)

            self._sleep_func(self._retry_delay(response))

        return response

    @staticmethod
    def _json(response: httpx.Response, context: str) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError as exc:
            raise FranceTravailClientError(f"Reponse JSON invalide pendant {context}.") from exc

        if not isinstance(data, dict):
            raise FranceTravailClientError(f"Reponse inattendue pendant {context}: objet JSON attendu.")
        return data

    @staticmethod
    def _search_json(response: httpx.Response, context: str) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError as exc:
            content_type = response.headers.get("Content-Type", "non specifie")
            body_preview = response.text.strip().replace("\n", " ")[:300]
            raise FranceTravailClientError(
                f"Reponse non JSON pendant {context}: "
                f"status={response.status_code}, content-type={content_type}, "
                f"body={body_preview or 'vide'}"
            ) from exc

        if not isinstance(data, dict):
            raise FranceTravailClientError(f"Reponse inattendue pendant {context}: objet JSON attendu.")
        return data

    @staticmethod
    def _raise_for_status(response: httpx.Response, context: str) -> None:
        if response.status_code < 400:
            return

        message = response.text.strip().replace("\n", " ")[:300]
        raise FranceTravailClientError(
            f"Erreur HTTP {response.status_code} pendant {context}: {message or 'aucun detail'}"
        )

    def _retry_delay(self, response: httpx.Response) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(float(retry_after), 0)
            except ValueError:
                return self.retry_delay_seconds
        return self.retry_delay_seconds

    @staticmethod
    def _rate_limit_error(response: httpx.Response, context: str) -> FranceTravailClientError:
        message = response.text.strip().replace("\n", " ")[:300]
        return FranceTravailClientError(
            f"Erreur HTTP 429 pendant {context}: l'API France Travail limite les requetes. "
            f"Reessayez plus tard ou augmentez api.request_delay_seconds. "
            f"Detail: {message or 'aucun detail'}"
        )
