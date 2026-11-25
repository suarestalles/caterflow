
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.employee import Employee


def get_employee_by_id(
    db: Session,
    employee_id: UUID,
) -> Employee | None:
    statement = select(Employee).where(Employee.id == employee_id)
    return db.scalar(statement)


def list_employees(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
) -> tuple[list[Employee], int]:
    statement = select(Employee).where(Employee.archived_at.is_(None))

    if search:
        search_term = f"%{search.strip()}%"

        statement = statement.where(
            or_(
                Employee.name.ilike(search_term),
                Employee.email.ilike(search_term),
                Employee.phone.ilike(search_term),
                Employee.position.ilike(search_term),
            )
        )

    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery()
    )

    total = db.scalar(count_statement) or 0

    statement = (
        statement.order_by(Employee.name.asc(), Employee.id.asc())
        .offset(offset)
        .limit(limit)
    )

    employees = list(db.scalars(statement).all())

    return employees, total


def create_employee(
    db: Session,
    *,
    data: dict,
) -> Employee:
    employee = Employee(**data)

    db.add(employee)
    db.flush()
    db.refresh(employee)

    return employee


def update_employee(
    db: Session,
    *,
    employee: Employee,
    data: dict,
) -> Employee:
    for field, value in data.items():
        setattr(employee, field, value)

    db.flush()
    db.refresh(employee)

    return employee


def archive_employee(
    db: Session,
    *,
    employee: Employee,
    archived_at,
) -> Employee:
    employee.archived_at = archived_at

    db.flush()
    db.refresh(employee)

    return employee
