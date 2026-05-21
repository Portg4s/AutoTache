from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotache_jobs.cv.candidates import select_top_candidate
from autotache_jobs.cv.docx_generator import generate_cv_docx
from autotache_jobs.cv.generator import draft_summary
from autotache_jobs.cv.matcher import match_offer_to_profile
from autotache_jobs.cv.offer_reader import read_offer_from_xlsx
from autotache_jobs.cv.profile import load_profile
from autotache_jobs.cv.template_docx_generator import generate_cv_docx_from_template


def main() -> int:
    parser = argparse.ArgumentParser(description="Generer un CV cible au format DOCX.")
    parser.add_argument("--debug-xlsx", required=True, help="Chemin du fichier exports/debug/debug_offres_*.xlsx")
    parser.add_argument("--profile", default="profile/profil_maitre.yaml", help="Profil YAML a utiliser.")
    parser.add_argument("--row", type=int, help="Ligne Excel reelle a utiliser.")
    parser.add_argument("--top", type=int, help="Rang de la meilleure offre candidate a utiliser.")
    parser.add_argument("--mode", choices=["draft", "recruiter"], default="draft", help="Type de rendu a generer.")
    parser.add_argument("--template", help="Template DOCX docxtpl a utiliser pour le mode recruiter.")
    args = parser.parse_args()

    if args.row is None and args.top is None:
        parser.error("Indiquer --row ou --top.")
    if args.row is not None and args.top is not None:
        parser.error("Indiquer --row ou --top, pas les deux.")
    if args.template and args.mode != "recruiter":
        parser.error("--template est reserve au mode recruiter.")

    try:
        profile = load_profile(args.profile)
        if args.top is not None:
            offer = select_top_candidate(args.debug_xlsx, top=args.top).offer
        elif args.row is not None:
            offer = read_offer_from_xlsx(args.debug_xlsx, args.row)

        if args.template:
            output_path = generate_cv_docx_from_template(
                offer=offer,
                profile=profile,
                template_path=args.template,
            )
        else:
            output_path = generate_cv_docx(offer=offer, profile=profile, mode=args.mode)
        match = match_offer_to_profile(offer, profile)
    except ValueError as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 2

    print(output_path)
    print(draft_summary(offer, match))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
