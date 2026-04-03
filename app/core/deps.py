from fastapi import Depends

from app.core.settings import Settings, get_settings
from app.core.supabase import get_supabase_client
from supabase import Client


def get_settings_dep() -> Settings:
    return get_settings()


def get_supabase_dep(settings: Settings = Depends(get_settings_dep)) -> Client:
    return get_supabase_client(settings)
