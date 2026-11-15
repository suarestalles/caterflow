import pytest

from app.core.security import decode_access_token, hash_password
from app.models.membership import Membership
from app.models.platform_admin import PlatformAdmin
from app.models.tenant import Tenant
from app.models.user import User
from app.services.auth import (
    InvalidCredentialsError,
    PlatformAccessDeniedError,
    TenantAccessDeniedError,
    login_platform,
    login_tenant,
)


def create_user(db_session, email="admin2@caterflow.com", active=True):
    user = User(
        full_name="Test Administrator",
        email=email,
        password_hash=hash_password("StrongPassword123!"),
        is_active=active,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_tenant(db_session, name="Test Tenant"):
    tenant = Tenant(name=name)
    db_session.add(tenant)
    db_session.flush()
    return tenant


def test_login_tenant_success(db_session):
    user = create_user(db_session)
    tenant = create_tenant(db_session)

    membership = Membership(
        user_id=user.id,
        tenant_id=tenant.id,
    )
    db_session.add(membership)
    db_session.flush()

    token = login_tenant(
        db_session,
        "admin2@caterflow.com",
        "StrongPassword123!",
        tenant.id,
    )

    payload = decode_access_token(token)

    assert payload["sub"] == str(user.id)
    assert payload["tenant_id"] == str(tenant.id)
    assert payload["type"] == "access"


def test_login_tenant_invalid_password(db_session):
    user = create_user(db_session)
    tenant = create_tenant(db_session)

    db_session.add(
        Membership(
            user_id=user.id,
            tenant_id=tenant.id,
        )
    )
    db_session.flush()

    with pytest.raises(InvalidCredentialsError):
        login_tenant(
            db_session,
            "admin2@caterflow.com",
            "WrongPassword123!",
            tenant.id,
        )


def test_login_tenant_without_membership(db_session):
    create_user(db_session)
    tenant = create_tenant(db_session)

    with pytest.raises(TenantAccessDeniedError):
        login_tenant(
            db_session,
            "admin2@caterflow.com",
            "StrongPassword123!",
            tenant.id,
        )


def test_login_platform_success(db_session):
    user = create_user(db_session)

    db_session.add(PlatformAdmin(user_id=user.id))
    db_session.flush()

    token = login_platform(
        db_session,
        "admin2@caterflow.com",
        "StrongPassword123!",
    )

    payload = decode_access_token(token)

    assert payload["sub"] == str(user.id)
    assert payload["type"] == "access"
    assert "tenant_id" not in payload


def test_login_platform_without_admin_access(db_session):
    create_user(db_session)

    with pytest.raises(PlatformAccessDeniedError):
        login_platform(
            db_session,
            "admin2@caterflow.com",
            "StrongPassword123!",
        )


def test_login_platform_revoked_admin(db_session):
    user = create_user(db_session)

    db_session.add(
        PlatformAdmin(
            user_id=user.id,
            revoked_at=None,
        )
    )
    db_session.flush()

    platform_admin = db_session.query(PlatformAdmin).filter_by(user_id=user.id).one()

    from datetime import UTC, datetime

    platform_admin.revoked_at = datetime.now(UTC)
    db_session.flush()

    with pytest.raises(PlatformAccessDeniedError):
        login_platform(
            db_session,
            "admin2@caterflow.com",
            "StrongPassword123!",
        )


def test_login_platform_invalid_password(db_session):
    user = create_user(db_session)

    db_session.add(PlatformAdmin(user_id=user.id))
    db_session.flush()

    with pytest.raises(InvalidCredentialsError):
        login_platform(
            db_session,
            "admin2@caterflow.com",
            "WrongPassword123!",
        )
