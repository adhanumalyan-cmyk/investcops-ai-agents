"""
Database engine and session management (SQLAlchemy 2.x).

Development defaults to SQLite so the app runs without a database server.
Production integration uses PostgreSQL via DATABASE_URL.
"""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("database")


def _create_engine() -> Engine:
    url = settings.DATABASE_URL or "sqlite:///./investcops.db"
    opts: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        opts["connect_args"] = {"check_same_thread": False}
    else:
        opts["pool_size"] = 5
        opts["max_overflow"] = 10
    return create_engine(url, **opts)


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables from models on startup (dev convenience). Alembic for migrations."""
    from app.database.base import Base  # noqa: F401
    from app.models import models  # noqa: F401  (register models)

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")


def check_db_connection() -> bool:
    """Raise-free health check."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.warning("Database connection check failed: %s", exc)
        return False


# Import Base here so `from app.database import Base` works.
from app.database.base import Base  # noqa: E402

__all__ = ["Base", "engine", "SessionLocal", "get_db", "init_db", "check_db_connection"]