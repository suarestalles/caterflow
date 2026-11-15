import uuid

from sqlalchemy import ForeignKeyConstraint, Index, UniqueConstraint, and_
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.membership import Membership
from app.models.role import Role
from app.models.tenant_scoped import TenantScoped


class MembershipRole(Abstract, TenantScoped):
    __tablename__ = "membership_roles"

    __table_args__ = (
        UniqueConstraint(
            "membership_id",
            "role_id",
            name="uq_membership_roles_membership_role",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
            name="fk_membership_roles_tenant_membership",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "role_id"],
            ["roles.tenant_id", "roles.id"],
            name="fk_membership_roles_tenant_role",
            ondelete="CASCADE",
        ),
        Index(
            "ix_membership_roles_tenant_membership",
            "tenant_id",
            "membership_id",
        ),
        Index(
            "ix_membership_roles_tenant_role",
            "tenant_id",
            "role_id",
        ),
    )

    membership_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    membership = relationship(
        Membership,
        back_populates="membership_roles",
        primaryjoin=lambda: and_(
            Membership.tenant_id == MembershipRole.tenant_id,
            Membership.id == foreign(MembershipRole.membership_id),
        ),
    )

    role = relationship(
        Role,
        back_populates="membership_roles",
        primaryjoin=lambda: and_(
            Role.tenant_id == MembershipRole.tenant_id,
            Role.id == foreign(MembershipRole.role_id),
        ),
    )
