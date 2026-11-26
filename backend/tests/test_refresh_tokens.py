
from datetime import UTC, datetime, timedelta

import pytest

from app.core.security import decode_access_token
from app.models.membership import Membership
from app.models.platform_admin import PlatformAdmin
from app.models.refresh_token import RefreshToken
from app.models.tenant import Tenant
from app.models.user import User
from app.services.refresh_tokens import (
    InvalidRefreshTokenError,
    RefreshTokenReuseError,
    create_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)


def create_user(db_session, email="refresh@example.com", active=True):
    user = User(
        full_name="Refresh Test User",
        email=email,
        password_hash="test-password-hash",
        is_active=active,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_tenant_session(db_session):
    user = create_user(db_session)
    tenant = Tenant(name="Refresh Test Tenant")
    db_session.add(tenant)
    db_session.flush()

    db_session.add(
        Membership(
            user_id=user.id,
            tenant_id=tenant.id,
        )
    )
    db_session.flush()

    raw_token = create_refresh_token(
        db_session,
        user_id=user.id,
        tenant_id=tenant.id,
    )

    return user, tenant, raw_token


def test_rotate_refresh_token_success(db_session):
    user, tenant, old_token = create_tenant_session(db_session)

    access_token, new_token = rotate_refresh_token(
        db_session,
        old_token,
    )

    payload = decode_access_token(access_token)

    assert payload["sub"] == str(user.id)
    assert payload["tenant_id"] == str(tenant.id)
    assert new_token != old_token

    new_access_token, another_token = rotate_refresh_token(
        db_session,
        new_token,
    )

    assert decode_access_token(new_access_token)["sub"] == str(user.id)
    assert another_token != new_token


def test_reusing_rotated_token_revokes_entire_family(db_session):
    _, _, old_token = create_tenant_session(db_session)

    _, new_token = rotate_refresh_token(db_session, old_token)

    with pytest.raises(RefreshTokenReuseError):
        rotate_refresh_token(db_session, old_token)

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(db_session, new_token)


def test_logout_revokes_entire_family(db_session):
    _, _, old_token = create_tenant_session(db_session)

    _, new_token = rotate_refresh_token(db_session, old_token)

    revoke_refresh_token(db_session, new_token)

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(db_session, new_token)


def test_platform_refresh_preserves_platform_context(db_session):
    user = create_user(db_session)

    db_session.add(PlatformAdmin(user_id=user.id))
    db_session.flush()

    raw_token = create_refresh_token(
        db_session,
        user_id=user.id,
        tenant_id=None,
    )

    access_token, new_token = rotate_refresh_token(
        db_session,
        raw_token,
    )

    payload = decode_access_token(access_token)

    assert payload["sub"] == str(user.id)
    assert "tenant_id" not in payload
    assert new_token != raw_token


def test_refresh_rejects_inactive_user(db_session):
    user, _, raw_token = create_tenant_session(db_session)
    user.is_active = False
    db_session.flush()

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(db_session, raw_token)


def test_refresh_rejects_removed_tenant_membership(db_session):
    user, tenant, raw_token = create_tenant_session(db_session)

    membership = db_session.query(Membership).filter_by(
        user_id=user.id,
        tenant_id=tenant.id,
    ).one()

    db_session.delete(membership)
    db_session.flush()

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(db_session, raw_token)


def test_refresh_rejects_revoked_platform_admin(db_session):
    user = create_user(db_session)

    admin = PlatformAdmin(user_id=user.id)
    db_session.add(admin)
    db_session.flush()

    raw_token = create_refresh_token(
        db_session,
        user_id=user.id,
        tenant_id=None,
    )

    admin.revoked_at = datetime.now(UTC)
    db_session.flush()

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(db_session, raw_token)


def test_refresh_rejects_expired_token(db_session):
    _, _, raw_token = create_tenant_session(db_session)

    stored_token = db_session.query(RefreshToken).filter_by(
        token_hash=__import__("hashlib").sha256(
            raw_token.encode("utf-8")
        ).hexdigest()
    ).one()

    stored_token.expires_at = datetime.now(UTC) - timedelta(days=1)
    db_session.flush()

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(db_session, raw_token)
