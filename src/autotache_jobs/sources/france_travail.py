"""France Travail offer source."""

from __future__ import annotations

from datetime import datetime, timedelta
import time
from typing import Any

from ..normalizer import normalize_france_travail_offer
from .base import JobSource, SourceResult, SourceStats


class FranceTravailSource(JobSource):
    """Collect and normalize offers from the France Travail API client."""

    name = "France Travail"

    def __init__(self, config: Any, client: Any, sleep_func: Any = time.sleep) -> None:
        self.config = config
        self.client = client
        self.sleep_func = sleep_func

    def collect(self) -> SourceResult:
        raw_offers = self.collect_raw_offers()
        normalized_offers = [
            normalize_france_travail_offer(
                raw_offer,
                allow_stage=self.config.allow_internship,
                allow_alternance=self.config.allow_apprenticeship,
            )
            for raw_offer in raw_offers
        ]
        return SourceResult(
            source_name=self.name,
            raw_offers=raw_offers,
            normalized_offers=normalized_offers,
            stats=SourceStats(
                enabled=True,
                fetched=len(raw_offers),
                kept=len(raw_offers),
                filtered=0,
            ),
        )

    def collect_raw_offers(self) -> list[dict]:
        raw_offers: list[dict] = []
        min_creation_date, max_creation_date = _creation_date_range(self.config.days_back)
        is_first_call = True

        for keyword in self.config.keywords:
            for commune in self.config.communes:
                for contract_type in self.config.contract_types:
                    if not is_first_call and self.config.api.request_delay_seconds > 0:
                        self.sleep_func(self.config.api.request_delay_seconds)
                    is_first_call = False
                    results = self.client.search_offers(
                        keyword=keyword,
                        commune=commune,
                        distance=self.config.distance_km,
                        type_contrat=contract_type,
                        min_creation_date=min_creation_date,
                        max_creation_date=max_creation_date,
                    )
                    raw_offers.extend(results or [])

        return raw_offers


def _creation_date_range(days_back: int) -> tuple[str, str]:
    now = datetime.now()
    min_creation_date = (now - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00Z")
    max_creation_date = now.strftime("%Y-%m-%dT23:59:59Z")
    return min_creation_date, max_creation_date
