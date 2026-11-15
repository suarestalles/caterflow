from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.models.platform_admin import PlatformAdmin
from app.models.user import User


def get_active_user_by_id(
    db: Session,
    user_id: UUID,
) -> User | None:
    return db.scalar(
        select(User).where(
            User.id == user_id,
            User.is_active.is_(True),
        )
    )


def get_active_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    return db.scalar(
        select(User).where(
            User.email == email,
            User.is_active.is_(True),
        )
    )


def get_membership(
    db: Session,
    user_id: UUID,
    tenant_id: UUID,
) -> Membership | None:
    return db.scalar(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.tenant_id == tenant_id,
        )
    )


def get_active_platform_admin(
    db: Session,
    user_id: UUID,
) -> PlatformAdmin | None:
    return db.scalar(
        select(PlatformAdmin).where(
            PlatformAdmin.user_id == user_id,
            PlatformAdmin.revoked_at.is_(None),
        )
    )
