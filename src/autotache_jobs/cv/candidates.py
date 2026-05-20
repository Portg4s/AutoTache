"""Candidate offer selection for targeted CV drafts."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autotache_jobs.cv.offer_reader import read_all_offers_from_xlsx


DEFAULT_DECISIONS = {"pertinent", "a verifier"}


@dataclass(frozen=True)
class CvCandidate:
    row: int
    decision: str
    score: float
    source: str
    entreprise: str
    titre: str
    localisation: str
    offer: dict[str, Any]


def list_candidates(
    xlsx_path: str | Path,
    *,
    limit: int | None = 10,
    include_rejected: bool = False,
) -> list[CvCandidate]:
    candidates = [
        _candidate_from_offer(offer)
        for offer in read_all_offers_from_xlsx(xlsx_path)
        if include_rejected or _normalize_decision(offer.get("decision")) in DEFAULT_DECISIONS
    ]
    candidates.sort(key=_sort_key)
    if limit is None:
        return candidates
    return candidates[:limit]


def select_top_candidate(xlsx_path: str | Path, top: int = 1) -> CvCandidate:
    if top < 1:
        raise ValueError("--top doit etre superieur ou egal a 1.")
    candidates = list_candidates(xlsx_path, limit=top, include_rejected=False)
    if len(candidates) < top:
        raise ValueError(f"Aucune offre candidate trouvee pour --top {top}.")
    return candidates[top - 1]


def _candidate_from_offer(offer: dict[str, Any]) -> CvCandidate:
    return CvCandidate(
        row=int(offer["row"]),
        decision=str(offer.get("decision") or ""),
        score=_score_value(offer.get("score_total")),
        source=str(offer.get("source") or ""),
        entreprise=str(offer.get("entreprise") or ""),
        titre=str(offer.get("titre") or ""),
        localisation=str(offer.get("localisation") or ""),
        offer=offer,
    )


def _sort_key(candidate: CvCandidate) -> tuple[int, float]:
    ranks = {"pertinent": 0, "a verifier": 1}
    rank = ranks.get(_normalize_decision(candidate.decision), 2)
    return (rank, -candidate.score)


def _score_value(value: Any) -> float:
    if value in (None, ""):
        return 0
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return 0


def _normalize_decision(value: Any) -> str:
    text = str(value or "").strip()
    if "Ã" in text:
        try:
            text = text.encode("latin1").decode("utf-8")
        except UnicodeError:
            pass
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    if "verifier" in text:
        return "a verifier"
    if "pertinent" in text:
        return "pertinent"
    if "rejet" in text:
        return "rejete"
    return text
