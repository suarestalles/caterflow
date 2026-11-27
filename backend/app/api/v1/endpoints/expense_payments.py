
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
from app.schemas.expense import ExpenseBalanceRead
from app.schemas.expense_payment import (
    ExpensePaymentCreate,
    ExpensePaymentRead,
)
from app.services import expense_payments as payment_service


router = APIRouter(tags=["Expense Payments"])


@router.post(
    "/",
    response_model=ExpensePaymentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(
                PermissionCode.FINANCE_EXPENSES_MANAGE
            )
        )
    ],
)
def create_expense_payment(
    data: ExpensePaymentCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payment_service.create(
        db,
        data,
        auth.user.id,
    )


@router.get(
    "/expenses/{expense_id}",
    response_model=list[ExpensePaymentRead],
    dependencies=[
        Depends(require_permission(PermissionCode.FINANCE_READ))
    ],
)
def list_expense_payments(
    expense_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payment_service.list_by_expense_id(db, expense_id)


@router.get(
    "/expenses/{expense_id}/balance",
    response_model=ExpenseBalanceRead,
    dependencies=[
        Depends(require_permission(PermissionCode.FINANCE_READ))
    ],
)
def get_expense_payment_balance(
    expense_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payment_service.get_balance(db, expense_id)


@router.get(
    "/{payment_id}",
    response_model=ExpensePaymentRead,
    dependencies=[
        Depends(require_permission(PermissionCode.FINANCE_READ))
    ],
)
def get_expense_payment(
    payment_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payment_service.get(db, payment_id)
