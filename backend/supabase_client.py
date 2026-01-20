import os
from supabase import create_client, Client


def get_supabase_client() -> Client:
    """Initialize and return a Supabase client using environment variables.

    Uses the Supabase service role key, so it MUST only be used on backend.
    If Supabase is not configured yet, this will raise a runtime error
    only when the upload endpoint is actually called.
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise RuntimeError("Supabase is not configured (missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)")

    return create_client(url, key)
