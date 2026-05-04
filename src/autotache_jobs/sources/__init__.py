"""Job offer sources used by AutoTache."""

from .base import JobSource, SourceResult
from .france_travail import FranceTravailSource

__all__ = ["FranceTravailSource", "JobSource", "SourceResult"]
