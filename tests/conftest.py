import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main


# One engine for the test session; in-memory + StaticPool so it persists
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


@pytest.fixture(scope="session", autouse=True)
def _override_dependency() -> None:
    # Swap the app's DB dependency to our test session; keep prod DB untouched
    def _get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[main.get_db] = _get_db
    yield
    main.app.dependency_overrides.clear()


@pytest.fixture()
def client():
    # Fresh tables each test — clean slate, calm mind
    main.Base.metadata.drop_all(bind=test_engine)
    main.Base.metadata.create_all(bind=test_engine)
    with TestClient(main.app) as c:
        yield c


