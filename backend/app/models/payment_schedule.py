
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.event import Event
from app.models.quote import Quote
from app.models.tenant_scoped import TenantScoped


class PaymentScheduleStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


class PaymentSchedule(Abstract, TenantScoped):
    __tablename__ = "payment_schedules"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_payment_schedules_tenant_id_id",
        ),
        UniqueConstraint(
            "tenant_id",
            "event_id",
            name="uq_payment_schedules_tenant_event",
        ),
        UniqueConstraint(
            "tenant_id",
            "quote_id",
            name="uq_payment_schedules_tenant_quote",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "event_id"],
            ["events.tenant_id", "events.id"],
            name="fk_payment_schedules_tenant_event",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "quote_id"],
            ["quotes.tenant_id", "quotes.id"],
            name="fk_payment_schedules_tenant_quote",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "total_amount > 0",
            name="payment_schedule_total_positive",
        ),
        CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name="payment_schedule_currency_valid",
        ),
        CheckConstraint(
            "status IN ('active', 'cancelled')",
            name="payment_schedule_status",
        ),
    )

    event_id: Mapped[UUID] = mapped_column(nullable=False)

    quote_id: Mapped[UUID] = mapped_column(nullable=False)

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="EUR",
        server_default="EUR",
        nullable=False,
    )

    payment_terms_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default=PaymentScheduleStatus.ACTIVE.value,
        server_default=PaymentScheduleStatus.ACTIVE.value,
        nullable=False,
    )

    event = relationship(
        "Event",
        back_populates="payment_schedule",
        primaryjoin=lambda: (
            (Event.id == foreign(PaymentSchedule.event_id))
            & (Event.tenant_id == PaymentSchedule.tenant_id)
        ),
        overlaps="payment_schedule",
    )

    quote = relationship(
        "Quote",
        back_populates="payment_schedule",
        primaryjoin=lambda: (
            (Quote.id == foreign(PaymentSchedule.quote_id))
            & (Quote.tenant_id == PaymentSchedule.tenant_id)
        ),
        overlaps="payment_schedule",
    )

    tenant = relationship(
        "Tenant",
        back_populates="payment_schedules",
        overlaps="payment_schedule",
    )

    installments = relationship(
        "PaymentInstallment",
        back_populates="payment_schedule",
        passive_deletes=True,
        order_by="PaymentInstallment.installment_number",
        overlaps="tenant",
    )
