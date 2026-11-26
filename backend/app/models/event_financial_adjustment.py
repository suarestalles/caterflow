
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
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
from app.models.event import Event
from app.models.payment_installment import PaymentInstallment
from app.models.tenant_scoped import TenantScoped


class FinancialAdjustmentType(StrEnum):
    ADDITIONAL = "additional"
    DISCOUNT = "discount"


class EventFinancialAdjustment(Abstract, TenantScoped):
    __tablename__ = "event_financial_adjustments"

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "event_id"],
            ["events.tenant_id", "events.id"],
            name="fk_event_financial_adjustments_tenant_event",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "created_installment_id"],
            [
                "payment_installments.tenant_id",
                "payment_installments.id",
            ],
            name="fk_event_financial_adjustments_tenant_installment",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "tenant_id",
            "created_installment_id",
            name="uq_event_financial_adjustments_tenant_installment",
        ),
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_event_financial_adjustments_tenant_id_id",
        ),
        CheckConstraint(
            "amount > 0",
            name="event_financial_adjustment_amount_positive",
        ),
        CheckConstraint(
            "adjustment_type IN ('additional', 'discount')",
            name="event_financial_adjustment_type_valid",
        ),
        CheckConstraint(
            """
            (
                adjustment_type = 'additional'
                AND created_installment_id IS NOT NULL
            )
            OR
            (
                adjustment_type = 'discount'
                AND created_installment_id IS NULL
            )
            """,
            name="event_financial_adjustment_installment_valid",
        ),
        Index(
            "ix_event_financial_adjustments_tenant_event",
            "tenant_id",
            "event_id",
        ),
    )

    event_id: Mapped[UUID] = mapped_column(nullable=False)

    created_installment_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
    )

    adjustment_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    recorded_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_event_financial_adjustments_recorded_by_user",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    event = relationship(
        "Event",
        back_populates="financial_adjustments",
        primaryjoin=lambda: (
            (Event.id == foreign(EventFinancialAdjustment.event_id))
            & (Event.tenant_id == EventFinancialAdjustment.tenant_id)
        ),
    )

    created_installment = relationship(
        "PaymentInstallment",
        primaryjoin=lambda: (
            (
                PaymentInstallment.id
                == foreign(EventFinancialAdjustment.created_installment_id)
            )
            & (
                PaymentInstallment.tenant_id
                == EventFinancialAdjustment.tenant_id
            )
        ),
        uselist=False,
        overlaps="created_by_adjustment",
    )

    recorded_by = relationship("User")

    tenant = relationship(
        "Tenant",
        back_populates="event_financial_adjustments",
        overlaps="financial_adjustments,created_by_adjustment",
    )

    allocations = relationship(
        "EventFinancialAdjustmentAllocation",
        back_populates="adjustment",
        passive_deletes=True,
        overlaps="allocations",
    )
