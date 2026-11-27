
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import (
    AuthContext,
    get_auth_context,
    get_current_tenant_db,
    require_permission,
)
from app.core.permissions import PermissionCode
from app.db.tenant_session import TenantSession
from app.schemas.expense import (
    ExpenseBalanceRead,
    ExpenseCreate,
    ExpenseListRead,
    ExpenseRead,
    ExpenseUpdate,
)
from app.services import expenses as expense_service


router = APIRouter(tags=["Expenses"])


@router.post(
    "/",
    response_model=ExpenseRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(
                PermissionCode.FINANCE_EXPENSES_MANAGE
            )
        )
    ],
)
def create_expense(
    data: ExpenseCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: TenantSession = Depends(get_current_tenant_db),
):
    return expense_service.create(
        db,
        data,
        auth.user.id,
    )


@router.get(
    "/",
    response_model=ExpenseListRead,
    dependencies=[
        Depends(require_permission(PermissionCode.FINANCE_READ))
    ],
)
def list_expenses(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: TenantSession = Depends(get_current_tenant_db),
):
    items, total = expense_service.list_all(
        db,
        offset=offset,
        limit=limit,
    )

    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get(
    "/events/{event_id}",
    response_model=list[ExpenseRead],
    dependencies=[
        Depends(require_permission(PermissionCode.FINANCE_READ))
    ],
)
def list_event_expenses(
    event_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return expense_service.list_by_event_id(db, event_id)


@router.get(
    "/{expense_id}/balance",
    response_model=ExpenseBalanceRead,
    dependencies=[
        Depends(require_permission(PermissionCode.FINANCE_READ))
    ],
)
def get_expense_balance(
    expense_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return expense_service.get_balance(db, expense_id)


@router.get(
    "/{expense_id}",
    response_model=ExpenseRead,
    dependencies=[
        Depends(require_permission(PermissionCode.FINANCE_READ))
    ],
)
def get_expense(
    expense_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return expense_service.get(db, expense_id)



@router.patch(
    "/{expense_id}",
    response_model=ExpenseRead,
    dependencies=[
        Depends(
            require_permission(
                PermissionCode.FINANCE_EXPENSES_MANAGE
            )
        )
    ],
)
def update_expense(
    expense_id: UUID,
    data: ExpenseUpdate,
    auth: AuthContext = Depends(get_auth_context),
    db: TenantSession = Depends(get_current_tenant_db),
):
    return expense_service.update(
        db,
        expense_id,
        data,
        recorded_by_user_id=auth.user.id,
    )
