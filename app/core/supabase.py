from app.core.settings import Settings
from supabase import Client, create_client


def get_supabase_client(settings: Settings) -> Client:
    key = settings.supabase_service_key or settings.supabase_anon_key
    if not key:
        raise ValueError("Supabase key is not configured")
    return create_client(settings.supabase_url, key)
