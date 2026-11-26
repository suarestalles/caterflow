import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.membership import Membership
from app.models.platform_admin import PlatformAdmin
from app.models.refresh_token import RefreshToken
from app.models.user import User


class InvalidRefreshTokenError(Exception):
    pass


class RefreshTokenReuseError(Exception):
    pass


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _generate_token() -> str:
    return secrets.token_urlsafe(64)


def _revoke_family(
    db: Session,
    family_id: UUID,
    now: datetime,
) -> None:
    db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )


def create_refresh_token(
    db: Session,
    user_id: UUID,
    tenant_id: UUID | None,
) -> str:
    raw_token = _generate_token()

    refresh_token = RefreshToken(
        user_id=user_id,
        tenant_id=tenant_id,
        token_hash=_hash_token(raw_token),
        family_id=uuid4(),
        expires_at=datetime.now(UTC)
        + timedelta(days=settings.refresh_token_expire_days),
    )

    db.add(refresh_token)
    db.commit()

    return raw_token


def rotate_refresh_token(
    db: Session,
    raw_token: str,
) -> tuple[str, str]:
    now = datetime.now(UTC)

    stored_token = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == _hash_token(raw_token))
        .with_for_update()
    )

    if stored_token is None:
        raise InvalidRefreshTokenError

    if stored_token.revoked_at is not None:
        if stored_token.replaced_by_token_id is not None:
            _revoke_family(db, stored_token.family_id, now)
            db.commit()
            raise RefreshTokenReuseError

        raise InvalidRefreshTokenError

    if stored_token.expires_at <= now:
        stored_token.revoked_at = now
        db.commit()
        raise InvalidRefreshTokenError

    user = db.scalar(
        select(User).where(
            User.id == stored_token.user_id,
            User.is_active.is_(True),
        )
    )

    if user is None:
        _revoke_family(db, stored_token.family_id, now)
        db.commit()
        raise InvalidRefreshTokenError

    tenant_id = stored_token.tenant_id

    if tenant_id is not None:
        membership = db.scalar(
            select(Membership.id).where(
                Membership.user_id == user.id,
                Membership.tenant_id == tenant_id,
            )
        )

        if membership is None:
            _revoke_family(db, stored_token.family_id, now)
            db.commit()
            raise InvalidRefreshTokenError

    else:
        platform_admin = db.scalar(
            select(PlatformAdmin.id).where(
                PlatformAdmin.user_id == user.id,
                PlatformAdmin.revoked_at.is_(None),
            )
        )

        if platform_admin is None:
            _revoke_family(db, stored_token.family_id, now)
            db.commit()
            raise InvalidRefreshTokenError

    new_raw_token = _generate_token()

    new_token = RefreshToken(
        user_id=user.id,
        tenant_id=tenant_id,
        token_hash=_hash_token(new_raw_token),
        family_id=stored_token.family_id,
        expires_at=now
        + timedelta(days=settings.refresh_token_expire_days),
    )

    db.add(new_token)
    db.flush()

    stored_token.revoked_at = now
    stored_token.replaced_by_token_id = new_token.id

    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant_id) if tenant_id is not None else None,
    )

    db.commit()

    return access_token, new_raw_token


def revoke_refresh_token(
    db: Session,
    raw_token: str,
) -> None:
    now = datetime.now(UTC)

    stored_token = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == _hash_token(raw_token))
        .with_for_update()
    )

    if stored_token is None:
        return

    _revoke_family(db, stored_token.family_id, now)
    db.commit()