from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract import Abstract


class Tenant(Abstract):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    roles = relationship(
        "Role",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    memberships = relationship(
        "Membership",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    clients = relationship(
        "Client",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
