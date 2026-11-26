
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.tenant_session import TenantSession
from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User


def get_membership(db: Session, tenant_id: UUID, membership_id: UUID):
    return db.scalar(
        select(Membership).where(
            Membership.id == membership_id,
            Membership.tenant_id == tenant_id,
        )
    )


def get_existing_membership(
    db: Session,
    tenant_id: UUID,
    user_id: UUID,
):
    return db.scalar(
        select(Membership).where(
            Membership.tenant_id == tenant_id,
            Membership.user_id == user_id,
        )
    )


def get_user(db: Session, user_id: UUID):
    return db.scalar(select(User).where(User.id == user_id))


def get_role(db: Session, tenant_id: UUID, role_id: UUID):
    return db.scalar(
        select(Role).where(
            Role.id == role_id,
            Role.tenant_id == tenant_id,
        )
    )


def list_memberships(
    db: Session,
    tenant_id: UUID,
    *,
    offset: int,
    limit: int,
):
    statement = (
        select(Membership, User, Role)
        .join(User, User.id == Membership.user_id)
        .join(
            MembershipRole,
            (MembershipRole.membership_id == Membership.id)
            & (MembershipRole.tenant_id == tenant_id),
        )
        .join(
            Role,
            (Role.id == MembershipRole.role_id)
            & (Role.tenant_id == tenant_id),
        )
        .where(Membership.tenant_id == tenant_id)
    )

    total = db.scalar(
        select(func.count()).select_from(
            statement.with_only_columns(Membership.id).subquery()
        )
    ) or 0

    rows = db.execute(
        statement
        .order_by(User.full_name)
        .offset(offset)
        .limit(limit)
    ).all()

    return rows, total


def get_membership_details(
    db: Session,
    tenant_id: UUID,
    membership_id: UUID,
):
    statement = (
        select(Membership, User, Role)
        .join(User, User.id == Membership.user_id)
        .join(
            MembershipRole,
            (MembershipRole.membership_id == Membership.id)
            & (MembershipRole.tenant_id == tenant_id),
        )
        .join(
            Role,
            (Role.id == MembershipRole.role_id)
            & (Role.tenant_id == tenant_id),
        )
        .where(
            Membership.id == membership_id,
            Membership.tenant_id == tenant_id,
        )
    )

    return db.execute(statement).first()


def get_membership_role(
    db: Session,
    tenant_id: UUID,
    membership_id: UUID,
):
    return db.scalar(
        select(MembershipRole).where(
            MembershipRole.tenant_id == tenant_id,
            MembershipRole.membership_id == membership_id,
        )
    )


def count_other_owners(
    db: Session,
    tenant_id: UUID,
    excluded_membership_id: UUID,
) -> int:
    statement = (
        select(func.count())
        .select_from(MembershipRole)
        .join(Role, Role.id == MembershipRole.role_id)
        .where(
            MembershipRole.tenant_id == tenant_id,
            Role.tenant_id == tenant_id,
            Role.name == "Owner",
            MembershipRole.membership_id != excluded_membership_id,
        )
    )

    return db.scalar(statement) or 0

def get_tenant(db: TenantSession, tenant_id: UUID) -> Tenant | None:
    return db.scalar(
        select(Tenant).where(Tenant.id == tenant_id)
    )


def list_tenant_roles(db: TenantSession, tenant_id: UUID) -> list[Role]:
    return db.scalars(
        select(Role)
        .where(Role.tenant_id == tenant_id)
        .order_by(Role.name)
    ).all()