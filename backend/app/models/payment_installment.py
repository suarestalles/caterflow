
from datetime import date
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.payment_schedule import PaymentSchedule
from app.models.tenant_scoped import TenantScoped


class InstallmentType(StrEnum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class InstallmentStatus(StrEnum):
    PENDING = "pending"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentInstallment(Abstract, TenantScoped):
    __tablename__ = "payment_installments"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_payment_installments_tenant_id_id",
        ),
        UniqueConstraint(
            "tenant_id",
            "payment_schedule_id",
            "installment_number",
            name="uq_payment_installments_schedule_number",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "payment_schedule_id"],
            ["payment_schedules.tenant_id", "payment_schedules.id"],
            name="fk_payment_installments_tenant_schedule",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "installment_number > 0",
            name="payment_installment_number_positive",
        ),
        CheckConstraint(
            "amount > 0",
            name="payment_installment_amount_positive",
        ),
        CheckConstraint(
            "installment_type IN ('percentage', 'fixed')",
            name="payment_installment_type",
        ),
        CheckConstraint(
            """
            (
                installment_type = 'percentage'
                AND percentage IS NOT NULL
                AND percentage > 0
                AND percentage <= 100
            )
            OR
            (
                installment_type = 'fixed'
                AND percentage IS NULL
            )
            """,
            name="payment_installment_percentage_valid",
        ),
        CheckConstraint(
            "status IN ('pending', 'partially_paid', 'paid', 'cancelled')",
            name="payment_installment_status",
        ),
        Index(
            "ix_payment_installments_tenant_schedule_due_date",
            "tenant_id",
            "payment_schedule_id",
            "due_date",
        ),
    )

    payment_schedule_id: Mapped[UUID] = mapped_column(nullable=False)

    installment_number: Mapped[int] = mapped_column(nullable=False)

    installment_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default=InstallmentStatus.PENDING.value,
        server_default=InstallmentStatus.PENDING.value,
        nullable=False,
    )

    payment_schedule = relationship(
        "PaymentSchedule",
        back_populates="installments",
        primaryjoin=lambda: (
            (PaymentSchedule.id == foreign(PaymentInstallment.payment_schedule_id))
            & (PaymentSchedule.tenant_id == PaymentInstallment.tenant_id)
        ),
    )

    tenant = relationship(
        "Tenant",
        back_populates="payment_installments",
    )

    payments = relationship(
        "Payment",
        back_populates="installment",
        passive_deletes=True,
        overlaps="tenant",
    )

    allocations = relationship(
        "EventFinancialAdjustmentAllocation",
        back_populates="installment",
        passive_deletes=True,
        overlaps="tenant,allocations",
    )

    created_by_adjustment = relationship(
        "EventFinancialAdjustment",
        back_populates="created_installment",
        uselist=False,
        overlaps="financial_adjustments,tenant,event",
    )
