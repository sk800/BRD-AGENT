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
    default_chunking_method: str = "parent_child"

    lance_db_path: str = "data/lancedb"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_pipeline_version: int = 1

    # Enterprise knowledge — Confluence
    confluence_base_url: str = ""
    confluence_email: str = ""
    confluence_api_token: str = ""

    # Enterprise knowledge — ServiceNow
    servicenow_instance_url: str = ""
    servicenow_username: str = ""
    servicenow_password: str = ""

    # MCP client: in-process server (dev) vs stdio subprocess (production)
    mcp_enterprise_use_inprocess: bool = True
    mcp_enterprise_server_command: str = ""
    mcp_enterprise_server_args: list[str] = []

    # Azure OpenAI requirement discovery
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-5.4-nano"
    azure_openai_api_version: str = "2024-12-01-preview"
    llm_max_completion_tokens: int = 16384

    # Context assembly (BRD generation): chunks retrieved from uploads in LanceDB
    context_retrieval_top_k: int = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()
