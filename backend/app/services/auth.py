from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories import auth as auth_repository


class InvalidCredentialsError(Exception):
    pass


class TenantAccessDeniedError(Exception):
    pass


class PlatformAccessDeniedError(Exception):
    pass


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    normalized_email = email.strip().lower()

    user = auth_repository.get_active_user_by_email(
        db,
        normalized_email,
    )

    if user is None or not verify_password(
        password,
        user.password_hash,
    ):
        raise InvalidCredentialsError

    return user


def login_tenant(
    db: Session,
    email: str,
    password: str,
    tenant_id: UUID,
) -> str:
    user = authenticate_user(db, email, password)

    membership = auth_repository.get_membership(
        db,
        user.id,
        tenant_id,
    )

    if membership is None:
        raise TenantAccessDeniedError

    return create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant_id),
    )


def login_platform(
    db: Session,
    email: str,
    password: str,
) -> str:
    user = authenticate_user(db, email, password)

    platform_admin = auth_repository.get_active_platform_admin(
        db,
        user.id,
    )

    if platform_admin is None:
        raise PlatformAccessDeniedError

    return create_access_token(subject=str(user.id))
