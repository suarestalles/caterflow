
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select

from app.db.tenant_session import TenantSession
from app.models.employee_compensation_payment import (
    EmployeeCompensationPayment,
)
from app.models.event_staff_assignment import EventStaffAssignment


def create(
    db: TenantSession,
    payment: EmployeeCompensationPayment,
) -> EmployeeCompensationPayment:
    db.add(payment)
    db.flush()
    return payment


def get_by_id(
    db: TenantSession,
    payment_id: UUID,
    *,
    for_update: bool = False,
) -> EmployeeCompensationPayment | None:
    stmt = select(EmployeeCompensationPayment).where(
        EmployeeCompensationPayment.id == payment_id,
    )

    if for_update:
        stmt = stmt.with_for_update()

    return db.scalar(stmt)


def get_assignment(
    db: TenantSession,
    assignment_id: UUID,
    *,
    for_update: bool = False,
) -> EventStaffAssignment | None:
    stmt = select(EventStaffAssignment).where(
        EventStaffAssignment.id == assignment_id,
    )

    if for_update:
        stmt = stmt.with_for_update()

    return db.scalar(stmt)


def list_by_assignment_id(
    db: TenantSession,
    assignment_id: UUID,
) -> list[EmployeeCompensationPayment]:
    stmt = (
        select(EmployeeCompensationPayment)
        .where(
            EmployeeCompensationPayment.assignment_id == assignment_id,
        )
        .order_by(
            EmployeeCompensationPayment.paid_at.desc(),
            EmployeeCompensationPayment.created_at.desc(),
        )
    )

    return list(db.scalars(stmt).all())


def get_total_paid(
    db: TenantSession,
    assignment_id: UUID,
):
    stmt = select(
        func.coalesce(
            func.sum(EmployeeCompensationPayment.amount),
            Decimal("0.00"),
        )
    ).where(
        EmployeeCompensationPayment.assignment_id == assignment_id,
    )

    return db.scalar(stmt) or 0
