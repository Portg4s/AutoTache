import json
from pathlib import Path

from autotache_jobs.notifications import COLOR_REVIEW, COLOR_SUCCESS, send_discord_summary


class FakeDiscordResponse:
    def raise_for_status(self) -> None:
        return None


def _send_and_capture(summary: dict) -> dict:
    captured = {}

    def fake_post(webhook_url: str, **kwargs) -> FakeDiscordResponse:
        captured["webhook_url"] = webhook_url
        captured["timeout"] = kwargs["timeout"]
        if "json" in kwargs:
            captured["payload"] = kwargs["json"]
        else:
            captured["payload"] = json.loads(kwargs["data"]["payload_json"])
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
            "decision_counts": {"Pertinent": 1, "\u00c0 v\u00e9rifier": 0, "Rejet\u00e9": 0},
            "best_score": 87,
            "xlsx_export_path": "exports/offres.xlsx",
            "tracking_xlsx_export_path": "exports/offres/offres_suivi.xlsx",
            "debug_xlsx_export_path": None,
            "source_stats": {"Adzuna": {"enabled": True, "fetched": 1, "kept": 1, "filtered": 0}},
            "client_secret": secret,
            "Authorization": "Bearer token",
        }
    )
    payload_text = str(payload)

    assert secret not in payload_text
    assert "Bearer token" not in payload_text
    assert "offres.xlsx" in payload_text
    assert "offres_suivi.xlsx" in payload_text
    assert "\U0001F4CC Suivi: offres_suivi.xlsx" in payload_text
    assert "\U0001F195 Nouvelles offres: offres.xlsx" in payload_text
    assert "\U0001F9EA Debug: aucun" in payload_text


def test_discord_summary_uses_file_names_without_full_paths() -> None:
    payload = _send_and_capture(
        {
            "total_raw": 3,
            "total_relevant": 1,
            "total_new": 1,
            "decision_counts": {"Pertinent": 1, "\u00c0 v\u00e9rifier": 0, "Rejet\u00e9": 2},
            "best_score": 91,
            "xlsx_export_path": r"D:\devAuto\AutoTache\exports\offres\offres_2026-05-04_1151.xlsx",
            "tracking_xlsx_export_path": r"D:\devAuto\AutoTache\exports\offres\offres_suivi.xlsx",
            "debug_xlsx_export_path": r"D:\devAuto\AutoTache\exports\debug\debug_offres_2026-05-04_1151.xlsx",
        }
    )
    payload_text = str(payload)

    assert "offres_2026-05-04_1151.xlsx" in payload_text
    assert "offres_suivi.xlsx" in payload_text
    assert "debug_offres_2026-05-04_1151.xlsx" in payload_text
    assert "\U0001F4CC Suivi: offres_suivi.xlsx" in payload_text
    assert "\U0001F195 Nouvelles offres: offres_2026-05-04_1151.xlsx" in payload_text
    assert "\U0001F9EA Debug: debug_offres_2026-05-04_1151.xlsx" in payload_text
    assert r"D:\devAuto\AutoTache" not in payload_text
    assert "Fichiers disponibles dans le dossier exports/" in payload_text


def test_discord_summary_contains_decision_counts_and_best_score() -> None:
    payload = _send_and_capture(
        {
            "total_raw": 3,
            "total_relevant": 0,
            "total_new": 0,
            "decision_counts": {"Pertinent": 0, "\u00c0 v\u00e9rifier": 2, "Rejet\u00e9": 1},
            "best_score": 72,
            "xlsx_export_path": None,
            "tracking_xlsx_export_path": None,
            "debug_xlsx_export_path": "exports/debug_offres.xlsx",
        }
    )
    payload_text = str(payload)

    assert "\U0001F7E2 Pertinent: 0" in payload_text
    assert "\U0001F7E1 \u00c0 v\u00e9rifier: 2" in payload_text
    assert "\U0001F534 Rejet\u00e9: 1" in payload_text
    assert "\U0001F3C6 Meilleur score: 72/100" in payload_text
    assert "Des offres sont \u00e0 v\u00e9rifier manuellement." in payload_text
    assert "\U0001F4CC Suivi: aucun" in payload_text
    assert "\U0001F195 Nouvelles offres: aucun" in payload_text
    assert "\U0001F9EA Debug: debug_offres.xlsx" in payload_text


def test_discord_summary_shows_only_sources_with_fetched_offers() -> None:
    payload = _send_and_capture(
        {
            "total_raw": 12,
            "total_relevant": 4,
            "total_new": 2,
            "decision_counts": {"Pertinent": 2, "\u00c0 v\u00e9rifier": 2, "Rejet\u00e9": 8},
            "source_stats": {
                "France Travail": {"enabled": False, "fetched": 0, "kept": 0, "filtered": 0},
                "Adzuna": {"enabled": True, "fetched": 12, "kept": 12, "filtered": 0},
                "Jooble": {"enabled": True, "fetched": 0, "kept": 0, "filtered": 0},
            },
        }
    )

    fields = payload["embeds"][0]["fields"]
    sources_field = next(field for field in fields if field["name"] == "\U0001F310 Sources")

    assert sources_field["value"] == "Adzuna : 12 r\u00e9cup\u00e9r\u00e9es"
    assert "France Travail" not in sources_field["value"]
    assert "Jooble" not in sources_field["value"]


