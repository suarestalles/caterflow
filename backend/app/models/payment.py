
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.payment_installment import PaymentInstallment
from app.models.tenant_scoped import TenantScoped


class PaymentMethod(StrEnum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    OTHER = "other"


class Payment(Abstract, TenantScoped):
    __tablename__ = "payments"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_payments_tenant_id_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "installment_id"],
            [
                "payment_installments.tenant_id",
                "payment_installments.id",
            ],
            name="fk_payments_tenant_installment",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "amount > 0",
            name="payment_amount_positive",
        ),
        CheckConstraint(
            "payment_method IN ('cash', 'card', 'bank_transfer', 'other')",
            name="payment_method_valid",
        ),
        Index(
            "ix_payments_tenant_installment",
            "tenant_id",
            "installment_id",
        ),
        Index(
            "ix_payments_tenant_received_at",
            "tenant_id",
            "received_at",
        ),
    )

    installment_id: Mapped[UUID] = mapped_column(nullable=False)

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    payment_method: Mapped[str] = mapped_column(
        String(20),
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
            name="fk_payments_recorded_by_user",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    installment = relationship(
        "PaymentInstallment",
        back_populates="payments",
        primaryjoin=lambda: (
            (PaymentInstallment.id == foreign(Payment.installment_id))
            & (PaymentInstallment.tenant_id == Payment.tenant_id)
        ),
    )

    recorded_by = relationship("User")

    tenant = relationship(
        "Tenant",
        back_populates="payments",
        overlaps="payments",
    )

    refunds = relationship(
        "PaymentRefund",
        back_populates="payment",
        passive_deletes=True,
    )
