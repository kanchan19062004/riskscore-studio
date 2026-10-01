import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.cache import MemoryCache, set_cache
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.rate_limit import MemoryRateLimiter, set_rate_limiter
from app.main import app
from app.models import User
from app.services import scorer


@pytest.fixture(autouse=True)
def isolated_model_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "MODEL_DIR", tmp_path / "artifacts")


@pytest.fixture(autouse=True)
def memory_cache():
    cache = MemoryCache()
    set_cache(cache)
    scorer._pipelines.clear()
    yield cache
    scorer._pipelines.clear()
    set_cache(None)


@pytest.fixture(autouse=True)
def memory_limiter():
    limiter = MemoryRateLimiter()
    set_rate_limiter(limiter)
    yield limiter
    set_rate_limiter(None)


@pytest.fixture
def session_factory():
    # StaticPool keeps one connection so every session sees the same in-memory DB.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


PASSWORD = "secret123"


def auth_headers(client, email):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": PASSWORD},
    )
    token = client.post(
        "/api/v1/auth/login", data={"username": email, "password": PASSWORD}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def analyst(client):
    return auth_headers(client, "analyst@example.com")


@pytest.fixture
def admin(client, session_factory):
    headers = auth_headers(client, "admin@example.com")
    with session_factory() as db:
        db.execute(update(User).where(User.email == "admin@example.com").values(role="admin"))
        db.commit()
    return headers


def train(client, headers, **body):
    return client.post("/api/v1/models/train", json={"n_samples": 2_000, **body}, headers=headers)
