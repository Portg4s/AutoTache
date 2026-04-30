from autotache_jobs.parsers import extract_technologies, parse_salary, parse_teletravail


def test_parse_teletravail_full_remote_percent() -> None:
    result = parse_teletravail("Poste en 100% télétravail possible.")

    assert result == {"teletravail_mention": "100% teletravail", "teletravail_jours": 5}


def test_parse_teletravail_full_remote_english() -> None:
    result = parse_teletravail("Frontend developer en full remote.")

    assert result["teletravail_mention"] == "100% teletravail"
    assert result["teletravail_jours"] == 5


def test_parse_teletravail_two_days_per_week() -> None:
    result = parse_teletravail("Télétravail 2 jours par semaine après intégration.")

    assert result == {"teletravail_mention": "teletravail partiel", "teletravail_jours": 2}


def test_parse_teletravail_up_to_three_days() -> None:
    result = parse_teletravail("Jusqu’à 3 jours de télétravail selon le planning.")

    assert result == {"teletravail_mention": "teletravail partiel", "teletravail_jours": 3}


def test_parse_teletravail_hybrid() -> None:
    result = parse_teletravail("Organisation hybride avec présence équipe produit.")

    assert result == {"teletravail_mention": "hybride", "teletravail_jours": None}


def test_parse_teletravail_presentiel_only() -> None:
    result = parse_teletravail("Poste en présentiel uniquement.")

    assert result == {"teletravail_mention": "presentiel uniquement", "teletravail_jours": 0}


def test_parse_teletravail_absent() -> None:
    result = parse_teletravail("Agence web recherche intégrateur WordPress.")

    assert result == {"teletravail_mention": None, "teletravail_jours": None}


def test_parse_salary_annual_euros_range() -> None:
    result = parse_salary("Annuel de 35000 Euros à 42000 Euros selon profil.")

    assert result["salaire_min"] == 35000
    assert result["salaire_max"] == 42000
    assert result["salaire_moyen"] == 38500
    assert result["salaire_type"] == "annuel"


def test_parse_salary_k_range() -> None:
    result = parse_salary("Salaire 35k à 45k selon expérience.")

    assert result["salaire_min"] == 35000
    assert result["salaire_max"] == 45000
    assert result["salaire_type"] == "annuel"


def test_parse_salary_spaced_euro_range() -> None:
    result = parse_salary("Rémunération 35 000 € - 45 000 €.")

    assert result["salaire_min"] == 35000
    assert result["salaire_max"] == 45000
    assert result["salaire_moyen"] == 40000


def test_parse_salary_monthly_gross() -> None:
    result = parse_salary("Salaire proposé : 2500 € brut mensuel.")

    assert result["salaire_min"] == 2500
    assert result["salaire_max"] is None
    assert result["salaire_type"] == "mensuel"
    assert result["salaire_brut"] is True


def test_parse_salary_absent() -> None:
    result = parse_salary("Rémunération selon profil.")

    assert result == {
        "salaire_min": None,
        "salaire_max": None,
        "salaire_moyen": None,
        "salaire_type": None,
        "salaire_brut": False,
    }


def test_extract_technologies_normalizes_and_deduplicates() -> None:
    result = extract_technologies(
        "WordPress, wordpress, WooCommerce, Vue.js, JS, TypeScript, Tailwind CSS et Figma."
    )

    assert result == [
        "WordPress",
        "WooCommerce",
        "CSS",
        "JavaScript",
        "TypeScript",
        "Vue.js",
        "Tailwind",
        "Figma",
    ]


def test_extract_technologies_design_terms() -> None:
    result = extract_technologies("Profil UI/UX avec Photoshop, Illustrator et sens interface utilisateur.")

    assert result == ["Photoshop", "Illustrator", "UI", "UX"]


def test_extract_technologies_absent() -> None:
    result = extract_technologies("Poste orienté relation client et coordination.")

    assert result == []
