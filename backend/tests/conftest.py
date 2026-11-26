
import pytest
from itertools import count
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.models.membership import Membership
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User


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


@pytest.fixture
def user_factory(db_session):
    """Create users for tests."""
    sequence = count(1)

    def factory(
        full_name="Test User",
        email=None,
        is_active=True,
        password_hash="test-password-hash",
    ):
        index = next(sequence)

        user = User(
            full_name=full_name,
            email=email or f"user{index}@example.com",
            password_hash=password_hash,
            is_active=is_active,
        )

        db_session.add(user)
        db_session.flush()

        return user

    return factory


@pytest.fixture
def tenant_factory(db_session):
    """Create tenants with a default Owner role."""
    sequence = count(1)

    def factory(
        name=None,
        is_active=True,
    ):
        index = next(sequence)

        tenant = Tenant(
            name=name or f"Test Tenant {index}",
            is_active=is_active,
        )

        db_session.add(tenant)
        db_session.flush()

        owner_role = Role(
            tenant_id=tenant.id,
            name="Owner",
            description="Tenant owner",
            is_system=True,
        )

        db_session.add(owner_role)
        db_session.flush()

        return tenant

    return factory


@pytest.fixture
def membership_factory(db_session):
    """Create tenant memberships for tests."""

    def factory(
        tenant,
        user,
    ):
        membership = Membership(
            tenant_id=tenant.id,
            user_id=user.id,
        )

        db_session.add(membership)
        db_session.flush()

        return membership

    return factory
