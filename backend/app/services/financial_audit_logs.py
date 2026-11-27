
from uuid import UUID

from fastapi import HTTPException, status

from app.db.tenant_session import TenantSession
from app.models.financial_audit_log import FinancialAuditLog
from app.repositories import financial_audit_logs
from app.schemas.financial_audit_log import (
    FinancialAuditEntityType,
    FinancialAuditLogCreate,
)


def record(
    db: TenantSession,
    data: FinancialAuditLogCreate,
    recorded_by_user_id: UUID,
) -> FinancialAuditLog:
    field_name = data.field_name.strip()
    reason = data.reason.strip()

    if not field_name or not reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Field name and reason cannot be empty.",
        )

    audit_log = FinancialAuditLog(
        tenant_id=db.tenant_id,
        event_id=data.event_id,
        entity_type=data.entity_type.value,
        entity_id=data.entity_id,
        field_name=field_name,
        old_value=data.old_value,
        new_value=data.new_value,
        reason=reason,
        recorded_by_user_id=recorded_by_user_id,
    )

    return financial_audit_logs.create(db, audit_log)


def list_by_entity(
    db: TenantSession,
    entity_type: FinancialAuditEntityType,
    entity_id: UUID,
) -> list[FinancialAuditLog]:
    return financial_audit_logs.list_by_entity(
        db,
        entity_type.value,
        entity_id,
    )


def list_by_event_id(
    db: TenantSession,
    event_id: UUID,
) -> list[FinancialAuditLog]:
    return financial_audit_logs.list_by_event_id(
        db,
        event_id,
    )
