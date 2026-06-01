from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the skeleton API.

    The MVP stores files locally first. Upload, AI analysis, and authentication
    are intentionally out of scope for this initial scaffold.
    """

    app_name: str = "work-support API"
    app_env: str = "local"
    database_url: str = "postgresql://localhost/work_support"
    local_storage_root: str = "storage/uploads"
    frontend_origin: str = "http://localhost:3000"
    default_owner_id: str = "local-owner"
    report_access_token: str = "dev-only-report-token"
    report_timezone: str = "Asia/Seoul"
    work_support_schema_sql_path: Optional[str] = None
    openai_api_key: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
