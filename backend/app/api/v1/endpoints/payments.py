
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
from app.schemas.event_financial_adjustment import (
    EventFinancialAdjustmentCreate,
    EventFinancialAdjustmentRead,
)
from app.schemas.payment import PaymentCreate, PaymentRead
from app.schemas.payment_refund import (
    PaymentRefundCreate,
    PaymentRefundRead,
)
from app.schemas.payment_schedule import (
    PaymentScheduleCreate,
    PaymentScheduleRead,
)
from app.services import (
    event_financial_adjustments,
    payment_refunds,
    payment_schedules,
    payments,
)

router = APIRouter(tags=["Payments"])


# ------------------------------------------------------------------
# Payment schedules
# ------------------------------------------------------------------


@router.post(
    "/schedules",
    response_model=PaymentScheduleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_CREATE)),
    ],
)
def create_schedule(
    data: PaymentScheduleCreate,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payment_schedules.create_payment_schedule(
        db=db,
        data=data,
    )


@router.get(
    "/schedules/{schedule_id}",
    response_model=PaymentScheduleRead,
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_READ)),
    ],
)
def get_schedule(
    schedule_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payment_schedules.get_payment_schedule(
        db=db,
        payment_schedule_id=schedule_id,
    )


@router.get(
    "/events/{event_id}/schedule",
    response_model=PaymentScheduleRead,
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_READ)),
    ],
)
def get_event_schedule(
    event_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payment_schedules.get_payment_schedule_by_event(
        db=db,
        event_id=event_id,
    )


# ------------------------------------------------------------------
# Payments
# ------------------------------------------------------------------


@router.post(
    "/",
    response_model=PaymentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_CREATE)),
    ],
)
def create_payment(
    data: PaymentCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payments.create_payment(
        db=db,
        data=data,
        recorded_by_user_id=auth.user.id,
    )


@router.get(
    "/installments/{installment_id}",
    response_model=list[PaymentRead],
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_READ)),
    ],
)
def list_installment_payments(
    installment_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payments.list_payments_by_installment(
        db=db,
        installment_id=installment_id,
    )


@router.get(
    "/events/{event_id}",
    response_model=list[PaymentRead],
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_READ)),
    ],
)
def list_event_payments(
    event_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payments.list_payments_by_event(
        db=db,
        event_id=event_id,
    )

@router.get(
    "/{payment_id}",
    response_model=PaymentRead,
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_READ)),
    ],
)
def get_payment(
    payment_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payments.get_payment(
        db=db,
        payment_id=payment_id,
    )


# ------------------------------------------------------------------
# Refunds
# ------------------------------------------------------------------


@router.post(
    "/refunds",
    response_model=PaymentRefundRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_REFUND)),
    ],
)
def create_refund(
    data: PaymentRefundCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payment_refunds.create_refund(
        db=db,
        data=data,
        recorded_by_user_id=auth.user.id,
    )


@router.get(
    "/refunds/{refund_id}",
    response_model=PaymentRefundRead,
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_READ)),
    ],
)
def get_refund(
    refund_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payment_refunds.get_refund(
        db=db,
        refund_id=refund_id,
    )


@router.post(
    "/refunds/{refund_id}/process",
    response_model=PaymentRefundRead,
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_REFUND)),
    ],
)
def process_refund(
    refund_id: UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payment_refunds.process_refund(
        db=db,
        refund_id=refund_id,
        processed_by_user_id=auth.user.id,
    )


@router.post(
    "/refunds/{refund_id}/cancel",
    response_model=PaymentRefundRead,
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_REFUND)),
    ],
)
def cancel_refund(
    refund_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payment_refunds.cancel_refund(
        db=db,
        refund_id=refund_id,
    )


@router.get(
    "/events/{event_id}/refunds",
    response_model=list[PaymentRefundRead],
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_READ)),
    ],
)
def list_event_refunds(
    event_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payment_refunds.list_refunds_by_event(
        db=db,
        event_id=event_id,
    )


@router.get(
    "/{payment_id}/refunds",
    response_model=list[PaymentRefundRead],
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_READ)),
    ],
)
def list_payment_refunds(
    payment_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return payment_refunds.list_refunds_by_payment(
        db=db,
        payment_id=payment_id,
    )


# ------------------------------------------------------------------
# Financial adjustments
# ------------------------------------------------------------------


@router.post(
    "/adjustments",
    response_model=EventFinancialAdjustmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_ADJUST)),
    ],
)
def create_financial_adjustment(
    data: EventFinancialAdjustmentCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: TenantSession = Depends(get_current_tenant_db),
):
    return event_financial_adjustments.create_financial_adjustment(
        db=db,
        data=data,
        recorded_by_user_id=auth.user.id,
    )


@router.get(
    "/adjustments/{adjustment_id}",
    response_model=EventFinancialAdjustmentRead,
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_READ)),
    ],
)
def get_financial_adjustment(
    adjustment_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return event_financial_adjustments.get_financial_adjustment(
        db=db,
        adjustment_id=adjustment_id,
    )


@router.get(
    "/events/{event_id}/adjustments",
    response_model=list[EventFinancialAdjustmentRead],
    dependencies=[
        Depends(require_permission(PermissionCode.PAYMENTS_READ)),
    ],
)
def list_event_financial_adjustments(
    event_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return event_financial_adjustments.list_financial_adjustments_by_event(
        db=db,
        event_id=event_id,
    )
