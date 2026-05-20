from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotache_jobs.cv.candidates import list_candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Lister les meilleures offres candidates CV depuis un debug xlsx.")
    parser.add_argument("--debug-xlsx", required=True, help="Chemin du fichier exports/debug/debug_offres_*.xlsx")
    parser.add_argument("--limit", type=int, default=10, help="Nombre maximum de lignes affichees.")
    parser.add_argument("--include-rejected", action="store_true", help="Inclure aussi les offres Rejete.")
    args = parser.parse_args()

    candidates = list_candidates(args.debug_xlsx, limit=args.limit, include_rejected=args.include_rejected)
    print("row | decision | score | source | entreprise | titre | localisation")
    print("-" * 78)
    for candidate in candidates:
        print(
            " | ".join(
                [
                    str(candidate.row),
                    candidate.decision,
                    _format_score(candidate.score),
                    candidate.source,
                    candidate.entreprise,
                    candidate.titre,
                    candidate.localisation,
                ]
            )
        )
    return 0


def _format_score(score: float) -> str:
    return str(int(score)) if score.is_integer() else f"{score:.1f}"


if __name__ == "__main__":
    raise SystemExit(main())

