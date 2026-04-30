"""Isolated France Travail API client."""

from __future__ import annotations

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
        http_client: httpx.Client | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.token_url = token_url
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout = timeout
        self._http_client = http_client or httpx.Client(timeout=timeout)
        self._cached_authorization: str | None = None

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

        response = self._http_client.get(
            f"{self.api_base_url}/offres/search",
            params=params,
            headers={"Authorization": self.get_access_token()},
        )
        self._raise_for_status(response, "recherche d'offres France Travail")

        data = self._json(response, "recherche d'offres France Travail")
        results = data.get("resultats", [])
        if not isinstance(results, list):
            return []
        return results

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
    def _raise_for_status(response: httpx.Response, context: str) -> None:
        if response.status_code < 400:
            return

        message = response.text.strip().replace("\n", " ")[:300]
        raise FranceTravailClientError(
            f"Erreur HTTP {response.status_code} pendant {context}: {message or 'aucun detail'}"
        )
