from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.v1.deps import (
    get_auth_context,
    get_current_platform_admin,
)
from app.core.security import create_access_token, hash_password
from app.models.platform_admin import PlatformAdmin
from app.models.tenant import Tenant
from app.models.user import User


def create_user(db_session):
    user = User(
        full_name="Platform Administrator",
        email="platform@caterflow.com",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_credentials(token):
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


def test_platform_admin_token_is_accepted(db_session):
    user = create_user(db_session)

    platform_admin = PlatformAdmin(user_id=user.id)
    db_session.add(platform_admin)
    db_session.flush()

    token = create_access_token(subject=str(user.id))

    context = get_current_platform_admin(
        credentials=create_credentials(token),
        db=db_session,
    )

    assert context.user.id == user.id
    assert context.platform_admin.id == platform_admin.id


def test_tenant_token_is_rejected_by_platform_dependency(db_session):
    user = create_user(db_session)

    db_session.add(PlatformAdmin(user_id=user.id))
    db_session.flush()

    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.flush()

    token = create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_platform_admin(
            credentials=create_credentials(token),
            db=db_session,
        )

    assert exc_info.value.status_code == 401


def test_platform_token_is_rejected_by_tenant_dependency(db_session):
    user = create_user(db_session)
    db_session.add(PlatformAdmin(user_id=user.id))
    db_session.flush()

    token = create_access_token(subject=str(user.id))

    with pytest.raises(HTTPException) as exc_info:
        get_auth_context(
            credentials=create_credentials(token),
            db=db_session,
        )

    assert exc_info.value.status_code == 401


def test_revoked_platform_admin_is_rejected(db_session):
    user = create_user(db_session)

    platform_admin = PlatformAdmin(
        user_id=user.id,
        revoked_at=datetime.now(UTC),
    )
    db_session.add(platform_admin)
    db_session.flush()

    token = create_access_token(subject=str(user.id))

    with pytest.raises(HTTPException) as exc_info:
        get_current_platform_admin(
            credentials=create_credentials(token),
            db=db_session,
        )

    assert exc_info.value.status_code == 403


def test_inactive_platform_user_is_rejected(db_session):
    user = create_user(db_session)
    user.is_active = False

    db_session.add(PlatformAdmin(user_id=user.id))
    db_session.flush()

    token = create_access_token(subject=str(user.id))

    with pytest.raises(HTTPException) as exc_info:
        get_current_platform_admin(
            credentials=create_credentials(token),
            db=db_session,
        )

    assert exc_info.value.status_code == 401
