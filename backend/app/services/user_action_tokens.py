
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user_action_token import UserActionToken
from app.repositories import user_action_tokens as repository


PLATFORM_INVITATION = "platform_invitation"
TENANT_INVITATION = "tenant_invitation"
PASSWORD_RESET = "password_reset"

VALID_PURPOSES = {
    PLATFORM_INVITATION,
    TENANT_INVITATION,
    PASSWORD_RESET,
}


class InvalidUserActionTokenError(Exception):
    pass


class InvalidUserActionTokenPurposeError(Exception):
    pass


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()


def _generate_raw_token() -> str:
    return secrets.token_urlsafe(64)


def create_user_action_token(
    db: Session,
    user_id: UUID | None,
    purpose: str,
    expires_in: timedelta,
    email: str,
    tenant_id: UUID | None = None,
    role_id: UUID | None = None,
    invited_by_user_id: UUID | None = None,
) -> tuple[str, UserActionToken]:
    if purpose not in VALID_PURPOSES:
        raise InvalidUserActionTokenPurposeError(
            "Invalid token purpose."
        )

    if purpose == TENANT_INVITATION and tenant_id is None:
        raise InvalidUserActionTokenPurposeError(
            "Tenant invitation requires a tenant."
        )

    if purpose != TENANT_INVITATION and tenant_id is not None:
        raise InvalidUserActionTokenPurposeError(
            "This token purpose cannot be associated with a tenant."
        )

    if expires_in.total_seconds() <= 0:
        raise InvalidUserActionTokenPurposeError(
            "Token expiration must be positive."
        )

    raw_token = _generate_raw_token()
    now = datetime.now(UTC)

    token = UserActionToken(
        user_id=user_id,
        email=email,
        tenant_id=tenant_id,
        role_id=role_id,
        invited_by_user_id=invited_by_user_id,
        token_hash=_hash_token(raw_token),
        purpose=purpose,
        expires_at=datetime.now(UTC) + expires_in,
    )

    repository.create_token(db, token)

    return raw_token, token


def get_valid_user_action_token(
    db: Session,
    raw_token: str,
    purpose: str,
) -> UserActionToken:
    if purpose not in VALID_PURPOSES:
        raise InvalidUserActionTokenPurposeError(
            "Invalid token purpose."
        )

    token = repository.get_valid_token(
        db=db,
        token_hash=_hash_token(raw_token),
        purpose=purpose,
        now=datetime.now(UTC),
    )

    if token is None:
        raise InvalidUserActionTokenError(
            "Invalid, expired or already used token."
        )

    return token


def consume_user_action_token(
    token: UserActionToken,
) -> None:
    repository.consume_token(
        token=token,
        now=datetime.now(UTC),
    )


def revoke_user_action_tokens(
    db: Session,
    user_id: UUID,
    purpose: str | None = None,
) -> int:
    if purpose is not None and purpose not in VALID_PURPOSES:
        raise InvalidUserActionTokenPurposeError(
            "Invalid token purpose."
        )

    return repository.revoke_user_tokens(
        db=db,
        user_id=user_id,
        now=datetime.now(UTC),
        purpose=purpose,
    )


def revoke_tenant_action_tokens(
    db: Session,
    tenant_id: UUID,
    purpose: str | None = None,
) -> int:
    if purpose is not None and purpose not in VALID_PURPOSES:
        raise InvalidUserActionTokenPurposeError(
            "Invalid token purpose."
        )

    return repository.revoke_tenant_tokens(
        db=db,
        tenant_id=tenant_id,
        now=datetime.now(UTC),
        purpose=purpose,
    )
