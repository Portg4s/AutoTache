"""Job offer sources used by AutoTache."""

from .adzuna import AdzunaSource, AdzunaSourceError, normalize_adzuna_offer
from .arbeitnow import ArbeitnowSource, ArbeitnowSourceError, normalize_arbeitnow_offer
from .base import JobSource, SourceResult
from .france_travail import FranceTravailSource
from .jooble import JoobleSource, JoobleSourceError, normalize_jooble_offer
from .remotive import RemotiveSource, RemotiveSourceError, normalize_remotive_offer

__all__ = [
    "AdzunaSource",
    "AdzunaSourceError",
    "ArbeitnowSource",
    "ArbeitnowSourceError",
    "FranceTravailSource",
    "JobSource",
    "JoobleSource",
    "JoobleSourceError",
    "RemotiveSource",
    "RemotiveSourceError",
    "SourceResult",
    "normalize_adzuna_offer",
    "normalize_arbeitnow_offer",
    "normalize_jooble_offer",
    "normalize_remotive_offer",
]
