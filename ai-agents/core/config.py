"""
Configuration Management
Environment-based configuration for agents and orchestrator.
Never hardcode secrets; everything comes from environment variables.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic-settings based application configuration."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Environment
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    ENVIRONMENT: str = Field(default="development", description="deployment: development|test|production")

    # Service URLs
    AGENTS_SERVICE_URL: str = Field(default="http://localhost:8001")
    BACKEND_SERVICE_URL: str = Field(default="http://localhost:8000")

    # LLM provider (initial implementation: Gemini). Abstracted so other
    # providers can be added later.
    LLM_PROVIDER: str = Field(default="none", description="none|gemini|openai|local")
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash")
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")
    LOCAL_LLM_URL: Optional[str] = Field(default=None)
    # Maximum number of LLM calls an agent may attempt before failing.
    LLM_MAX_RETRIES: int = Field(default=2)
    LLM_TIMEOUT_SECONDS: int = Field(default=60)
    # Hard cap on context characters sent to an LLM per call (safety: do not
    # send the entire evidence repository to the model).
    LLM_MAX_CONTEXT_CHARS: int = Field(default=40_000)

    # Graph database (Neo4j)
    NEO4J_URI: Optional[str] = Field(default=None)
    NEO4J_USERNAME: Optional[str] = Field(default=None)
    NEO4J_PASSWORD: Optional[str] = Field(default=None)

    # PostgreSQL
    DATABASE_URL: Optional[str] = Field(default=None)

    # Evidence storage (development: local directory; production: S3-compatible)
    STORAGE_ENDPOINT: Optional[str] = Field(default=None)
    STORAGE_ACCESS_KEY: Optional[str] = Field(default=None)
    STORAGE_SECRET_KEY: Optional[str] = Field(default=None)
    STORAGE_BUCKET: Optional[str] = Field(default=None)
    LOCAL_STORAGE_DIR: str = Field(default="data/evidence")

    # Versioning -- recorded in every agent run for reproducibility.
    AGENT_VERSION: str = Field(default="1.0.0")

    @property
    def llm_enabled(self) -> bool:
        """True when an LLM provider + key are configured."""
        if self.LLM_PROVIDER == "gemini":
            return bool(self.GEMINI_API_KEY)
        if self.LLM_PROVIDER == "openai":
            return bool(self.OPENAI_API_KEY)
        if self.LLM_PROVIDER == "local":
            return bool(self.LOCAL_LLM_URL)
        return False

    def validate_required(self) -> None:
        """Raise a clear error for misconfigured critical settings."""
        if self.NEO4J_URI and not (self.NEO4J_USERNAME and self.NEO4J_PASSWORD):
            raise ValueError(
                "NEO4J_URI is set but NEO4J_USERNAME/NEO4J_PASSWORD are missing"
            )
        if self.LLM_PROVIDER not in ("none", "gemini", "openai", "local"):
            raise ValueError(
                f"Unsupported LLM_PROVIDER: {self.LLM_PROVIDER!r}. "
                "Use one of: none, gemini, openai, local"
            )


# Backwards-compatible singleton accessor.
def get_config() -> Settings:
    return Settings()


# Backwards-compatible module-level helper.
def validate() -> bool:
    """Validate critical configuration. Returns True when valid."""
    try:
        Settings().validate_required()
        return True
    except ValueError:
        return False


_config: Optional[Settings] = None


def load_config() -> Settings:
    """Load configuration once and cache it."""
    global _config
    if _config is None:
        _config = Settings()
        _config.validate_required()
    return _config


# Convenience default instance (lazily resolved).
settings = load_config()