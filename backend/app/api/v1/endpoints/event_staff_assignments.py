
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import get_current_tenant_db, require_permission
from app.core.permissions import PermissionCode
from app.db.tenant_session import TenantSession
from app.schemas.event_staff_assignment import (
    EventStaffAssignmentCreate,
    EventStaffAssignmentListResponse,
    EventStaffAssignmentResponse,
    EventStaffAssignmentStatus,
    EventStaffAssignmentUpdate,
)
from app.services.event_staff_assignments import (
    AssignmentEmployeeNotFoundError,
    AssignmentEventNotFoundError,
    EventStaffAssignmentNotFoundError,
    InvalidEventStaffAssignmentDataError,
    create_event_staff_assignment,
    get_event_staff_assignment,
    list_event_staff_assignments,
    update_event_staff_assignment,
)

router = APIRouter(tags=["Event Staff Assignments"])


def _handle_assignment_error(error: Exception) -> None:
    if isinstance(
        error,
        (
            EventStaffAssignmentNotFoundError,
            AssignmentEmployeeNotFoundError,
            AssignmentEventNotFoundError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    if isinstance(error, InvalidEventStaffAssignmentDataError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    raise error


@router.post(
    "/",
    response_model=EventStaffAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PermissionCode.STAFF_ASSIGN))],
)
def create_event_staff_assignment_endpoint(
    payload: EventStaffAssignmentCreate,
    db: TenantSession = Depends(get_current_tenant_db),
) -> EventStaffAssignmentResponse:
    try:
        return create_event_staff_assignment(
            db,
            data=payload.model_dump(),
        )
    except (
        AssignmentEmployeeNotFoundError,
        AssignmentEventNotFoundError,
        InvalidEventStaffAssignmentDataError,
    ) as error:
        _handle_assignment_error(error)


@router.get(
    "/",
    response_model=EventStaffAssignmentListResponse,
    dependencies=[Depends(require_permission(PermissionCode.STAFF_READ))],
)
def list_event_staff_assignments_endpoint(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    event_id: UUID | None = Query(default=None),
    employee_id: UUID | None = Query(default=None),
    assignment_status: EventStaffAssignmentStatus | None = Query(
        default=None,
        alias="status",
    ),
    db: TenantSession = Depends(get_current_tenant_db),
) -> EventStaffAssignmentListResponse:
    assignments, total = list_event_staff_assignments(
        db,
        offset=offset,
        limit=limit,
        event_id=event_id,
        employee_id=employee_id,
        status=assignment_status,
    )

    return EventStaffAssignmentListResponse(
        items=assignments,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{assignment_id}",
    response_model=EventStaffAssignmentResponse,
    dependencies=[Depends(require_permission(PermissionCode.STAFF_READ))],
)
def get_event_staff_assignment_endpoint(
    assignment_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
) -> EventStaffAssignmentResponse:
    try:
        return get_event_staff_assignment(
            db,
            assignment_id=assignment_id,
        )
    except EventStaffAssignmentNotFoundError as error:
        _handle_assignment_error(error)


@router.patch(
    "/{assignment_id}",
    response_model=EventStaffAssignmentResponse,
    dependencies=[Depends(require_permission(PermissionCode.STAFF_ASSIGN))],
)
def update_event_staff_assignment_endpoint(
    assignment_id: UUID,
    payload: EventStaffAssignmentUpdate,
    db: TenantSession = Depends(get_current_tenant_db),
) -> EventStaffAssignmentResponse:
    try:
        return update_event_staff_assignment(
            db,
            assignment_id=assignment_id,
            data=payload.model_dump(exclude_unset=True),
        )
    except (
        EventStaffAssignmentNotFoundError,
        AssignmentEmployeeNotFoundError,
        AssignmentEventNotFoundError,
        InvalidEventStaffAssignmentDataError,
    ) as error:
        _handle_assignment_error(error)
