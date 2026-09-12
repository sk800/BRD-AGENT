from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    environment: str = "dev"
    debug: bool = True

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "brd_agent"

    secret_key: str = "change-me-to-a-long-random-secret-key"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    upload_dir: str = "data/uploads"
    max_file_size_mb: int = 25
    max_files_per_message: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
