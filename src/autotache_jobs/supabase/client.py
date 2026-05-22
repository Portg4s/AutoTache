"""Thin wrapper around the official Supabase client."""

from __future__ import annotations

from typing import Any

from autotache_jobs.supabase.settings import SupabaseSettings


def create_supabase_client(settings: SupabaseSettings) -> Any:
    """Create the official Supabase client without logging credentials."""

    from supabase import create_client

    return create_client(settings.url, settings.secret_key)
