from autotache_jobs.notifications import COLOR_REVIEW, COLOR_SUCCESS, send_discord_summary


class FakeDiscordResponse:
    def raise_for_status(self) -> None:
        return None


def _send_and_capture(summary: dict) -> dict:
    captured = {}

    def fake_post(webhook_url: str, json: dict, timeout: int) -> FakeDiscordResponse:
        captured["webhook_url"] = webhook_url
        captured["payload"] = json
        captured["timeout"] = timeout
        return FakeDiscordResponse()

    result = send_discord_summary("https://discord.test/webhook", summary, http_post=fake_post)

    assert result["sent"] is True
    return captured["payload"]


def test_discord_summary_message_does_not_contain_secret() -> None:
    secret = "fake-client-secret"

    payload = _send_and_capture(
        {
            "total_raw": 1,
            "total_relevant": 1,
            "total_new": 1,
            "decision_counts": {"Pertinent": 1, "À vérifier": 0, "Rejeté": 0},
            "best_score": 87,
            "xlsx_export_path": "exports/offres.xlsx",
            "debug_xlsx_export_path": None,
            "client_secret": secret,
            "Authorization": "Bearer token",
        }
    )
    payload_text = str(payload)

    assert secret not in payload_text
    assert "Bearer token" not in payload_text
    assert "offres.xlsx" in payload_text


def test_discord_summary_uses_file_names_without_full_paths() -> None:
    payload = _send_and_capture(
        {
            "total_raw": 3,
            "total_relevant": 1,
            "total_new": 1,
            "decision_counts": {"Pertinent": 1, "À vérifier": 0, "Rejeté": 2},
            "best_score": 91,
            "xlsx_export_path": r"D:\devAuto\AutoTache\exports\offres_2026-05-04_1151.xlsx",
            "debug_xlsx_export_path": r"D:\devAuto\AutoTache\exports\debug_offres_2026-05-04_1151.xlsx",
        }
    )
    payload_text = str(payload)

    assert "offres_2026-05-04_1151.xlsx" in payload_text
    assert "debug_offres_2026-05-04_1151.xlsx" in payload_text
    assert r"D:\devAuto\AutoTache" not in payload_text
    assert "Fichiers disponibles dans le dossier exports/" in payload_text


def test_discord_summary_contains_decision_counts_and_best_score() -> None:
    payload = _send_and_capture(
        {
            "total_raw": 3,
            "total_relevant": 0,
            "total_new": 0,
            "decision_counts": {"Pertinent": 0, "À vérifier": 2, "Rejeté": 1},
            "best_score": 72,
            "xlsx_export_path": None,
            "debug_xlsx_export_path": "exports/debug_offres.xlsx",
        }
    )
    payload_text = str(payload)

    assert "🟢 Pertinent: 0" in payload_text
    assert "🟡 À vérifier: 2" in payload_text
    assert "🔴 Rejeté: 1" in payload_text
    assert "🏆 Meilleur score: 72/100" in payload_text
    assert "Des offres sont à vérifier manuellement." in payload_text


def test_discord_payload_contains_embed_with_color() -> None:
    payload = _send_and_capture(
        {
            "total_raw": 1,
            "total_relevant": 1,
            "total_new": 1,
            "decision_counts": {"Pertinent": 1, "À vérifier": 0, "Rejeté": 0},
        }
    )

    embed = payload["embeds"][0]

    assert embed["title"] == "📌 AutoTache - Résumé recherche emploi"
    assert embed["color"] == COLOR_SUCCESS
    assert embed["fields"]


def test_discord_payload_uses_review_color_when_no_new_offer_but_review_exists() -> None:
    payload = _send_and_capture(
        {
            "total_raw": 1,
            "total_relevant": 0,
            "total_new": 0,
            "decision_counts": {"Pertinent": 0, "À vérifier": 1, "Rejeté": 0},
        }
    )

    assert payload["embeds"][0]["color"] == COLOR_REVIEW


def test_discord_summary_without_webhook_returns_clear_status() -> None:
    calls = []

    result = send_discord_summary(
        "",
        {"total_raw": 0, "total_relevant": 0, "total_new": 0},
        http_post=lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    assert calls == []
    assert result["sent"] is False
    assert result["status"] == "webhook_missing"
    assert "DISCORD_WEBHOOK_URL" in result["error"]
