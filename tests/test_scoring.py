from autotache_jobs.scoring import score_offer


def test_wordpress_developer_is_relevant_with_high_score() -> None:
    result = score_offer(
        {
            "titre": "Developpeur WordPress",
            "description": "Creation de sites WordPress avec Elementor et WooCommerce.",
            "technologies": ["WordPress", "Elementor", "WooCommerce", "HTML", "CSS"],
            "type_contrat": "CDI",
        }
    )

    assert result["decision"] == "Pertinent"
    assert result["score_total"] >= 80


def test_frontend_integrator_is_relevant_or_close_to_relevant() -> None:
    result = score_offer(
        {
            "titre": "Integrateur front-end",
            "description": "Integration responsive en HTML CSS JavaScript.",
            "technologies": ["HTML", "CSS", "JavaScript"],
            "type_contrat": "CDD",
        }
    )

    assert result["decision"] in {"Pertinent", "À vérifier"}
    assert result["score_total"] >= 70


def test_ui_ux_designer_figma_is_relevant() -> None:
    result = score_offer(
        {
            "titre": "UI/UX designer",
            "description": "Conception interface, maquettes et design system.",
            "technologies": ["Figma"],
            "type_contrat": "CDI",
        }
    )

    assert result["decision"] == "Pertinent"


def test_web_graphic_designer_digital_is_relevant_or_review() -> None:
    result = score_offer(
        {
            "titre": "Graphiste web",
            "description": "Creation digitale, maquettes web et supports responsive.",
            "technologies": ["Photoshop", "Illustrator"],
        }
    )

    assert result["decision"] in {"Pertinent", "À vérifier"}
    assert result["score_total"] >= 45


def test_it_project_manager_with_web_signals_is_not_relevant() -> None:
    result = score_offer(
        {
            "titre": "Chef de projet IT Web",
            "description": "Coordination projet avec notions HTML CSS Bootstrap.",
            "technologies": ["HTML", "CSS", "Bootstrap"],
        }
    )

    assert result["decision"] in {"À vérifier", "Rejeté"}


def test_devops_lead_is_rejected() -> None:
    result = score_offer(
        {
            "titre": "Tech Lead DevOps",
            "description": "Infrastructure, CI/CD, cloud et TypeScript.",
        }
    )

    assert result["decision"] == "Rejeté"
    assert result["score_details"]["eliminatory_reason"] == "devops pur"


def test_apprenticeship_javascript_developer_is_rejected() -> None:
    result = score_offer(
        {
            "titre": "Alternance developpeur JavaScript",
            "description": "Developpement web frontend.",
        }
    )

    assert result["decision"] == "Rejeté"
    assert result["score_details"]["eliminatory_reason"] == "alternance"


def test_internship_webdesigner_is_rejected() -> None:
    result = score_offer(
        {
            "titre": "Stage webdesigner",
            "description": "Maquettes Figma et design web.",
        }
    )

    assert result["decision"] == "Rejeté"
    assert result["score_details"]["eliminatory_reason"] == "stage"


def test_backend_only_node_python_is_rejected() -> None:
    result = score_offer(
        {
            "titre": "Developpeur backend",
            "description": "API Node Python Django, architecture serveur.",
            "technologies": ["Node", "Python", "Django"],
        }
    )

    assert result["decision"] == "Rejeté"
    assert result["score_details"]["eliminatory_reason"] == "backend pur"


def test_data_analyst_is_rejected() -> None:
    result = score_offer({"titre": "Data analyst", "description": "Reporting BI et SQL."})

    assert result["decision"] == "Rejeté"
    assert result["score_details"]["eliminatory_reason"] == "data pur"


def test_it_support_is_rejected() -> None:
    result = score_offer({"titre": "Support informatique", "description": "Helpdesk utilisateurs."})

    assert result["decision"] == "Rejeté"
    assert result["score_details"]["eliminatory_reason"] == "support informatique pur"


def test_empty_offer_is_rejected_without_error() -> None:
    result = score_offer({})

    assert result["decision"] == "Rejeté"
    assert result["score_total"] == 0
    assert result["score_reason"]


def test_remote_offer_gets_points() -> None:
    without_remote = score_offer({"titre": "Developpeur WordPress", "technologies": ["WordPress"]})
    with_remote = score_offer(
        {
            "titre": "Developpeur WordPress",
            "technologies": ["WordPress"],
            "teletravail_mention": "Teletravail partiel",
            "teletravail_jours": 2,
        }
    )

    assert with_remote["score_details"]["teletravail"]["score"] == 10
    assert with_remote["score_total"] > without_remote["score_total"]


def test_dijon_or_21_location_gets_points() -> None:
    result = score_offer(
        {
            "titre": "Webdesigner",
            "technologies": ["Figma"],
            "localisation": "Dijon 21000",
        }
    )

    assert result["score_details"]["localisation"]["score"] == 10


def test_cdi_or_cdd_contract_gets_points() -> None:
    result = score_offer(
        {
            "titre": "Integrateur web",
            "technologies": ["HTML", "CSS"],
            "type_contrat": "CDI",
        }
    )

    assert result["score_details"]["contrat"]["score"] == 5
