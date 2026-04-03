from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: Optional[str] = None
    supabase_url: str
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None
    supabase_jwt_secret: str
    supabase_jwt_alg: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
