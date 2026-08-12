"""
app/core/config.py

Application settings (pydantic-settings, .env friendly).
Keeps the backend concept: FastAPI + PostgreSQL (optional) + Neo4j (optional).
All settings below have sane defaults so the app runs standalone.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "InvestCops AI - Forensic Intelligence Backend"
    api_prefix: str = "/api"

    # Optional infra (concept-ready): only used when set
    database_url: Optional[str] = None
    neo4j_uri: Optional[str] = None
    neo4j_user: Optional[str] = "neo4j"
    neo4j_password: Optional[str] = None

    # Ollama (used for FIR conversion; falls back to mock when offline)
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:0.6b"

    # Limits
    max_fir_chars: int = 20000
    max_system_chars: int = 4000


settings = Settings()