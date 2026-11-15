import uuid

from sqlalchemy import (
    ForeignKey,
    ForeignKeyConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.tenant_scoped import TenantScoped


class RolePermission(Abstract, TenantScoped):
    __tablename__ = "role_permissions"

    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permissions_role_permission",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "role_id"],
            ["roles.tenant_id", "roles.id"],
            name="fk_role_permissions_tenant_role",
            ondelete="CASCADE",
        ),
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    permission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
