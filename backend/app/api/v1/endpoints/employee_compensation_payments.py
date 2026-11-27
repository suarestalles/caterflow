
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.v1.deps import (
    AuthContext,
    get_auth_context,
    get_current_tenant_db,
    require_permission,
)
from app.core.permissions import PermissionCode
from app.db.tenant_session import TenantSession
from app.schemas.employee_compensation_payment import (
    EmployeeCompensationBalanceRead,
    EmployeeCompensationPaymentCreate,
    EmployeeCompensationPaymentRead,
)
from app.services import employee_compensation_payments

router = APIRouter(tags=["Employee Compensation Payments"])


@router.post(
    "/",
    response_model=EmployeeCompensationPaymentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(PermissionCode.FINANCE_PAYMENTS_MANAGE),
        ),
    ],
)
def create_employee_compensation_payment_endpoint(
    data: EmployeeCompensationPaymentCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: TenantSession = Depends(get_current_tenant_db),
):
    return employee_compensation_payments.create_employee_compensation_payment(
        db=db,
        data=data,
        recorded_by_user_id=auth.user.id,
    )


@router.get(
    "/assignments/{assignment_id}",
    response_model=list[EmployeeCompensationPaymentRead],
    dependencies=[
        Depends(require_permission(PermissionCode.FINANCE_READ)),
    ],
)
def list_assignment_compensation_payments_endpoint(
    assignment_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return employee_compensation_payments.list_employee_compensation_payments(
        db=db,
        assignment_id=assignment_id,
    )


@router.get(
    "/assignments/{assignment_id}/balance",
    response_model=EmployeeCompensationBalanceRead,
    dependencies=[
        Depends(require_permission(PermissionCode.FINANCE_READ)),
    ],
)
def get_assignment_compensation_balance_endpoint(
    assignment_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return employee_compensation_payments.get_employee_compensation_balance(
        db=db,
        assignment_id=assignment_id,
    )


@router.get(
    "/{payment_id}",
    response_model=EmployeeCompensationPaymentRead,
    dependencies=[
        Depends(require_permission(PermissionCode.FINANCE_READ)),
    ],
)
def get_employee_compensation_payment_endpoint(
    payment_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return employee_compensation_payments.get_employee_compensation_payment(
        db=db,
        payment_id=payment_id,
    )
