from autotache_jobs.normalizer import normalize_france_travail_offer


def test_complete_wordpress_offer_is_normalized_and_relevant() -> None:
    normalized = normalize_france_travail_offer(
        {
            "id": "123ABC",
            "intitule": "Developpeur WordPress",
            "description": "Creation de themes WordPress avec Elementor. Teletravail 2 jours par semaine.",
            "entreprise": {"nom": "Agence Web"},
            "lieuTravail": {"libelle": "Paris 11e", "codePostal": "75011"},
            "typeContratLibelle": "CDI",
            "experienceLibelle": "2 ans",
            "salaire": {"libelle": "Annuel de 35000 Euros a 42000 Euros"},
            "dateCreation": "2026-04-20T10:00:00.000Z",
            "dateActualisation": "2026-04-21T12:00:00.000Z",
        }
    )

    assert normalized["id_offre"] == "123ABC"
    assert normalized["source"] == "France Travail"
    assert normalized["entreprise"] == "Agence Web"
    assert normalized["salaire_min"] == 35000
    assert normalized["salaire_max"] == 42000
    assert normalized["teletravail_jours"] == 2
    assert normalized["is_relevant"] is True
    assert "WordPress" in normalized["technologies"]


def test_missing_company_does_not_crash() -> None:
    normalized = normalize_france_travail_offer(
        {
            "id": "NO-COMPANY",
            "intitule": "Integrateur front-end",
            "description": "Integration HTML CSS JavaScript.",
        }
    )

    assert normalized["entreprise"] == "Non specifie"
    assert normalized["is_relevant"] is True


def test_missing_salary_does_not_crash() -> None:
    normalized = normalize_france_travail_offer(
        {
            "id": "NO-SALARY",
            "intitule": "Webdesigner",
            "description": "Creation de maquettes Figma pour sites web.",
        }
    )

    assert normalized["salaire_brut"] == ""
    assert normalized["salaire_min"] is None
    assert normalized["salaire_max"] is None


def test_backend_only_is_normalized_but_not_relevant() -> None:
    normalized = normalize_france_travail_offer(
        {
            "id": "BACKEND",
            "intitule": "Developpeur backend",
            "description": "Developpement Symfony, API REST et bases de donnees.",
            "typeContrat": "CDI",
        }
    )

    assert normalized["titre"] == "Developpeur backend"
    assert normalized["is_relevant"] is False
    assert "backend pur" in normalized["excluded_by"]


def test_stage_is_rejected_by_default() -> None:
    normalized = normalize_france_travail_offer(
        {
            "id": "STAGE",
            "intitule": "Stage integrateur web",
            "description": "Stage WordPress et HTML CSS.",
            "typeContratLibelle": "Stage",
        }
    )

    assert normalized["is_relevant"] is False
    assert "stage" in normalized["excluded_by"]


def test_stage_is_accepted_when_allowed() -> None:
    normalized = normalize_france_travail_offer(
        {
            "id": "STAGE-OK",
            "intitule": "Stage integrateur web",
            "description": "Stage WordPress et HTML CSS.",
            "typeContratLibelle": "Stage",
        },
        allow_stage=True,
    )

    assert normalized["is_relevant"] is True
    assert "stage" not in normalized["excluded_by"]


def test_technologies_are_extracted_from_description_and_competences() -> None:
    normalized = normalize_france_travail_offer(
        {
            "id": "TECH",
            "intitule": "Developpeur front-end",
            "description": "Interface React avec Tailwind.",
            "competences": [
                {"libelle": "Vue.js"},
                {"libelle": "Figma"},
                {"libelle": "JavaScript"},
            ],
        }
    )

    assert normalized["technologies"] == ["JavaScript", "React", "Vue.js", "Tailwind", "Figma"]


def test_france_travail_url_is_built_from_offer_id() -> None:
    normalized = normalize_france_travail_offer(
        {
            "id": "987XYZ",
            "intitule": "UI designer",
            "description": "Design UI sur Figma.",
        }
    )

    assert normalized["url_offre"] == "https://candidat.francetravail.fr/offres/recherche/detail/987XYZ"