def test_discord_summary_shows_empty_sources_message_when_none_fetched() -> None:
    payload = _send_and_capture(
        {
            "total_raw": 0,
            "total_relevant": 0,
            "total_new": 0,
            "decision_counts": {"Pertinent": 0, "\u00c0 v\u00e9rifier": 0, "Rejet\u00e9": 0},
            "source_stats": {
                "Adzuna": {"enabled": True, "fetched": 0, "kept": 0, "filtered": 0},
                "Jooble": {"enabled": False, "fetched": 0, "kept": 0, "filtered": 0},
            },
        }
    )

    fields = payload["embeds"][0]["fields"]
    sources_field = next(field for field in fields if field["name"] == "\U0001F310 Sources")

    assert sources_field["value"] == "Aucune offre r\u00e9cup\u00e9r\u00e9e"
    assert "Adzuna :" not in sources_field["value"]
    assert "Jooble :" not in sources_field["value"]


def test_discord_payload_contains_embed_with_color() -> None:
    payload = _send_and_capture(
        {
            "total_raw": 1,
            "total_relevant": 1,
            "total_new": 1,
            "decision_counts": {"Pertinent": 1, "\u00c0 v\u00e9rifier": 0, "Rejet\u00e9": 0},
        }
    )

    embed = payload["embeds"][0]

    assert embed["title"] == "\U0001F4CC AutoTache - R\u00e9sum\u00e9 recherche emploi"
    assert embed["color"] == COLOR_SUCCESS
    assert embed["fields"]


def test_discord_payload_uses_review_color_when_no_new_offer_but_review_exists() -> None:
    payload = _send_and_capture(
        {
            "total_raw": 1,
            "total_relevant": 0,
            "total_new": 0,
            "decision_counts": {"Pertinent": 0, "\u00c0 v\u00e9rifier": 1, "Rejet\u00e9": 0},
        }
    )

    assert payload["embeds"][0]["color"] == COLOR_REVIEW


def test_discord_summary_sends_tracking_xlsx_as_attachment_when_file_exists(tmp_path: Path) -> None:
    tracking_file = tmp_path / "exports" / "offres" / "offres_suivi.xlsx"
    tracking_file.parent.mkdir(parents=True)
    tracking_file.write_bytes(b"fake xlsx bytes")
    captured = {}

    def fake_post(webhook_url: str, data: dict, files: dict, timeout: int) -> FakeDiscordResponse:
        captured["webhook_url"] = webhook_url
        captured["data"] = data
        captured["files"] = files
        captured["timeout"] = timeout
        return FakeDiscordResponse()

    result = send_discord_summary(
        "https://discord.test/webhook",
        {
            "total_raw": 1,
            "total_relevant": 1,
            "total_new": 1,
            "decision_counts": {"Pertinent": 1, "\u00c0 v\u00e9rifier": 0, "Rejet\u00e9": 0},
            "tracking_xlsx_export_path": str(tracking_file),
        },
        http_post=fake_post,
    )

    payload = json.loads(captured["data"]["payload_json"])
    file_name, file_handle, content_type = captured["files"]["file"]

    assert result["sent"] is True
    assert captured["webhook_url"] == "https://discord.test/webhook"
    assert captured["timeout"] == 10
    assert "payload_json" in captured["data"]
    assert "json" not in captured
    assert file_name == "offres_suivi.xlsx"
    assert file_handle.name == str(tracking_file)
    assert content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "Le fichier de suivi cumulatif est joint." in str(payload)


def test_discord_summary_uses_json_when_tracking_xlsx_is_missing(tmp_path: Path) -> None:
    missing_file = tmp_path / "exports" / "offres" / "offres_suivi.xlsx"
    captured = {}

    def fake_post(webhook_url: str, json: dict, timeout: int) -> FakeDiscordResponse:
        captured["webhook_url"] = webhook_url
        captured["payload"] = json
        captured["timeout"] = timeout
        return FakeDiscordResponse()

    result = send_discord_summary(
        "https://discord.test/webhook",
        {
            "total_raw": 0,
            "total_relevant": 0,
            "total_new": 0,
            "tracking_xlsx_export_path": str(missing_file),
        },
        http_post=fake_post,
    )

    assert result["sent"] is True
    assert captured["webhook_url"] == "https://discord.test/webhook"
    assert captured["timeout"] == 10
    assert captured["payload"]["embeds"]
    assert "Le fichier de suivi cumulatif est joint." not in str(captured["payload"])


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
