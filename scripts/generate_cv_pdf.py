from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotache_jobs.cv.candidates import select_top_candidate
from autotache_jobs.cv.offer_reader import read_offer_from_xlsx
from autotache_jobs.cv.pdf_generator import generate_cv_pdf
from autotache_jobs.cv.profile import load_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Generer un CV recruiter au format PDF.")
    parser.add_argument("--debug-xlsx", required=True, help="Chemin du fichier exports/debug/debug_offres_*.xlsx")
    parser.add_argument("--profile", default="profile/profil_maitre.yaml", help="Profil YAML a utiliser.")
    parser.add_argument("--row", type=int, help="Ligne Excel reelle a utiliser.")
    parser.add_argument("--top", type=int, help="Rang de la meilleure offre candidate a utiliser.")
    parser.add_argument("--keep-html", action="store_true", help="Conserver le HTML de previsualisation.")
    args = parser.parse_args()

    if args.row is None and args.top is None:
        parser.error("Indiquer --row ou --top.")
    if args.row is not None and args.top is not None:
        parser.error("Indiquer --row ou --top, pas les deux.")

    try:
        profile = load_profile(args.profile)
        if args.top is not None:
            offer = select_top_candidate(args.debug_xlsx, top=args.top).offer
        else:
            offer = read_offer_from_xlsx(args.debug_xlsx, args.row)

        output_path = generate_cv_pdf(offer=offer, profile=profile, keep_html=args.keep_html)
    except ValueError as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 2

    print(output_path)
    if args.keep_html:
        print(output_path.with_suffix(".html"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
