# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
from pathlib import Path
from sqlmodel import SQLModel

from api.db.dependencies import get_db

# Get project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Alembic configuration
def run_migrations():
    config = Config(BASE_DIR / "alembic.ini")
    config.set_main_option("script_location", str(BASE_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.upgrade(config, "head")

# Fixtures
@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    SQLModel.metadata.create_all(engine)  # Create tables first
    run_migrations()
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    from fastapi.testclient import TestClient
    from api.main import app

    # Dependency override with commit
    def override_get_db():
        try:
            db_session.begin()  # Start nested transaction
            yield db_session
            db_session.commit()
        except:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


def test_check_db(client):
    response = client.get("/check-db")
    assert response.status_code == 200
    data = response.json()
    # Ensure the key 'database_time' exists in the response.
    assert "database_time" in data
    # Optionally, check that the value is not None or matches an expected format