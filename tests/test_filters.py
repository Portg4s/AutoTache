from autotache_jobs.filters import is_relevant_offer


def test_wordpress_developer_is_relevant() -> None:
    result = is_relevant_offer(
        {
            "titre": "Developpeur WordPress",
            "description": "Creation de themes WordPress avec Elementor et WooCommerce.",
        }
    )

    assert result["is_relevant"] is True
    assert "WordPress" in result["matched_keywords"]


def test_frontend_integrator_is_relevant() -> None:
    result = is_relevant_offer(
        {
            "titre": "Integrateur front-end",
            "description": "Integration HTML CSS JavaScript avec Bootstrap.",
        }
    )

    assert result["is_relevant"] is True
    assert "integrateur front-end" in result["matched_keywords"]


def test_ui_ux_designer_is_relevant() -> None:
    result = is_relevant_offer(
        {
            "titre": "UI/UX designer",
            "description": "Conception de parcours UX et interfaces UI sur Figma.",
        }
    )

    assert result["is_relevant"] is True
    assert "UI/UX designer" in result["matched_keywords"]


def test_graphiste_web_is_relevant() -> None:
    result = is_relevant_offer(
        {
            "titre": "Graphiste web",
            "description": "Creation de visuels digitaux pour sites et landing pages.",
        }
    )

    assert result["is_relevant"] is True
    assert "graphiste web" in result["matched_keywords"]


def test_print_only_graphiste_is_rejected() -> None:
    result = is_relevant_offer(
        {
            "titre": "Graphiste print",
            "description": "Execution pre-presse, packaging et supports imprimes.",
        }
    )

    assert result["is_relevant"] is False
    assert "graphiste print uniquement" in result["excluded_by"]


def test_backend_only_is_rejected() -> None:
    result = is_relevant_offer(
        {
            "titre": "Developpeur backend",
            "description": "APIs REST en Symfony, architecture serveur et bases de donnees.",
        }
    )

    assert result["is_relevant"] is False
    assert "backend pur" in result["excluded_by"]


def test_fullstack_react_is_relevant() -> None:
    result = is_relevant_offer(
        {
            "titre": "Developpeur fullstack",
            "description": "Developpement fullstack avec React cote front-end et API existante.",
        }
    )

    assert result["is_relevant"] is True
    assert "React" in result["matched_keywords"]


def test_data_analyst_is_rejected() -> None:
    result = is_relevant_offer(
        {
            "titre": "Data analyst",
            "description": "Analyse de donnees, reporting BI et SQL.",
        }
    )

    assert result["is_relevant"] is False
    assert "data analyst" in result["excluded_by"]


def test_support_informatique_is_rejected() -> None:
    result = is_relevant_offer(
        {
            "titre": "Technicien support informatique",
            "description": "Assistance utilisateurs et gestion tickets.",
        }
    )

    assert result["is_relevant"] is False
    assert "support informatique" in result["excluded_by"]


def test_stage_is_rejected_by_default() -> None:
    result = is_relevant_offer(
        {
            "titre": "Stage integrateur web",
            "description": "Stage HTML CSS WordPress.",
            "type_contrat": "Stage",
        }
    )

    assert result["is_relevant"] is False
    assert "stage" in result["excluded_by"]


def test_stage_is_allowed_when_enabled() -> None:
    result = is_relevant_offer(
        {
            "titre": "Stage integrateur web",
            "description": "Stage HTML CSS WordPress.",
            "type_contrat": "Stage",
        },
        allow_stage=True,
    )

    assert result["is_relevant"] is True
    assert "stage" not in result["excluded_by"]


def test_alternance_is_rejected_by_default() -> None:
    result = is_relevant_offer(
        {
            "titre": "Alternance developpeur front-end",
            "description": "Contrat en alternance sur React.",
            "type_contrat": "Alternance",
        }
    )

    assert result["is_relevant"] is False
    assert "alternance" in result["excluded_by"]


def test_alternance_is_allowed_when_enabled() -> None:
    result = is_relevant_offer(
        {
            "titre": "Alternance developpeur front-end",
            "description": "Contrat en alternance sur React.",
            "type_contrat": "Alternance",
        },
        allow_alternance=True,
    )

    assert result["is_relevant"] is True
    assert "alternance" not in result["excluded_by"]
