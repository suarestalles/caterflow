
from datetime import date
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
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
from app.models.tenant_scoped import TenantScoped


class ExpenseCategory(StrEnum):
    FOOD = "food"
    BEVERAGES = "beverages"
    TRANSPORT = "transport"
    FUEL = "fuel"
    EQUIPMENT_RENTAL = "equipment_rental"
    DECORATION = "decoration"
    PARKING = "parking"
    DISPOSABLES = "disposables"
    EXTERNAL_SERVICES = "external_services"
    OTHER = "other"


class Expense(Abstract, TenantScoped):
    __tablename__ = "expenses"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_expenses_tenant_id_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "event_id"],
            ["events.tenant_id", "events.id"],
            name="fk_expenses_tenant_event",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_expenses_amount_positive",
        ),
        CheckConstraint(
            """
            category IN (
                'food',
                'beverages',
                'transport',
                'fuel',
                'equipment_rental',
                'decoration',
                'parking',
                'disposables',
                'external_services',
                'other'
            )
            """,
            name="ck_expenses_category_valid",
        ),
        Index(
            "ix_expenses_tenant_event",
            "tenant_id",
            "event_id",
        ),
        Index(
            "ix_expenses_tenant_incurred_at",
            "tenant_id",
            "incurred_at",
        ),
        Index(
            "ix_expenses_tenant_category",
            "tenant_id",
            "category",
        ),
    )

    event_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
    )

    category: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    incurred_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    supplier_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    invoice_reference: Mapped[str | None] = mapped_column(
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
            name="fk_expenses_recorded_by_user",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    event = relationship(
        "Event",
        back_populates="expenses",
        primaryjoin=lambda: (
            (Event.id == foreign(Expense.event_id))
            & (Event.tenant_id == Expense.tenant_id)
        ),
    )

    payments = relationship(
        "ExpensePayment",
        back_populates="expense",
        passive_deletes=True,
    )

    recorded_by = relationship("User")

    tenant = relationship(
        "Tenant",
        back_populates="expenses",
        overlaps="expenses",
    )
