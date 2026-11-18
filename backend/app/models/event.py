from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    and_,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.client import Client
from app.models.tenant_scoped import TenantScoped


class EventStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Event(Abstract, TenantScoped):
    __tablename__ = "events"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_events_tenant_id_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id"],
            ["clients.tenant_id", "clients.id"],
            name="fk_events_tenant_client",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status IN ('draft', 'confirmed', 'in_progress', 'completed', 'cancelled')",
            name="event_status",
        ),
        CheckConstraint(
            "guest_count > 0",
            name="guest_count_positive",
        ),
        CheckConstraint(
            "starts_at < ends_at",
            name="event_date_range",
        ),
    )

    client_id: Mapped[UUID] = mapped_column(nullable=False)

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    guest_count: Mapped[int] = mapped_column(nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default=EventStatus.DRAFT.value,
        server_default=EventStatus.DRAFT.value,
        nullable=False,
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
        default="ES",
        server_default="ES",
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    client = relationship(
        "Client",
        back_populates="events",
        primaryjoin=lambda: and_(
            Client.id == foreign(Event.client_id),
            Client.tenant_id == Event.tenant_id,
        ),
    )

    tenant = relationship(
        "Tenant",
        back_populates="events",
    )

    quotes = relationship(
        "Quote",
        back_populates="event",
        primaryjoin="and_(Event.id == foreign(Quote.event_id), Event.tenant_id == Quote.tenant_id)",
    )