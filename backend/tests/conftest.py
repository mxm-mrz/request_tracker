import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

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
