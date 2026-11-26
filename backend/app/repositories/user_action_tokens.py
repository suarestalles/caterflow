
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.user_action_token import UserActionToken


def create_token(
    db: Session,
    token: UserActionToken,
) -> UserActionToken:
    db.add(token)
    db.flush()
    return token


def get_valid_token(
    db: Session,
    token_hash: str,
    purpose: str,
    now: datetime,
) -> UserActionToken | None:
    return db.scalar(
        select(UserActionToken)
        .where(
            UserActionToken.token_hash == token_hash,
            UserActionToken.purpose == purpose,
            UserActionToken.used_at.is_(None),
            UserActionToken.expires_at > now,
        )
        .with_for_update()
    )


def consume_token(
    token: UserActionToken,
    now: datetime,
) -> None:
    token.used_at = now


def revoke_user_tokens(
    db: Session,
    user_id: UUID,
    now: datetime,
    purpose: str | None = None,
) -> int:
    statement = (
        update(UserActionToken)
        .where(
            UserActionToken.user_id == user_id,
            UserActionToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    if purpose is not None:
        statement = statement.where(
            UserActionToken.purpose == purpose
        )

    result = db.execute(statement)
    return result.rowcount or 0


def revoke_tenant_tokens(
    db: Session,
    tenant_id: UUID,
    now: datetime,
    purpose: str | None = None,
) -> int:
    statement = (
        update(UserActionToken)
        .where(
            UserActionToken.tenant_id == tenant_id,
            UserActionToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    if purpose is not None:
        statement = statement.where(
            UserActionToken.purpose == purpose
        )

    result = db.execute(statement)
    return result.rowcount or 0
