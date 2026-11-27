
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.event import Event, EventStatus
from app.models.event_staff_assignment import (
    CompensationType,
    EventStaffAssignment,
    EventStaffAssignmentStatus,
)
from app.repositories import employees as employee_repository
from app.repositories import events as event_repository
from app.repositories import event_staff_assignments as assignment_repository
from app.schemas.financial_audit_log import (
    FinancialAuditEntityType,
    FinancialAuditLogCreate,
)
from app.services import financial_audit_logs


class EventStaffAssignmentNotFoundError(Exception):
    pass


class AssignmentEmployeeNotFoundError(Exception):
    pass


class AssignmentEventNotFoundError(Exception):
    pass


class InvalidEventStaffAssignmentDataError(Exception):
    pass


ALLOWED_STATUS_TRANSITIONS = {
    EventStaffAssignmentStatus.ASSIGNED.value: {
        EventStaffAssignmentStatus.CONFIRMED.value,
        EventStaffAssignmentStatus.CANCELLED.value,
    },
    EventStaffAssignmentStatus.CONFIRMED.value: {
        EventStaffAssignmentStatus.COMPLETED.value,
        EventStaffAssignmentStatus.CANCELLED.value,
    },
}


def list_event_staff_assignments(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    event_id: UUID | None = None,
    employee_id: UUID | None = None,
    status: str | None = None,
) -> tuple[list[EventStaffAssignment], int]:
    return assignment_repository.list_event_staff_assignments(
        db,
        offset=offset,
        limit=limit,
        event_id=event_id,
        employee_id=employee_id,
        status=status,
    )


def get_event_staff_assignment(
    db: Session,
    *,
    assignment_id: UUID,
) -> EventStaffAssignment:
    assignment = assignment_repository.get_event_staff_assignment_by_id(
        db,
        assignment_id=assignment_id,
    )

    if assignment is None:
        raise EventStaffAssignmentNotFoundError(
            "Event staff assignment not found."
        )

    return assignment


def create_event_staff_assignment(
    db: Session,
    *,
    data: dict,
) -> EventStaffAssignment:
    assignment_data = data.copy()

    _validate_event(
        db,
        event_id=assignment_data["event_id"],
    )

    employee = _validate_employee(
        db,
        employee_id=assignment_data["employee_id"],
    )

    existing_assignment = (
        assignment_repository.get_event_staff_assignment_by_employee(
            db,
            event_id=assignment_data["event_id"],
            employee_id=assignment_data["employee_id"],
        )
    )

    if existing_assignment is not None:
        raise InvalidEventStaffAssignmentDataError(
            "This employee is already assigned to this event."
        )

    compensation_type = assignment_data.get("compensation_type")
    compensation_rate = assignment_data.get("compensation_rate")

    if compensation_type is None and compensation_rate is None:
        compensation_type = employee.default_compensation_type
        compensation_rate = employee.default_compensation_rate

    elif compensation_type is None or compensation_rate is None:
        raise InvalidEventStaffAssignmentDataError(
            "Compensation type and rate must be provided together."
        )

    if compensation_type is None or compensation_rate is None:
        raise InvalidEventStaffAssignmentDataError(
            "The employee has no default compensation. "
            "Provide compensation type and rate for this assignment."
        )

    compensation_type = _normalize_compensation_type(
        compensation_type
    )

    if compensation_rate <= Decimal("0"):
        raise InvalidEventStaffAssignmentDataError(
            "Compensation rate must be greater than zero."
        )

    assignment_data["compensation_type"] = compensation_type
    assignment_data["compensation_rate"] = compensation_rate
    assignment_data["status"] = EventStaffAssignmentStatus.ASSIGNED.value

    assignment_data["planned_compensation"] = _calculate_planned_compensation(
        planned_hours=assignment_data["planned_hours"],
        compensation_rate=compensation_rate,
        compensation_type=compensation_type,
    )

    try:
        assignment = assignment_repository.create_event_staff_assignment(
            db,
            data=assignment_data,
        )

        db.commit()
        db.refresh(assignment)

        return assignment
    except Exception:
        db.rollback()
        raise



