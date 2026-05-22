"""Supabase environment settings loaded only when sync is enabled."""

from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import UUID


class SupabaseSettingsError(RuntimeError):
    """Raised when Supabase sync settings are missing or invalid."""


@dataclass(frozen=True)
class SupabaseSettings:
    url: str
    secret_key: str
    owner_id: str
    github_run_id: str
    trigger_type: str


def load_supabase_settings_from_env() -> SupabaseSettings:
    """Load required Supabase settings from environment variables."""

    url = _required_env("SUPABASE_URL")
    secret_key = _required_env("SUPABASE_SECRET_KEY")
    owner_id = _required_env("SUPABASE_OWNER_ID")
    try:
        UUID(owner_id)
    except ValueError as exc:
        raise SupabaseSettingsError("SUPABASE_OWNER_ID doit etre un UUID valide.") from exc

    return SupabaseSettings(
        url=url,
        secret_key=secret_key,
        owner_id=owner_id,
        github_run_id=os.getenv("GITHUB_RUN_ID", "").strip(),
        trigger_type=_trigger_type(os.getenv("GITHUB_EVENT_NAME", "").strip()),
    )


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SupabaseSettingsError(f"Variable {name} manquante pour la synchronisation Supabase.")
    return value


def _trigger_type(event_name: str) -> str:
    if event_name == "schedule":
        return "scheduled"
    if event_name == "workflow_dispatch":
        return "manual"
    return "local"
