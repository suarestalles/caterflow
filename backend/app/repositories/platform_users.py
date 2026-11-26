
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.models.user import User


def list_users(
    db: Session,
    *,
    offset: int,
    limit: int,
    search: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[User], int]:
    statement = select(User)

    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                User.full_name.ilike(term),
                User.email.ilike(term),
            )
        )

    if is_active is not None:
        statement = statement.where(User.is_active.is_(is_active))

    total = db.scalar(
        select(func.count()).select_from(statement.subquery())
    ) or 0

    users = db.scalars(
        statement
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return list(users), total


def get_user(db: Session, user_id: UUID) -> User | None:
    return db.scalar(select(User).where(User.id == user_id))


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    password_hash: str,
) -> User:
    user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user

def set_user_active(
    db: Session,
    user: User,
    is_active: bool,
) -> None:
    user.is_active = is_active

    if not is_active:
        db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )