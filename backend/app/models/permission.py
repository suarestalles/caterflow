from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract import Abstract


class Permission(Abstract):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role_permissions = relationship(
        "RolePermission",
        back_populates="permission",
        passive_deletes=True,
    )
