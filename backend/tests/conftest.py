import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create an engine exclusively for the test database."""
    if not settings.test_database_url:
        pytest.fail("TEST_DATABASE_URL must be configured.")

    database_url = make_url(settings.test_database_url)

    if database_url.database != "caterflow_test":
        pytest.fail(
            "Tests can only run against the 'caterflow_test' database. "
            f"Configured database: {database_url.database!r}"
        )

    engine = create_engine(
        settings.test_database_url,
        pool_pre_ping=True,
    )

    Base.metadata.create_all(bind=engine)

    yield engine

    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """Provide a test session isolated by an external transaction."""
    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
