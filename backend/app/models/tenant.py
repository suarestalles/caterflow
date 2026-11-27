
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract import Abstract


class Tenant(Abstract):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    roles = relationship(
        "Role",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    memberships = relationship(
        "Membership",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    clients = relationship(
        "Client",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    events = relationship(
        "Event",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    quotes = relationship(
        "Quote",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    product_categories = relationship(
        "ProductCategory",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    products = relationship(
        "Product",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    employees = relationship(
        "Employee",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    event_staff_assignments = relationship(
        "EventStaffAssignment",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    payment_schedules = relationship(
        "PaymentSchedule",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="payment_schedule",
    )

    payment_installments = relationship(
        "PaymentInstallment",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="installments",
    )

    payments = relationship(
        "Payment",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="payments",
    )

    payment_refunds = relationship(
        "PaymentRefund",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="refunds",
    )

    event_financial_adjustments = relationship(
        "EventFinancialAdjustment",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="financial_adjustments,created_by_adjustment",
    )

    event_financial_adjustment_allocations = relationship(
        "EventFinancialAdjustmentAllocation",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="allocations",
    )

    employee_compensation_payments = relationship(
        "EmployeeCompensationPayment",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="compensation_payments,assignment",
    )

    expenses = relationship(
        "Expense",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="expenses",
    )

    expense_payments = relationship(
        "ExpensePayment",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="payments,expense",
    )

    financial_audit_logs = relationship(
        "FinancialAuditLog",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )