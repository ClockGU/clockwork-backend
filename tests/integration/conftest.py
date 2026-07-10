# tests/conftest.py
import asyncio
import os
import uuid
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import psycopg2
import pytest
from alembic import command
from alembic.config import Config
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

from api.consts import PetitionStatus
from api.db.dependencies import get_db
from api.db.schema.budget_position import BudgetPosition
from api.db.schema.employee import Employee
from api.db.schema.petition import Petition
from api.db.schema.student_documents import StudentDocuments
from api.env import settings
from api.main import app
from api.security import get_current_student

# Get project root
from api.websockets.managers import (
    WebsocketConnectionManager,
    get_clerk_connection_manager,
)

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DB_URI = settings.DATABASE_URL.replace("/db_app", "/postgres")
TEST_DB_URL = ""
engine: Engine
TestingSessionLocal: Session


# Alembic configuration
def run_migrations():
    config = Config(BASE_DIR / "alembic.ini")
    config.set_main_option("script_location", str(BASE_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.upgrade(config, "head")


def create_test_database():
    conn = psycopg2.connect(DB_URI)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'test_db'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE test_db")
    cur.close()
    conn.close()


def drop_test_database():
    conn = psycopg2.connect(DB_URI)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("DROP DATABASE IF EXISTS test_db")
    cur.close()
    conn.close()


# Fixtures
@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    create_test_database()
    # point engine at test_db, not the real one
    global engine, TestingSessionLocal, TEST_DB_URL
    TEST_DB_URL = settings.DATABASE_URL.replace("/your_real_db", "/test_db")
    engine = create_engine(TEST_DB_URL)
    TestingSessionLocal = sessionmaker(bind=engine)
    run_migrations()
    yield
    drop_test_database()


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(
        bind=connection, join_transaction_mode="create_savepoint"
    )
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    from fastapi.testclient import TestClient

    from api.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture
def get_clerk_connection_manager_fixture_callable():
    def mock_auth(token):
        if token != "some_valid_token":
            raise ValueError("invalid token")

    _websocket_manager = WebsocketConnectionManager(mock_auth)
    return lambda: _websocket_manager


@pytest.fixture
def petition_student_action(db_session):
    petition = Petition(
        user_account=uuid.uuid4(),
        org_unit="Finance",
        eos_number="F123456",
        start_date=date(2025, 3, 1),
        end_date=date(2025, 6, 30),
        minutes=480,
        ba_degree=False,
        student_username="teststudent",
        status=PetitionStatus.STUDENT_ACTION,
    )
    db_session.add(petition)
    db_session.flush()
    db_session.commit()
    budget_position = BudgetPosition(
        petition_id=petition.id,
        budget_position="SHK",
        budget_approver="approver@uni-frankfurt.de",
        percentage=100.0,
    )
    db_session.add(budget_position)
    db_session.flush()

    return petition


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mock_clerk_list(monkeypatch):
    import api.websockets.routers.web_socket as ws_module

    monkeypatch.setattr(ws_module, "get_all_clerks", lambda: ["clerk1"])


@pytest.fixture
def mock_get_clerk_connection_manager(
    monkeypatch, get_clerk_connection_manager_fixture_callable
):
    import api.websockets.routers.web_socket as ws_module

    monkeypatch.setattr(
        ws_module,
        "get_clerk_connection_manager",
        get_clerk_connection_manager_fixture_callable,
    )


@pytest.fixture
def student_employee(db_session):
    employee = Employee(
        user_account=uuid.uuid4(),
        username="teststudent",
        date_of_birth=date(2000, 1, 1),
        address="Test Street 1",
    )
    db_session.add(employee)
    db_session.flush()
    return employee


@pytest.fixture
def student_documents(db_session, student_employee):
    docs = StudentDocuments(
        employee_id=student_employee.id,
        elstam_url="elstam.pdf",
        studienbescheinigung_url="studien.pdf",
        versicherungsbescheinigung_url="versicherung.pdf",
        sozialversicherungsbogen_url="sozialversicherung.pdf",
    )
    db_session.add(docs)
    db_session.flush()
    return docs


@pytest.fixture
async def clerk_ws_setup(
    db_session,
    mock_clerk_list,
    mock_get_clerk_connection_manager,
    get_clerk_connection_manager_fixture_callable,
):

    app.dependency_overrides[get_clerk_connection_manager] = (
        get_clerk_connection_manager_fixture_callable
    )
    app.dependency_overrides[get_current_student] = lambda: {}
    app.dependency_overrides[get_db] = lambda: db_session

    c2s: asyncio.Queue = asyncio.Queue()
    s2c: asyncio.Queue = asyncio.Queue()

    async def receive():
        return await c2s.get()

    async def send(message):
        await s2c.put(message)

    ws_scope = {
        "type": "websocket",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "headers": [],
        "path": "/ws/clerk1",
        "raw_path": b"/ws/clerk1",
        "query_string": b"",
        "root_path": "",
        "scheme": "ws",
        "server": ("testserver", 80),
        "subprotocols": [],
        "client": ("testclient", 50000),
        "extensions": {},
    }

    yield SimpleNamespace(
        app=app,
        c2s=c2s,
        s2c=s2c,
        receive=receive,
        send=send,
        ws_scope=ws_scope,
    )

    app.dependency_overrides.pop(get_current_student, None)
    app.dependency_overrides.pop(get_db, None)


def test_check_db(client):
    response = client.get("/check-db")
    assert response.status_code == 200
    data = response.json()
    # Ensure the key 'database_time' exists in the response.
    assert "database_time" in data
    # Optionally, check that the value is not None or matches an expected format
