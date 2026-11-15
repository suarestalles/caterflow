import uuid

from sqlalchemy import ForeignKey, UniqueConstraint, and_
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.tenant_scoped import TenantScoped


class Membership(Abstract, TenantScoped):
    __tablename__ = "memberships"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "user_id",
            name="uq_memberships_tenant_user",
        ),
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_memberships_tenant_id_id",
        ),
    )

    def _membership_roles_join():
        from app.models.membership_role import MembershipRole

        return and_(
            Membership.tenant_id == MembershipRole.tenant_id,
            Membership.id == foreign(MembershipRole.membership_id),
        )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    membership_roles = relationship(
        "MembershipRole",
        back_populates="membership",
        cascade="all, delete-orphan",
        primaryjoin=_membership_roles_join,
        passive_deletes=True,
    )

    tenant = relationship("Tenant", back_populates="memberships")
    user = relationship("User", back_populates="memberships")
