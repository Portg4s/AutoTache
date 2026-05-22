import pytest

from autotache_jobs.supabase.settings import SupabaseSettingsError, load_supabase_settings_from_env


def test_load_supabase_settings_reads_valid_environment(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "secret-value")
    monkeypatch.setenv("SUPABASE_OWNER_ID", "11111111-1111-1111-1111-111111111111")
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")

    settings = load_supabase_settings_from_env()

    assert settings.url == "https://example.supabase.co"
    assert settings.secret_key == "secret-value"
    assert settings.owner_id == "11111111-1111-1111-1111-111111111111"
    assert settings.github_run_id == "12345"
    assert settings.trigger_type == "manual"


def test_load_supabase_settings_requires_values_only_when_called(monkeypatch) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_OWNER_ID", raising=False)

    with pytest.raises(SupabaseSettingsError, match="SUPABASE_URL"):
        load_supabase_settings_from_env()


def test_load_supabase_settings_rejects_invalid_owner_uuid(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "secret-value")
    monkeypatch.setenv("SUPABASE_OWNER_ID", "not-a-uuid")

    with pytest.raises(SupabaseSettingsError, match="UUID valide"):
        load_supabase_settings_from_env()


def test_load_supabase_settings_maps_scheduled_and_local_events(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "secret-value")
    monkeypatch.setenv("SUPABASE_OWNER_ID", "11111111-1111-1111-1111-111111111111")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "schedule")

    assert load_supabase_settings_from_env().trigger_type == "scheduled"

    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")

    assert load_supabase_settings_from_env().trigger_type == "local"
