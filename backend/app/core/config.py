"""
Application configuration for the FastAPI backend.
All values come from environment variables (never hardcoded secrets).
"""


from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    ENVIRONMENT: str = Field(default="development")
    APP_NAME: str = Field(default="INVESTCOPS AI Backend")
    APP_VERSION: str = Field(default="0.2.0")
    CORS_ORIGINS: str = Field(default="*")

    # Database (PostgreSQL in production, SQLite fallback for local dev/tests)
    DATABASE_URL: str | None = Field(default="sqlite:///./investcops.db")

    # Neo4j (optional; graph module degrades gracefully when disabled)
    NEO4J_URI: str | None = None
    NEO4J_USERNAME: str | None = None
    NEO4J_PASSWORD: str | None = None

    # Auth
    JWT_SECRET: str = Field(default="dev-only-change-me", description="Set a strong secret in production")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRES_MINUTES: int = Field(default=1440)

    # Evidence storage
    STORAGE_ENDPOINT: str | None = None
    STORAGE_ACCESS_KEY: str | None = None
    STORAGE_SECRET_KEY: str | None = None
    STORAGE_BUCKET: str | None = None
    LOCAL_STORAGE_DIR: str = Field(default="data/evidence")

    # Evidence limits
    MAX_UPLOAD_MB: int = Field(default=200, description="Max evidence file size in MB")
    ALLOWED_EXTENSIONS: str = Field(
        default="txt,json,pdf,jpg,jpeg,png,mp4,webm,mp3,wav,m4a,apk,html,csv,zip,eml,msg"
    )

    # Agents integration
    AGENTS_SERVICE_URL: str = Field(default="http://localhost:8001")

    # Ollama (FIR conversion; falls back to mock when offline)
    OLLAMA_BASE_URL: str = Field(default="http://127.0.0.1:11434")
    OLLAMA_MODEL: str = Field(default="qwen3:0.6b")

    # FIR conversion limits
    MAX_FIR_CHARS: int = Field(default=20000)
    MAX_SYSTEM_CHARS: int = Field(default=4000)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [e.strip().lower() for e in self.ALLOWED_EXTENSIONS.split(",") if e.strip()]


def get_settings() -> Settings:
    return Settings()


settings = get_settings()