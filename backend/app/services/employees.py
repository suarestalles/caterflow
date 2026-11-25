
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.repositories import employees as employee_repository


class EmployeeNotFoundError(Exception):
    pass


class InvalidEmployeeDataError(Exception):
    pass


def list_employees(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
) -> tuple[list[Employee], int]:
    return employee_repository.list_employees(
        db,
        offset=offset,
        limit=limit,
        search=search,
    )


def get_employee(
    db: Session,
    *,
    employee_id: UUID,
) -> Employee:
    employee = employee_repository.get_employee_by_id(
        db,
        employee_id,
    )

    if employee is None or employee.archived_at is not None:
        raise EmployeeNotFoundError("Employee not found.")

    return employee


def create_employee(
    db: Session,
    *,
    data: dict,
) -> Employee:
    employee_data = data.copy()

    if employee_data.get("name") is None:
        raise InvalidEmployeeDataError("Employee name cannot be null.")

    if employee_data.get("employment_type") is None:
        raise InvalidEmployeeDataError("Employment type cannot be null.")

    try:
        employee = employee_repository.create_employee(
            db,
            data=employee_data,
        )

        db.commit()
        db.refresh(employee)

        return employee
    except Exception:
        db.rollback()
        raise


def update_employee(
    db: Session,
    *,
    employee_id: UUID,
    data: dict,
) -> Employee:
    employee = get_employee(
        db,
        employee_id=employee_id,
    )

    updated_data = data.copy()

    if not updated_data:
        raise InvalidEmployeeDataError(
            "At least one field must be provided."
        )

    if "name" in updated_data and updated_data["name"] is None:
        raise InvalidEmployeeDataError("Employee name cannot be null.")

    if (
        "employment_type" in updated_data
        and updated_data["employment_type"] is None
    ):
        raise InvalidEmployeeDataError(
            "Employment type cannot be null."
        )

    try:
        employee = employee_repository.update_employee(
            db,
            employee=employee,
            data=updated_data,
        )

        db.commit()
        db.refresh(employee)

        return employee
    except Exception:
        db.rollback()
        raise


def archive_employee(
    db: Session,
    *,
    employee_id: UUID,
) -> None:
    employee = get_employee(
        db,
        employee_id=employee_id,
    )

    try:
        employee_repository.archive_employee(
            db,
            employee=employee,
            archived_at=datetime.now(UTC),
        )

        db.commit()
    except Exception:
        db.rollback()
        raise
