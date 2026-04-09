from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    app_name: str = Field(default="azure-genai-ops-copilot", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    azure_openai_api_key: str = Field(default="", alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = Field(
        default="2024-12-01-preview",
        alias="AZURE_OPENAI_API_VERSION",
    )
    azure_openai_chat_deployment: str = Field(
        default="gpt-4o-mini",
        alias="AZURE_OPENAI_CHAT_DEPLOYMENT",
    )
    azure_openai_embedding_deployment: str = Field(
        default="text-embedding-3-small",
        alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    )

    azure_search_endpoint: str = Field(default="", alias="AZURE_SEARCH_ENDPOINT")
    azure_search_api_key: str = Field(default="", alias="AZURE_SEARCH_API_KEY")
    azure_search_index_name: str = Field(
        default="ops-docs-index",
        alias="AZURE_SEARCH_INDEX_NAME",
    )

    azure_monitor_connection_string: str = Field(
        default="",
        alias="AZURE_MONITOR_CONNECTION_STRING",
    )

    default_retrieval_mode: str = Field(
        default="hybrid",
        alias="DEFAULT_RETRIEVAL_MODE",
    )
    default_top_k: int = Field(default=5, alias="DEFAULT_TOP_K")
    
    azure_openai_input_cost_per_1m: float = Field(
    default=0.0,
    alias="AZURE_OPENAI_INPUT_COST_PER_1M",
    )

    azure_openai_output_cost_per_1m: float = Field(
    default=0.0,
    alias="AZURE_OPENAI_OUTPUT_COST_PER_1M",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()