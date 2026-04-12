import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

import app.services.blacklist_service as blacklist_service_module
from app.main import app
from app.database import Base, get_db
from app.redis_client import redis_client

# Строка подключения для SQLite в оперативной памяти
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


class FakeSecurityRedis:
    def __init__(self):
        self.store: dict[str, object] = {}

    def get(self, name: str):
        return self.store.get(name)

    def setex(self, name: str, time: int, value):
        self.store[name] = value

    def delete(self, *names: str):
        deleted = 0
        for name in names:
            if name in self.store:
                del self.store[name]
                deleted += 1
        return deleted

    def scan_iter(self, match: str | None = None):
        for key in list(self.store.keys()):
            if match is None or key.startswith(match.rstrip('*')):
                yield key


@pytest.fixture()
def db_session():
    """Создает свежую базу данных для каждого теста и удаляет её после."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    """Подменяет зависимость базы данных в FastAPI и выдает TestClient."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def fake_blacklist_redis(monkeypatch):
    fake_redis = FakeSecurityRedis()
    monkeypatch.setattr(blacklist_service_module, 'redis_client', fake_redis)
    return fake_redis


@pytest.fixture(autouse=True)
def clear_rate_limit_keys():
    try:
        keys_to_delete = list(redis_client.scan_iter(match='rate_limit:*'))
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)
    except Exception:
        pass

    yield

    try:
        keys_to_delete = list(redis_client.scan_iter(match='rate_limit:*'))
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)
    except Exception:
        pass
