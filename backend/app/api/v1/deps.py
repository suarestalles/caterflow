from collections.abc import Generator
from dataclasses import dataclass
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.db.tenant_session import TenantSession, get_tenant_db
from app.models.membership import Membership
from app.models.platform_admin import PlatformAdmin
from app.models.user import User
from app.repositories import auth as auth_repository

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    user: User
    tenant_id: UUID


@dataclass(frozen=True)
class PlatformAdminContext:
    user: User
    platform_admin: PlatformAdmin


def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AuthContext:
    """Authenticate the user and validate access to the selected tenant."""

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)

        user_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tenant_id"])

    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise unauthorized from None

    user = db.scalar(
        select(User).where(
            User.id == user_id,
            User.is_active.is_(True),
        )
    )

    if user is None:
        raise unauthorized

    membership = db.scalar(
        select(Membership.id).where(
            Membership.user_id == user_id,
            Membership.tenant_id == tenant_id,
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this tenant.",
        )

    return AuthContext(
        user=user,
        tenant_id=tenant_id,
    )


def get_current_user(
    auth: AuthContext = Depends(get_auth_context),
) -> User:
    """Return the authenticated user."""

    return auth.user


def get_current_tenant_db(
    auth: AuthContext = Depends(get_auth_context),
) -> Generator[TenantSession, None, None]:
    """Provide a database session scoped to the authenticated tenant."""

    yield from get_tenant_db(auth.tenant_id)


def get_current_platform_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> PlatformAdminContext:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)

        # Platform tokens must not contain a tenant context.
        if "tenant_id" in payload:
            raise unauthorized

        user_id = UUID(payload["sub"])

    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise unauthorized from None

    user = auth_repository.get_active_user_by_id(db, user_id)

    if user is None:
        raise unauthorized

    platform_admin = auth_repository.get_active_platform_admin(
        db,
        user.id,
    )

    if platform_admin is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrator access is required.",
        )

    return PlatformAdminContext(
        user=user,
        platform_admin=platform_admin,
    )
