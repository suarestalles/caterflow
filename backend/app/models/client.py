
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.tenant_scoped import TenantScoped


class Client(Abstract, TenantScoped):
    __tablename__ = "clients"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_clients_tenant_id_id",
        ),
        CheckConstraint(
            "client_type IN ('individual', 'company')",
            name="client_type",
        ),
        CheckConstraint(
            "email IS NOT NULL OR phone IS NOT NULL",
            name="contact_required",
        ),
    )

    client_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="individual",
        server_default="individual",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    contact_person: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(254),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    address_line: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    address_line_2: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    postal_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    province: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    country: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="ES",
        server_default="ES",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    tenant = relationship(
        "Tenant",
        back_populates="clients",
    )
