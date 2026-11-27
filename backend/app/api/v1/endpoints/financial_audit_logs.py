
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_tenant_db, require_permission
from app.core.permissions import PermissionCode
from app.db.tenant_session import TenantSession
from app.schemas.financial_audit_log import (
    FinancialAuditEntityType,
    FinancialAuditLogRead,
)
from app.services import financial_audit_logs

router = APIRouter(tags=["Financial Audit Logs"])


@router.get(
    "/entities/{entity_type}/{entity_id}",
    response_model=list[FinancialAuditLogRead],
    dependencies=[Depends(require_permission(PermissionCode.FINANCE_READ))],
)
def list_entity_audit_logs(
    entity_type: FinancialAuditEntityType,
    entity_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return financial_audit_logs.list_by_entity(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
    )


@router.get(
    "/events/{event_id}",
    response_model=list[FinancialAuditLogRead],
    dependencies=[Depends(require_permission(PermissionCode.FINANCE_READ))],
)
def list_event_audit_logs(
    event_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    return financial_audit_logs.list_by_event_id(
        db=db,
        event_id=event_id,
    )
