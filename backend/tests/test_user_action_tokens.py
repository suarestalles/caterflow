
from datetime import UTC, datetime, timedelta

import pytest

from app.models.user_action_token import UserActionToken
from app.services.user_action_tokens import (
    PASSWORD_RESET,
    PLATFORM_INVITATION,
    TENANT_INVITATION,
    InvalidUserActionTokenError,
    InvalidUserActionTokenPurposeError,
    consume_user_action_token,
    create_user_action_token,
    get_valid_user_action_token,
    revoke_tenant_action_tokens,
    revoke_user_action_tokens,
)


def test_create_token_stores_hash_not_raw_token(
    db_session,
    user_factory,
):
    user = user_factory()

    raw_token, token = create_user_action_token(
        db=db_session,
        user_id=user.id,
        purpose=PASSWORD_RESET,
        expires_in=timedelta(minutes=30),
        email=user.email,
    )

    assert raw_token
    assert token.token_hash != raw_token
    assert len(token.token_hash) == 64
    assert token.user_id == user.id
    assert token.email == user.email

    stored = db_session.get(UserActionToken, token.id)
    assert stored.token_hash == token.token_hash


def test_get_valid_token_returns_token_for_correct_purpose(
    db_session,
    user_factory,
):
    user = user_factory()

    raw_token, created = create_user_action_token(
        db=db_session,
        user_id=user.id,
        purpose=PASSWORD_RESET,
        expires_in=timedelta(minutes=30),
        email=user.email,
    )
    db_session.commit()

    token = get_valid_user_action_token(
        db_session,
        raw_token,
        PASSWORD_RESET,
    )

    assert token.id == created.id


def test_get_valid_token_rejects_wrong_purpose(
    db_session,
    user_factory,
):
    user = user_factory()

    raw_token, _ = create_user_action_token(
        db=db_session,
        user_id=user.id,
        purpose=PASSWORD_RESET,
        expires_in=timedelta(minutes=30),
        email=user.email,
    )
    db_session.commit()

    with pytest.raises(InvalidUserActionTokenError):
        get_valid_user_action_token(
            db_session,
            raw_token,
            PLATFORM_INVITATION,
        )


def test_get_valid_token_rejects_unknown_token(db_session):
    with pytest.raises(InvalidUserActionTokenError):
        get_valid_user_action_token(
            db_session,
            "unknown-token",
            PASSWORD_RESET,
        )


def test_get_valid_token_rejects_expired_token(
    db_session,
    user_factory,
):
    user = user_factory()

    raw_token, token = create_user_action_token(
        db=db_session,
        user_id=user.id,
        purpose=PASSWORD_RESET,
        expires_in=timedelta(minutes=30),
        email=user.email,
    )

    token.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.commit()

    with pytest.raises(InvalidUserActionTokenError):
        get_valid_user_action_token(
            db_session,
            raw_token,
            PASSWORD_RESET,
        )


def test_consumed_token_cannot_be_used_again(
    db_session,
    user_factory,
):
    user = user_factory()

    raw_token, token = create_user_action_token(
        db=db_session,
        user_id=user.id,
        purpose=PASSWORD_RESET,
        expires_in=timedelta(minutes=30),
        email=user.email,
    )
    db_session.commit()

    consume_user_action_token(token)
    db_session.commit()

    with pytest.raises(InvalidUserActionTokenError):
        get_valid_user_action_token(
            db_session,
            raw_token,
            PASSWORD_RESET,
        )


def test_revoke_user_tokens(
    db_session,
    user_factory,
):
    user = user_factory()

    raw_token, _ = create_user_action_token(
        db=db_session,
        user_id=user.id,
        purpose=PASSWORD_RESET,
        expires_in=timedelta(minutes=30),
        email=user.email,
    )
    db_session.commit()

    revoked = revoke_user_action_tokens(
        db_session,
        user.id,
    )
    db_session.commit()

    assert revoked == 1

    with pytest.raises(InvalidUserActionTokenError):
        get_valid_user_action_token(
            db_session,
            raw_token,
            PASSWORD_RESET,
        )


def test_revoke_user_tokens_by_purpose(
    db_session,
    user_factory,
):
    user = user_factory()

    reset_token, _ = create_user_action_token(
        db=db_session,
        user_id=user.id,
        purpose=PASSWORD_RESET,
        expires_in=timedelta(minutes=30),
        email=user.email,
    )

    platform_token, _ = create_user_action_token(
        db=db_session,
        user_id=user.id,
        purpose=PLATFORM_INVITATION,
        expires_in=timedelta(hours=72),
        email=user.email,
    )
    db_session.commit()

    revoked = revoke_user_action_tokens(
        db_session,
        user.id,
        PASSWORD_RESET,
    )
    db_session.commit()

    assert revoked == 1

    with pytest.raises(InvalidUserActionTokenError):
        get_valid_user_action_token(
            db_session,
            reset_token,
            PASSWORD_RESET,
        )

    assert get_valid_user_action_token(
        db_session,
        platform_token,
        PLATFORM_INVITATION,
    )


def test_revoke_tenant_tokens(
    db_session,
    tenant_factory,
):
    tenant = tenant_factory()

    raw_token, _ = create_user_action_token(
        db=db_session,
        user_id=None,
        purpose=TENANT_INVITATION,
        expires_in=timedelta(hours=72),
        email="invite@example.com",
        tenant_id=tenant.id,
        role_id=tenant.roles[0].id,
    )
    db_session.commit()

    revoked = revoke_tenant_action_tokens(
        db_session,
        tenant.id,
    )
    db_session.commit()

    assert revoked == 1

    with pytest.raises(InvalidUserActionTokenError):
        get_valid_user_action_token(
            db_session,
            raw_token,
            TENANT_INVITATION,
        )


def test_create_tenant_invitation_requires_tenant_id(db_session):
    with pytest.raises(InvalidUserActionTokenPurposeError):
        create_user_action_token(
            db=db_session,
            user_id=None,
            purpose=TENANT_INVITATION,
            expires_in=timedelta(hours=72),
            email="invite@example.com",
        )


def test_password_reset_rejects_tenant_id(
    db_session,
    user_factory,
    tenant_factory,
):
    user = user_factory()
    tenant = tenant_factory()

    with pytest.raises(InvalidUserActionTokenPurposeError):
        create_user_action_token(
            db=db_session,
            user_id=user.id,
            purpose=PASSWORD_RESET,
            expires_in=timedelta(minutes=30),
            email=user.email,
            tenant_id=tenant.id,
        )


def test_invalid_purpose_is_rejected(db_session, user_factory):
    user = user_factory()

    with pytest.raises(InvalidUserActionTokenPurposeError):
        create_user_action_token(
            db=db_session,
            user_id=user.id,
            purpose="invalid_purpose",
            expires_in=timedelta(minutes=30),
            email=user.email,
        )


def test_non_positive_expiration_is_rejected(
    db_session,
    user_factory,
):
    user = user_factory()

    with pytest.raises(InvalidUserActionTokenPurposeError):
        create_user_action_token(
            db=db_session,
            user_id=user.id,
            purpose=PASSWORD_RESET,
            expires_in=timedelta(seconds=0),
            email=user.email,
        )
