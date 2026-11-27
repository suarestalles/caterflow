
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
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.payment import PaymentMethod
from app.models.tenant_scoped import TenantScoped


class EmployeeCompensationPayment(Abstract, TenantScoped):
    __tablename__ = "employee_compensation_payments"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_employee_compensation_payments_tenant_id_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            [
                "event_staff_assignments.tenant_id",
                "event_staff_assignments.id",
            ],
            name="fk_employee_compensation_payments_tenant_assignment",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "amount > 0",
            name="amount_positive",
        ),
        CheckConstraint(
            "payment_method IN ('cash', 'card', 'bank_transfer', 'other')",
            name="payment_method_valid",
        ),
        Index(
            "ix_employee_compensation_payments_tenant_assignment",
            "tenant_id",
            "assignment_id",
        ),
        Index(
            "ix_employee_compensation_payments_tenant_paid_at",
            "tenant_id",
            "paid_at",
        ),
    )

    assignment_id: Mapped[UUID] = mapped_column(nullable=False)

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    payment_method: Mapped[str] = mapped_column(
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recorded_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_employee_compensation_payments_recorded_by_user",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    assignment = relationship(
        "EventStaffAssignment",
        back_populates="compensation_payments",
        primaryjoin=(
            "and_("
            "foreign(EmployeeCompensationPayment.assignment_id) "
            "== EventStaffAssignment.id, "
            "EmployeeCompensationPayment.tenant_id "
            "== EventStaffAssignment.tenant_id"
            ")"
        ),
    )

    recorded_by = relationship("User")

    tenant = relationship(
        "Tenant",
        back_populates="employee_compensation_payments",
    )
