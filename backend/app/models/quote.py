from datetime import date
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKeyConstraint,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.tenant_scoped import TenantScoped


class QuoteStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Quote(Abstract, TenantScoped):
    __tablename__ = "quotes"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_quotes_tenant_id_id",
        ),
        UniqueConstraint(
            "tenant_id",
            "quote_number",
            name="uq_quotes_tenant_number",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "client_id"],
            ["clients.tenant_id", "clients.id"],
            name="fk_quotes_tenant_client",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "event_id"],
            ["events.tenant_id", "events.id"],
            name="fk_quotes_tenant_event",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status IN ('draft', 'sent', 'accepted', 'rejected', 'expired', 'cancelled')",
            name="quote_status",
        ),
        CheckConstraint("subtotal >= 0", name="quote_subtotal_nonnegative"),
        CheckConstraint(
            "discount_amount >= 0",
            name="quote_discount_nonnegative",
        ),
        CheckConstraint("tax_amount >= 0", name="quote_tax_nonnegative"),
        CheckConstraint("total_amount >= 0", name="quote_total_nonnegative"),
    )

    client_id: Mapped[UUID] = mapped_column(nullable=False)
    event_id: Mapped[UUID | None] = mapped_column(nullable=True)

    quote_number: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20),
        default=QuoteStatus.DRAFT.value,
        server_default=QuoteStatus.DRAFT.value,
        nullable=False,
    )

    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        server_default="0",
        nullable=False,
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        server_default="0",
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        server_default="0",
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        server_default="0",
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    terms: Mapped[str | None] = mapped_column(Text, nullable=True)

    client = relationship(
        "Client",
        back_populates="quotes",
        primaryjoin=lambda: (
            (Client.id == foreign(Quote.client_id))
            & (Client.tenant_id == Quote.tenant_id)
        ),
    )

    event = relationship(
        "Event",
        back_populates="quotes",
        primaryjoin=lambda: (
            (Event.id == foreign(Quote.event_id))
            & (Event.tenant_id == Quote.tenant_id)
        ),
    )

    tenant = relationship("Tenant", back_populates="quotes")

    items = relationship(
        "QuoteItem",
        back_populates="quote",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    payment_schedule = relationship(
        "PaymentSchedule",
        back_populates="quote",
        uselist=False,
        overlaps="payment_schedule",
    )


# Imports used by relationship joins
from app.models.client import Client
from app.models.event import Event
