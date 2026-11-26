from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_action_token import UserActionToken


def get_tenant(
    db: Session,
    tenant_id: UUID,
    *,
    for_update: bool = False,
) -> Tenant | None:
    statement = select(Tenant).where(Tenant.id == tenant_id)

    if for_update:
        statement = statement.with_for_update()

    return db.scalar(statement)


def get_role(
    db: Session,
    tenant_id: UUID,
    role_id: UUID,
) -> Role | None:
    return db.scalar(
        select(Role).where(
            Role.id == role_id,
            Role.tenant_id == tenant_id,
        )
    )


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(
        select(User).where(User.email == email)
    )


def get_membership(
    db: Session,
    tenant_id: UUID,
    user_id: UUID,
) -> Membership | None:
    return db.scalar(
        select(Membership).where(
            Membership.tenant_id == tenant_id,
            Membership.user_id == user_id,
        )
    )


def create_user(
    db: Session,
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


def create_membership(
    db: Session,
    tenant_id: UUID,
    user_id: UUID,
    role_id: UUID,
) -> Membership:
    membership = Membership(
        tenant_id=tenant_id,
        user_id=user_id,
    )
    db.add(membership)
    db.flush()

    membership_role = MembershipRole(
        tenant_id=tenant_id,
        membership_id=membership.id,
        role_id=role_id,
    )
    db.add(membership_role)
    db.flush()

    return membership


def revoke_pending_invites(
    db: Session,
    tenant_id: UUID,
    email: str,
    now: datetime,
) -> int:
    result = db.execute(
        update(UserActionToken)
        .where(
            UserActionToken.tenant_id == tenant_id,
            UserActionToken.email == email,
            UserActionToken.purpose == "tenant_invitation",
            UserActionToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    return result.rowcount or 0