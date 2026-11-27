
from datetime import datetime
from decimal import Decimal
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
from app.models.expense import Expense
from app.models.payment import PaymentMethod
from app.models.tenant_scoped import TenantScoped


class ExpensePayment(Abstract, TenantScoped):
    __tablename__ = "expense_payments"

    __table_args__ = (
        
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_expense_payments_tenant_id_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "expense_id"],
            ["expenses.tenant_id", "expenses.id"],
            name="fk_expense_payments_tenant_expense",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_expense_payments_amount_positive",
        ),
        CheckConstraint(
            """
            payment_method IN (
                'cash',
                'card',
                'bank_transfer',
                'other'
            )
            """,
            name="ck_expense_payments_method_valid",
        ),
        Index(
            "ix_expense_payments_tenant_expense",
            "tenant_id",
            "expense_id",
        ),
        Index(
            "ix_expense_payments_tenant_paid_at",
            "tenant_id",
            "paid_at",
        ),
    )

    expense_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    paid_at: Mapped[datetime] = mapped_column(
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
            name="fk_expense_payments_recorded_by_user",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    expense = relationship(
        "Expense",
        back_populates="payments",
        primaryjoin=lambda: (
            (Expense.id == foreign(ExpensePayment.expense_id))
            & (Expense.tenant_id == ExpensePayment.tenant_id)
        ),
    )

    recorded_by = relationship("User")

    tenant = relationship(
        "Tenant",
        back_populates="expense_payments",
        overlaps="payments,expense",
    )
