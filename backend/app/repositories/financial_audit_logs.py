
from uuid import UUID

from sqlalchemy import select

from app.db.tenant_session import TenantSession
from app.models.financial_audit_log import FinancialAuditLog


def create(
    db: TenantSession,
    audit_log: FinancialAuditLog,
) -> FinancialAuditLog:
    db.add(audit_log)
    db.flush()
    return audit_log


def list_by_entity(
    db: TenantSession,
    entity_type: str,
    entity_id: UUID,
) -> list[FinancialAuditLog]:
    stmt = (
        select(FinancialAuditLog)
        .where(
            FinancialAuditLog.entity_type == entity_type,
            FinancialAuditLog.entity_id == entity_id,
        )
        .order_by(
            FinancialAuditLog.created_at.desc(),
            FinancialAuditLog.id.desc(),
        )
    )

    return list(db.scalars(stmt).all())


def list_by_event_id(
    db: TenantSession,
    event_id: UUID,
) -> list[FinancialAuditLog]:
    stmt = (
        select(FinancialAuditLog)
        .where(FinancialAuditLog.event_id == event_id)
        .order_by(
            FinancialAuditLog.created_at.desc(),
            FinancialAuditLog.id.desc(),
        )
    )

    return list(db.scalars(stmt).all())
