import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, and_
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.abstract import Abstract


class Role(Abstract):
    __tablename__ = "roles"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "name",
            name="uq_roles_tenant_name",
        ),
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_roles_tenant_id_id",
        ),
    )

    def _membership_roles_join():
        from app.models.membership_role import MembershipRole

        return and_(
            Role.tenant_id == MembershipRole.tenant_id,
            Role.id == foreign(MembershipRole.role_id),
        )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    tenant = relationship("Tenant", back_populates="roles")

    role_permissions = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    membership_roles = relationship(
        "MembershipRole",
        back_populates="role",
        cascade="all, delete-orphan",
        passive_deletes=True,
        primaryjoin=_membership_roles_join,
    )