def update_event_staff_assignment(
    db: Session,
    *,
    assignment_id: UUID,
    data: dict,
    recorded_by_user_id: UUID | None = None,
    allow_financial_correction: bool = False,
) -> EventStaffAssignment:
    assignment = get_event_staff_assignment(
        db,
        assignment_id=assignment_id,
    )

    updated_data = data.copy()
    reason = updated_data.pop("reason", None)

    if not updated_data:
        raise InvalidEventStaffAssignmentDataError(
            "At least one field must be provided."
        )

    is_completed = (
        assignment.status == EventStaffAssignmentStatus.COMPLETED.value
    )

    if assignment.status == EventStaffAssignmentStatus.CANCELLED.value:
        raise InvalidEventStaffAssignmentDataError(
            "Cancelled assignments cannot be modified."
        )

    financial_fields = {
        "actual_hours",
        "actual_compensation",
        "compensation_rate",
        "compensation_type",
    }

    if is_completed:
        if not allow_financial_correction:
            raise InvalidEventStaffAssignmentDataError(
                "Financial correction permission is required."
            )

        if not set(updated_data).issubset(financial_fields):
            raise InvalidEventStaffAssignmentDataError(
                "Only financial fields can be corrected "
                "on completed assignments."
            )

        if not isinstance(reason, str) or not reason.strip():
            raise InvalidEventStaffAssignmentDataError(
                "A reason is required for financial corrections."
            )

        if recorded_by_user_id is None:
            raise InvalidEventStaffAssignmentDataError(
                "The user responsible for the correction is required."
            )

    if "status" in updated_data:
        new_status = _normalize_status(updated_data["status"])

        _validate_status_transition(
            current_status=assignment.status,
            new_status=new_status,
        )

        updated_data["status"] = new_status

    if "position" in updated_data and updated_data["position"] is None:
        raise InvalidEventStaffAssignmentDataError(
            "Assignment position cannot be null."
        )

    if (
        "planned_hours" in updated_data
        and updated_data["planned_hours"] is None
    ):
        raise InvalidEventStaffAssignmentDataError(
            "Planned hours cannot be null."
        )

    if (
        "compensation_type" in updated_data
        and updated_data["compensation_type"] is None
    ):
        raise InvalidEventStaffAssignmentDataError(
            "Compensation type cannot be null."
        )

    if (
        "compensation_rate" in updated_data
        and updated_data["compensation_rate"] is None
    ):
        raise InvalidEventStaffAssignmentDataError(
            "Compensation rate cannot be null."
        )

    planned_hours = updated_data.get(
        "planned_hours",
        assignment.planned_hours,
    )

    compensation_rate = updated_data.get(
        "compensation_rate",
        assignment.compensation_rate,
    )

    compensation_type = _normalize_compensation_type(
        updated_data.get(
            "compensation_type",
            assignment.compensation_type,
        )
    )

    updated_data["compensation_type"] = compensation_type

    if {
        "planned_hours",
        "compensation_rate",
        "compensation_type",
    }.intersection(updated_data) and not is_completed:
        updated_data["planned_compensation"] = (
            _calculate_planned_compensation(
                planned_hours=planned_hours,
                compensation_rate=compensation_rate,
                compensation_type=compensation_type,
            )
        )

    if (
        updated_data.get("status")
        == EventStaffAssignmentStatus.COMPLETED.value
    ):
        actual_hours = updated_data.get(
            "actual_hours",
            assignment.actual_hours,
        )

        if actual_hours is None:
            raise InvalidEventStaffAssignmentDataError(
                "Actual hours are required to complete an assignment."
            )

        if "actual_compensation" not in updated_data:
            updated_data["actual_compensation"] = (
                _calculate_actual_compensation(
                    actual_hours=actual_hours,
                    compensation_rate=compensation_rate,
                    compensation_type=compensation_type,
                )
            )

    audit_changes = []

    if is_completed:
        if (
            {
                "actual_hours",
                "compensation_rate",
                "compensation_type",
            }.intersection(updated_data)
            and "actual_compensation" not in updated_data
        ):
            actual_hours = updated_data.get(
                "actual_hours",
                assignment.actual_hours,
            )

            if actual_hours is None:
                actual_hours = Decimal("0")

            updated_data["actual_compensation"] = (
                _calculate_actual_compensation(
                    actual_hours=actual_hours,
                    compensation_rate=compensation_rate,
                    compensation_type=compensation_type,
                )
            )

        for field_name in financial_fields:
            if field_name not in updated_data:
                continue

            old_value = getattr(assignment, field_name)
            new_value = updated_data[field_name]

            if field_name == "compensation_type":
                new_value = _normalize_compensation_type(new_value)
                updated_data[field_name] = new_value

            if old_value is None and new_value is None:
                continue

            if old_value is not None and new_value is not None:
                if field_name == "compensation_type":
                    unchanged = old_value == new_value
                else:
                    unchanged = Decimal(str(old_value)) == Decimal(
                        str(new_value)
                    )
            else:
                unchanged = old_value == new_value

            if not unchanged:
                audit_changes.append(
                    {
                        "field_name": field_name,
                        "old_value": (
                            str(old_value) if old_value is not None else None
                        ),
                        "new_value": (
                            str(new_value) if new_value is not None else None
                        ),
                    }
                )

        if not audit_changes:
            raise InvalidEventStaffAssignmentDataError(
                "No financial changes were detected."
            )

    try:
        assignment = assignment_repository.update_event_staff_assignment(
            db,
            assignment=assignment,
            data=updated_data,
        )

        for change in audit_changes:
            financial_audit_logs.record(
                db,
                data=FinancialAuditLogCreate(
                    event_id=assignment.event_id,
                    entity_type=FinancialAuditEntityType.EVENT_STAFF_ASSIGNMENT,
                    entity_id=assignment.id,
                    field_name=change["field_name"],
                    old_value=change["old_value"],
                    new_value=change["new_value"],
                    reason=reason.strip(),
                ),
                recorded_by_user_id=recorded_by_user_id,
            )

        db.commit()
        db.refresh(assignment)

        return assignment
    except Exception:
        db.rollback()
        raise



