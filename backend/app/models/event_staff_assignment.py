
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
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.tenant_scoped import TenantScoped


class EventStaffAssignmentStatus(StrEnum):
    ASSIGNED = "assigned"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CompensationType(StrEnum):
    HOURLY = "hourly"
    FIXED = "fixed"


class EventStaffAssignment(Abstract, TenantScoped):
    __tablename__ = "event_staff_assignments"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_event_staff_assignments_tenant_id_id",
        ),
        UniqueConstraint(
            "tenant_id",
            "event_id",
            "employee_id",
            name="uq_event_staff_assignments_event_employee",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "event_id"],
            ["events.tenant_id", "events.id"],
            name="fk_event_staff_assignments_tenant_event",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["employees.tenant_id", "employees.id"],
            name="fk_event_staff_assignments_tenant_employee",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status IN ('assigned', 'confirmed', 'completed', 'cancelled')",
            name="status",
        ),
        CheckConstraint(
            "compensation_type IN ('hourly', 'fixed')",
            name="compensation_type",
        ),
        CheckConstraint(
            "planned_hours >= 0",
            name="planned_hours",
        ),
        CheckConstraint(
            "actual_hours IS NULL OR actual_hours >= 0",
            name="actual_hours",
        ),
        CheckConstraint(
            "compensation_rate >= 0",
            name="compensation_rate",
        ),
        CheckConstraint(
            "planned_compensation >= 0",
            name="planned_compensation",
        ),
        CheckConstraint(
            "actual_compensation IS NULL OR actual_compensation >= 0",
            name="actual_compensation",
        ),
    )

    event_id: Mapped[UUID] = mapped_column(nullable=False)
    employee_id: Mapped[UUID] = mapped_column(nullable=False)

    position: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EventStaffAssignmentStatus.ASSIGNED.value,
        server_default=text("'assigned'"),
    )

    planned_hours: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
    )

    actual_hours: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )

    compensation_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    compensation_rate: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    planned_compensation: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    actual_compensation: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    event = relationship(
        "Event",
        back_populates="staff_assignments",
        primaryjoin=(
            "and_("
            "foreign(EventStaffAssignment.event_id) == Event.id, "
            "EventStaffAssignment.tenant_id == Event.tenant_id"
            ")"
        ),
    )

    employee = relationship(
        "Employee",
        back_populates="event_assignments",
        primaryjoin=(
            "and_("
            "foreign(EventStaffAssignment.employee_id) == Employee.id, "
            "EventStaffAssignment.tenant_id == Employee.tenant_id"
            ")"
        ),
    )

    tenant = relationship(
        "Tenant",
        back_populates="event_staff_assignments",
    )

    compensation_payments = relationship(
        "EmployeeCompensationPayment",
        back_populates="assignment",
        passive_deletes=True,
        overlaps="tenant,employee_compensation_payments",
    )