import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = f"sqlite:///{Path(__file__).resolve().parent / 'test_investcops.db'}"
os.environ["LOG_LEVEL"] = "WARNING"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import pytest
from fastapi.testclient import TestClient

from app.database import session
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _prepare_db():
    db_path = Path(__file__).resolve().parent / "test_investcops.db"
    db_path.unlink(missing_ok=True)
    session.init_db()
    yield
    session.engine.dispose()


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c