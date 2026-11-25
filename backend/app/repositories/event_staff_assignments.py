
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.event_staff_assignment import EventStaffAssignment


def get_event_staff_assignment_by_id(
    db: Session,
    *,
    assignment_id: UUID,
) -> EventStaffAssignment | None:
    statement = select(EventStaffAssignment).where(
        EventStaffAssignment.id == assignment_id
    )
    return db.scalar(statement)


def get_event_staff_assignment_by_employee(
    db: Session,
    *,
    event_id: UUID,
    employee_id: UUID,
) -> EventStaffAssignment | None:
    statement = select(EventStaffAssignment).where(
        EventStaffAssignment.event_id == event_id,
        EventStaffAssignment.employee_id == employee_id,
    )
    return db.scalar(statement)


def list_event_staff_assignments(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    event_id: UUID | None = None,
    employee_id: UUID | None = None,
    status: str | None = None,
) -> tuple[list[EventStaffAssignment], int]:
    statement = select(EventStaffAssignment)

    if event_id is not None:
        statement = statement.where(
            EventStaffAssignment.event_id == event_id
        )

    if employee_id is not None:
        statement = statement.where(
            EventStaffAssignment.employee_id == employee_id
        )

    if status is not None:
        statement = statement.where(
            EventStaffAssignment.status == status
        )

    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery()
    )
    total = db.scalar(count_statement) or 0

    items_statement = (
        statement.order_by(
            EventStaffAssignment.created_at.desc(),
            EventStaffAssignment.id.asc(),
        )
        .offset(offset)
        .limit(limit)
    )

    items = list(db.scalars(items_statement).all())

    return items, total


def create_event_staff_assignment(
    db: Session,
    *,
    data: dict,
) -> EventStaffAssignment:
    assignment = EventStaffAssignment(**data)

    db.add(assignment)
    db.flush()
    db.refresh(assignment)

    return assignment


def update_event_staff_assignment(
    db: Session,
    *,
    assignment: EventStaffAssignment,
    data: dict,
) -> EventStaffAssignment:
    for field, value in data.items():
        setattr(assignment, field, value)

    db.flush()
    db.refresh(assignment)

    return assignment
