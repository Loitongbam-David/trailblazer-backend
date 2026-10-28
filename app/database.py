import re
from typing import Any

from supabase import Client, create_client

from app.config import settings


class _MissingSupabaseClient:
    def __getattr__(self, name: str) -> Any:
        raise RuntimeError(
            "Supabase client is not configured. Set valid SUPABASE_URL and SUPABASE_SERVICE_KEY values before using the database layer."
        )

    def table(self, *args, **kwargs):
        raise RuntimeError(
            "Supabase client is not configured. Set valid SUPABASE_URL and SUPABASE_SERVICE_KEY values before using the database layer."
        )


def _has_valid_supabase_url(url: str | None) -> bool:
    return bool(url) and re.match(r"^(https?)://.+", url) is not None


def _has_valid_supabase_key(key: str | None) -> bool:
    return bool(key) and re.match(
        r"^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$",
        key,
    ) is not None


def get_supabase() -> Client:
    url = getattr(settings, "supabase_url", "")
    key = getattr(settings, "supabase_service_key", "")

    if not _has_valid_supabase_url(url) or not _has_valid_supabase_key(key):
        return _MissingSupabaseClient()  # type: ignore[return-value]

    return create_client(url, key)


supabase: Client = get_supabase()
