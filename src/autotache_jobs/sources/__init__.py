"""Job offer sources used by AutoTache."""

from .arbeitnow import ArbeitnowSource, ArbeitnowSourceError, normalize_arbeitnow_offer
from .base import JobSource, SourceResult
from .france_travail import FranceTravailSource
from .remotive import RemotiveSource, RemotiveSourceError, normalize_remotive_offer

__all__ = [
    "ArbeitnowSource",
    "ArbeitnowSourceError",
    "FranceTravailSource",
    "JobSource",
    "RemotiveSource",
    "RemotiveSourceError",
    "SourceResult",
    "normalize_arbeitnow_offer",
    "normalize_remotive_offer",
]
