
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.payment import Payment
from app.models.tenant_scoped import TenantScoped


class PaymentRefundStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentRefund(Abstract, TenantScoped):
    __tablename__ = "payment_refunds"

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "payment_id"],
            ["payments.tenant_id", "payments.id"],
            name="fk_payment_refunds_tenant_payment",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "financial_adjustment_id"],
            [
                "event_financial_adjustments.tenant_id",
                "event_financial_adjustments.id",
            ],
            name="fk_payment_refunds_tenant_adjustment",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "amount > 0",
            name="payment_refund_amount_positive",
        ),
        CheckConstraint(
            "refund_method IN ('cash', 'card', 'bank_transfer', 'other')",
            name="payment_refund_method_valid",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'cancelled')",
            name="payment_refund_status_valid",
        ),
        CheckConstraint(
            """
            (
                status = 'completed'
                AND refunded_at IS NOT NULL
                AND processed_by_user_id IS NOT NULL
            )
            OR
            (
                status IN ('pending', 'cancelled')
                AND refunded_at IS NULL
                AND processed_by_user_id IS NULL
            )
            """,
            name="payment_refund_processing_valid",
        ),
        Index(
            "ix_payment_refunds_tenant_payment",
            "tenant_id",
            "payment_id",
        ),
        Index(
            "ix_payment_refunds_tenant_refunded_at",
            "tenant_id",
            "refunded_at",
        ),
        Index(
            "ix_payment_refunds_tenant_status",
            "tenant_id",
            "status",
        ),
        Index(
            "ix_payment_refunds_tenant_adjustment",
            "tenant_id",
            "financial_adjustment_id",
        ),
    )

    payment_id: Mapped[UUID] = mapped_column(nullable=False)

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    refunded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    refund_method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default=PaymentRefundStatus.PENDING.value,
        server_default=PaymentRefundStatus.PENDING.value,
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    external_reference: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recorded_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_payment_refunds_recorded_by_user",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    processed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_payment_refunds_processed_by_user",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    financial_adjustment_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
    )

    payment = relationship(
        "Payment",
        back_populates="refunds",
        primaryjoin=lambda: (
            (Payment.id == foreign(PaymentRefund.payment_id))
            & (Payment.tenant_id == PaymentRefund.tenant_id)
        ),
    )

    recorded_by = relationship(
        "User",
        foreign_keys=[recorded_by_user_id],
    )

    processed_by = relationship(
        "User",
        foreign_keys=[processed_by_user_id],
    )

    tenant = relationship(
        "Tenant",
        back_populates="payment_refunds",
        overlaps="refunds",
    )
