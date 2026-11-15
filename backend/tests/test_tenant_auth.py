import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.v1.deps import get_auth_context
from app.core.security import create_access_token
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.user import User


def create_user(db_session, email, is_active=True):
    user = User(
        full_name="Test User",
        email=email,
        password_hash="test-password-hash",
        is_active=is_active,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_credentials(user_id, tenant_id=None):
    token = create_access_token(
        subject=str(user_id),
        tenant_id=str(tenant_id) if tenant_id else None,
    )

    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


def test_auth_context_accepts_valid_tenant_membership(db_session):
    tenant = Tenant(name="Auth Tenant")
    db_session.add(tenant)
    db_session.flush()

    user = create_user(db_session, "auth-valid@example.com")

    membership = Membership(
        user_id=user.id,
        tenant_id=tenant.id,
    )
    db_session.add(membership)
    db_session.flush()

    credentials = create_credentials(user.id, tenant.id)

    auth = get_auth_context(
        credentials=credentials,
        db=db_session,
    )

    assert auth.user.id == user.id
    assert auth.tenant_id == tenant.id


def test_auth_context_rejects_token_without_tenant(db_session):
    user = create_user(db_session, "auth-no-tenant@example.com")
    credentials = create_credentials(user.id)

    with pytest.raises(HTTPException) as exc:
        get_auth_context(
            credentials=credentials,
            db=db_session,
        )

    assert exc.value.status_code == 401


def test_auth_context_rejects_unassociated_tenant(db_session):
    tenant = Tenant(name="Unauthorized Tenant")
    db_session.add(tenant)
    db_session.flush()

    user = create_user(db_session, "auth-unauthorized@example.com")
    credentials = create_credentials(user.id, tenant.id)

    with pytest.raises(HTTPException) as exc:
        get_auth_context(
            credentials=credentials,
            db=db_session,
        )

    assert exc.value.status_code == 403


def test_auth_context_rejects_inactive_user(db_session):
    tenant = Tenant(name="Inactive User Tenant")
    db_session.add(tenant)
    db_session.flush()

    user = create_user(
        db_session,
        "auth-inactive@example.com",
        is_active=False,
    )

    db_session.add(
        Membership(
            user_id=user.id,
            tenant_id=tenant.id,
        )
    )
    db_session.flush()

    credentials = create_credentials(user.id, tenant.id)

    with pytest.raises(HTTPException) as exc:
        get_auth_context(
            credentials=credentials,
            db=db_session,
        )

    assert exc.value.status_code == 401
