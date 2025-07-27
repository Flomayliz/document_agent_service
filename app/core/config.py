from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
import os


ENV_FILE_PATH = os.getenv("ENV_PATH", ".env")


class Settings(BaseSettings):
    """Application settings."""

    # LLM Configuration
    model_backend: Literal["openai", "ollama", "gemini"] = "openai"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    ollama_model: str = "deepseek-67b"

    # API Configuration
    api_token: str = "demo-token"

    # Database Configuration
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "llm_doc_poc"

    # Watcher Configuration
    watch_folder: str = "/data/inbox"

    # Processing Configuration
    max_tokens_doc: int = 15000

    # Server Configuration
    main_api_host: str = "0.0.0.0"
    main_api_port: int = 8000
    admin_api_host: str = "127.0.0.1"
    admin_api_port: int = 8001

    # Development
    debug: bool = False

    # Configuration
    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
