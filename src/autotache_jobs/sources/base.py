"""Base interfaces for job offer sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceStats:
    """Collection stats for one offer source."""

    enabled: bool
    fetched: int
    kept: int
    filtered: int


@dataclass(frozen=True)
class SourceResult:
    """Offers collected from one source before and after normalization."""

    source_name: str
    raw_offers: list[dict]
    normalized_offers: list[dict]
    stats: SourceStats


class JobSource(ABC):
    """Collect and normalize offers from one provider."""

    name: str

    @abstractmethod
    def collect(self) -> SourceResult:
        """Return raw and normalized offers for this source."""
