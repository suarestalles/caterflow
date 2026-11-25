
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.tenant_scoped import TenantScoped


class Employee(Abstract, TenantScoped):
    __tablename__ = "employees"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_employees_tenant_id_id",
        ),
        CheckConstraint(
            "employment_type IN ('employee', 'freelancer')",
            name="employment_type",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    employment_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="employee",
        server_default="employee",
    )

    position: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(254),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    tenant = relationship(
        "Tenant",
        back_populates="employees",
    )

    event_assignments = relationship(
        "EventStaffAssignment",
        back_populates="employee",
        primaryjoin=(
            "and_("
            "Employee.id == foreign(EventStaffAssignment.employee_id), "
            "Employee.tenant_id == EventStaffAssignment.tenant_id"
            ")"
        ),
    )