def _validate_employee(
    db: Session,
    *,
    employee_id: UUID,
) -> Employee:
    employee = employee_repository.get_employee_by_id(
        db,
        employee_id,
    )

    if employee is None or employee.archived_at is not None:
        raise AssignmentEmployeeNotFoundError(
            "An active employee from this tenant is required."
        )

    return employee


def _validate_event(
    db: Session,
    *,
    event_id: UUID,
) -> None:
    event = event_repository.get_event_by_id(
        db,
        event_id=event_id,
    )

    if event is None:
        raise AssignmentEventNotFoundError("Event not found.")

    if event.status in {
        EventStatus.COMPLETED.value,
        EventStatus.CANCELLED.value,
    }:
        raise InvalidEventStaffAssignmentDataError(
            "Staff cannot be assigned to completed or cancelled events."
        )


def _calculate_planned_compensation(
    *,
    planned_hours: Decimal,
    compensation_rate: Decimal,
    compensation_type: str,
) -> Decimal:
    if compensation_type == CompensationType.HOURLY.value:
        return (planned_hours * compensation_rate).quantize(
            Decimal("0.01")
        )

    return compensation_rate.quantize(Decimal("0.01"))


def _calculate_actual_compensation(
    *,
    actual_hours: Decimal | None,
    compensation_rate: Decimal,
    compensation_type: str,
) -> Decimal:
    if compensation_type == CompensationType.HOURLY.value:
        if actual_hours is None:
            raise InvalidEventStaffAssignmentDataError(
                "Actual hours are required for hourly compensation."
            )

        return (actual_hours * compensation_rate).quantize(
            Decimal("0.01")
        )

    return compensation_rate.quantize(Decimal("0.01"))


def _normalize_compensation_type(
    compensation_type: CompensationType | str,
) -> str:
    if isinstance(compensation_type, CompensationType):
        return compensation_type.value

    try:
        return CompensationType(compensation_type).value
    except ValueError as exc:
        raise InvalidEventStaffAssignmentDataError(
            "Invalid compensation type."
        ) from exc


def _normalize_status(
    status: EventStaffAssignmentStatus | str,
) -> str:
    if isinstance(status, EventStaffAssignmentStatus):
        return status.value

    try:
        return EventStaffAssignmentStatus(status).value
    except ValueError as exc:
        raise InvalidEventStaffAssignmentDataError(
            "Invalid assignment status."
        ) from exc


def _validate_status_transition(
    *,
    current_status: str,
    new_status: str,
) -> None:
    if current_status == new_status:
        return

    allowed_statuses = ALLOWED_STATUS_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise InvalidEventStaffAssignmentDataError(
            f"Invalid assignment status transition: "
            f"{current_status} -> {new_status}."
        )
