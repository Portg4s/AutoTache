"""Job offer sources used by AutoTache."""

from .arbeitnow import ArbeitnowSource, ArbeitnowSourceError, normalize_arbeitnow_offer
from .base import JobSource, SourceResult
from .france_travail import FranceTravailSource

__all__ = [
    "ArbeitnowSource",
    "ArbeitnowSourceError",
    "FranceTravailSource",
    "JobSource",
    "SourceResult",
    "normalize_arbeitnow_offer",
]
