
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.event_financial_adjustment import EventFinancialAdjustment
from app.models.payment_installment import PaymentInstallment
from app.models.tenant_scoped import TenantScoped


class EventFinancialAdjustmentAllocation(Abstract, TenantScoped):
    __tablename__ = "event_financial_adjustment_allocations"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_event_financial_adjustment_allocations_tenant_id_id",
        ),
        UniqueConstraint(
            "tenant_id",
            "adjustment_id",
            "installment_id",
            name="uq_efa_alloc_tenant_adj_inst",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "adjustment_id"],
            [
                "event_financial_adjustments.tenant_id",
                "event_financial_adjustments.id",
            ],
            name="fk_adjustment_allocations_tenant_adjustment",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "installment_id"],
            [
                "payment_installments.tenant_id",
                "payment_installments.id",
            ],
            name="fk_adjustment_allocations_tenant_installment",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "allocated_amount > 0",
            name="adjustment_allocation_amount_positive",
        ),
        Index(
            "ix_adjustment_allocations_tenant_adjustment",
            "tenant_id",
            "adjustment_id",
        ),
        Index(
            "ix_adjustment_allocations_tenant_installment",
            "tenant_id",
            "installment_id",
        ),
    )

    adjustment_id: Mapped[UUID] = mapped_column(nullable=False)

    installment_id: Mapped[UUID] = mapped_column(nullable=False)

    allocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    adjustment = relationship(
        "EventFinancialAdjustment",
        back_populates="allocations",
        primaryjoin=lambda: (
            (
                EventFinancialAdjustment.id
                == foreign(EventFinancialAdjustmentAllocation.adjustment_id)
            )
            & (
                EventFinancialAdjustment.tenant_id
                == EventFinancialAdjustmentAllocation.tenant_id
            )
        ),
        overlaps="allocations,tenant",
    )

    installment = relationship(
        "PaymentInstallment",
        back_populates="allocations",
        primaryjoin=lambda: (
            (
                PaymentInstallment.id
                == foreign(EventFinancialAdjustmentAllocation.installment_id)
            )
            & (
                PaymentInstallment.tenant_id
                == EventFinancialAdjustmentAllocation.tenant_id
            )
        ),
        overlaps="allocations,tenant",
    )

    tenant = relationship(
        "Tenant",
        back_populates="event_financial_adjustment_allocations",
        overlaps="allocations",
    )
