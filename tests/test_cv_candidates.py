from pathlib import Path

from openpyxl import Workbook

from autotache_jobs.cv.candidates import list_candidates


def test_filters_and_sorts_candidates_keeping_excel_row(tmp_path: Path) -> None:
    xlsx_path = tmp_path / "debug.xlsx"
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["source", "titre", "entreprise", "localisation", "decision", "score_total"])
    worksheet.append(["A", "Rejected", "Nope", "Paris", "Rejeté", 99])
    worksheet.append(["B", "Review high", "Beta", "Dijon", "À vérifier", 91])
    worksheet.append(["C", "Relevant low", "Gamma", "Lyon", "Pertinent", 70])
    worksheet.append(["D", "Relevant high", "Delta", "Beaune", "Pertinent", 88])
    workbook.save(xlsx_path)

    candidates = list_candidates(xlsx_path)

    assert [candidate.row for candidate in candidates] == [5, 4, 3]
    assert [candidate.titre for candidate in candidates] == ["Relevant high", "Relevant low", "Review high"]
    assert all(candidate.decision != "Rejeté" for candidate in candidates)


def test_include_rejected_keeps_rejected_rows(tmp_path: Path) -> None:
    xlsx_path = tmp_path / "debug.xlsx"
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["titre", "decision", "score_total"])
    worksheet.append(["Rejected", "Rejeté", 99])
    workbook.save(xlsx_path)

    candidates = list_candidates(xlsx_path, include_rejected=True)

    assert candidates[0].row == 2
    assert candidates[0].decision == "Rejeté"

