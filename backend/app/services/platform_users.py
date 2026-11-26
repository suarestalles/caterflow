
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories import platform_users as repository


class PlatformUserNotFoundError(Exception):
    pass


class PlatformUserAlreadyExistsError(Exception):
    pass

class PlatformUserValidationError(Exception):
    pass


def list_users(
    db: Session,
    *,
    offset: int,
    limit: int,
    search: str | None = None,
    is_active: bool | None = None,
):
    return repository.list_users(
        db,
        offset=offset,
        limit=limit,
        search=search,
        is_active=is_active,
    )


def get_user(db: Session, user_id: UUID) -> User:
    user = repository.get_user(db, user_id)

    if user is None:
        raise PlatformUserNotFoundError

    return user


def create_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    password: str,
) -> User:
    normalized_email = email.strip().lower()

    if repository.get_user_by_email(db, normalized_email):
        raise PlatformUserAlreadyExistsError

    user = repository.create_user(
        db,
        full_name=full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
    )

    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise PlatformUserAlreadyExistsError from None
    except Exception:
        db.rollback()
        raise

def activate_user(
    db: Session,
    user_id: UUID,
) -> User:
    user = repository.get_user(db, user_id)

    if user is None:
        raise PlatformUserNotFoundError

    if user.is_active:
        return user

    repository.set_user_active(db, user, True)

    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise


def deactivate_user(
    db: Session,
    user_id: UUID,
    current_admin_id: UUID,
) -> User:
    if user_id == current_admin_id:
        raise PlatformUserValidationError(
            "You cannot deactivate your own account."
        )

    user = repository.get_user(db, user_id)

    if user is None:
        raise PlatformUserNotFoundError

    if not user.is_active:
        return user

    repository.set_user_active(db, user, False)

    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise