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
    assert result["score_details"]["eliminatory_reason"] is None
    assert "devops" in result["score_details"]["penalties"]["matches"]


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
    assert result["score_details"]["eliminatory_reason"] is None
    assert "backend pur" in result["score_details"]["penalties"]["matches"]


def test_data_analyst_is_rejected() -> None:
    result = score_offer({"titre": "Data analyst", "description": "Reporting BI et SQL."})

    assert result["decision"] == "Rejeté"
    assert result["score_details"]["eliminatory_reason"] == "data pur"


def test_it_support_without_web_signals_is_rejected() -> None:
    result = score_offer({"titre": "Support informatique", "description": "Helpdesk utilisateurs."})

    assert result["decision"] == "Rejeté"
    assert result["score_details"]["eliminatory_reason"] is None
    assert "support informatique" in result["score_details"]["penalties"]["matches"]


def test_it_support_with_web_signals_goes_to_review_when_score_is_enough() -> None:
    result = score_offer(
        {
            "titre": "Support informatique WordPress",
            "description": "Support de sites web avec interfaces HTML CSS JavaScript.",
            "technologies": ["WordPress", "HTML", "CSS", "JavaScript"],
        }
    )

    assert result["decision"] == "À vérifier"
    assert result["score_total"] >= 45
    assert result["score_details"]["eliminatory_reason"] is None


def test_backend_with_front_signals_goes_to_review_when_score_is_enough() -> None:
    result = score_offer(
        {
            "titre": "Developpeur front-end backend",
            "description": "Creation d'interfaces React en HTML CSS JavaScript.",
            "technologies": ["React", "HTML", "CSS", "JavaScript"],
        }
    )

    assert result["decision"] == "À vérifier"
    assert result["score_total"] >= 45
    assert result["score_details"]["eliminatory_reason"] is None


def test_devops_with_front_signals_goes_to_review_when_score_is_enough() -> None:
    result = score_offer(
        {
            "titre": "Frontend DevOps",
            "description": "Developpement d'interfaces WordPress HTML CSS JavaScript avec CI/CD.",
            "technologies": ["WordPress", "HTML", "CSS", "JavaScript"],
        }
    )

    assert result["decision"] == "À vérifier"
    assert result["score_total"] >= 45
    assert result["score_details"]["eliminatory_reason"] is None


def test_web_project_manager_with_front_signals_goes_to_review() -> None:
    result = score_offer(
        {
            "titre": "Chef de projet web WordPress",
            "description": "Coordination de sites avec HTML CSS JavaScript et maquettes.",
            "technologies": ["WordPress", "HTML", "CSS", "JavaScript"],
        }
    )

    assert result["decision"] == "À vérifier"
    assert result["score_total"] >= 45
    assert result["score_details"]["eliminatory_reason"] is None


def test_non_web_engineering_with_good_web_score_goes_to_review() -> None:
    result = score_offer(
        {
            "titre": "Ingenieur qualite frontend",
            "description": "Qualite d'interfaces WordPress HTML CSS JavaScript.",
            "technologies": ["WordPress", "HTML", "CSS", "JavaScript"],
            "type_contrat": "CDI",
            "teletravail_mention": "Teletravail partiel",
            "teletravail_jours": 2,
        }
    )

    assert result["decision"] == "À vérifier"
    assert result["score_total"] >= 45
    assert result["score_details"]["eliminatory_reason"] is None


def test_commercial_pure_offer_stays_rejected_even_with_web_signals() -> None:
    result = score_offer(
        {
            "titre": "Commercial WordPress",
            "description": "Vente de sites web HTML CSS JavaScript.",
            "technologies": ["WordPress", "HTML", "CSS", "JavaScript"],
        }
    )

    assert result["decision"] == "Rejeté"
    assert result["score_details"]["eliminatory_reason"] == "commercial pur"


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

    assert result["score_details"]["localisation"]["score"] == 15
    assert result["score_details"]["localisation"]["level"] == "local"


def test_beaune_location_gets_strong_local_points() -> None:
    result = score_offer({"localisation": "Beaune 21200"})

    assert result["score_details"]["localisation"]["score"] == 15
    assert result["score_details"]["localisation"]["level"] == "local"


def test_near_dijon_city_gets_strong_local_points() -> None:
    result = score_offer({"localisation": "Saint-Apollinaire"})
    other_result = score_offer({"localisation": "Quetigny"})

    assert result["score_details"]["localisation"]["score"] == 15
    assert result["score_details"]["localisation"]["level"] == "local"
    assert other_result["score_details"]["localisation"]["score"] == 15
    assert other_result["score_details"]["localisation"]["level"] == "local"


def test_cote_dor_or_21xxx_location_gets_department_points() -> None:
    cote_dor = score_offer({"localisation": "Cote-d'Or"})
    postal_code = score_offer({"localisation": "Chatillon-sur-Seine 21400"})

    assert cote_dor["score_details"]["localisation"]["score"] == 12
    assert cote_dor["score_details"]["localisation"]["level"] == "department"
    assert postal_code["score_details"]["localisation"]["score"] == 12
    assert postal_code["score_details"]["localisation"]["level"] == "department"


def test_bourgogne_franche_comte_or_besancon_location_gets_region_points() -> None:
    region = score_offer({"localisation": "Bourgogne-Franche-Comte"})
    city = score_offer({"localisation": "Besancon"})

    assert region["score_details"]["localisation"]["score"] == 8
    assert region["score_details"]["localisation"]["level"] == "region"
    assert city["score_details"]["localisation"]["score"] == 8
    assert city["score_details"]["localisation"]["level"] == "region"


def test_paris_location_gets_no_geographic_bonus() -> None:
    result = score_offer({"localisation": "Paris 75010"})

    assert result["score_details"]["localisation"]["score"] == 0
    assert result["score_details"]["localisation"]["level"] == "none"


def test_same_web_offer_scores_higher_in_dijon_than_paris() -> None:
    base_offer = {
        "titre": "Developpeur WordPress",
        "description": "Creation de sites WordPress avec Elementor HTML CSS.",
        "technologies": ["WordPress", "Elementor", "HTML", "CSS"],
        "type_contrat": "CDI",
    }

    dijon = score_offer({**base_offer, "localisation": "Dijon 21000"})
    paris = score_offer({**base_offer, "localisation": "Paris 75010"})

    assert dijon["score_total"] > paris["score_total"]


def test_cdi_or_cdd_contract_gets_points() -> None:
    result = score_offer(
        {
            "titre": "Integrateur web",
            "technologies": ["HTML", "CSS"],
            "type_contrat": "CDI",
        }
    )

    assert result["score_details"]["contrat"]["score"] == 5
