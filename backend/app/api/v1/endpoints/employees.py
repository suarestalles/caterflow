
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.v1.deps import get_current_tenant_db, require_permission
from app.core.permissions import PermissionCode
from app.db.tenant_session import TenantSession
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.services.employees import (
    EmployeeNotFoundError,
    InvalidEmployeeDataError,
    archive_employee,
    create_employee,
    get_employee,
    list_employees,
    update_employee,
)

router = APIRouter(tags=["Staff"])


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PermissionCode.STAFF_CREATE))],
)
def create_employee_endpoint(
    payload: EmployeeCreate,
    db: TenantSession = Depends(get_current_tenant_db),
) -> EmployeeResponse:
    try:
        return create_employee(
            db,
            data=payload.model_dump(),
        )
    except InvalidEmployeeDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get(
    "/",
    response_model=EmployeeListResponse,
    dependencies=[Depends(require_permission(PermissionCode.STAFF_READ))],
)
def list_employees_endpoint(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    db: TenantSession = Depends(get_current_tenant_db),
) -> EmployeeListResponse:
    employees, total = list_employees(
        db,
        offset=offset,
        limit=limit,
        search=search,
    )

    return EmployeeListResponse(
        items=employees,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    dependencies=[Depends(require_permission(PermissionCode.STAFF_READ))],
)
def get_employee_endpoint(
    employee_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
) -> EmployeeResponse:
    try:
        return get_employee(
            db,
            employee_id=employee_id,
        )
    except EmployeeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found.",
        ) from None


@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
    dependencies=[Depends(require_permission(PermissionCode.STAFF_UPDATE))],
)
def update_employee_endpoint(
    employee_id: UUID,
    payload: EmployeeUpdate,
    db: TenantSession = Depends(get_current_tenant_db),
) -> EmployeeResponse:
    try:
        return update_employee(
            db,
            employee_id=employee_id,
            data=payload.model_dump(exclude_unset=True),
        )
    except EmployeeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found.",
        ) from None
    except InvalidEmployeeDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(PermissionCode.STAFF_ARCHIVE))],
)
def archive_employee_endpoint(
    employee_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
) -> Response:
    try:
        archive_employee(
            db,
            employee_id=employee_id,
        )
    except EmployeeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found.",
        ) from None

    return Response(status_code=status.HTTP_204_NO_CONTENT)
