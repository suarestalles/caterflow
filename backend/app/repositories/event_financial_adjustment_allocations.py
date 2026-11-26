
from uuid import UUID

from sqlalchemy import select

from app.db.tenant_session import TenantSession
from app.models.event_financial_adjustment_allocation import (
    EventFinancialAdjustmentAllocation,
)


def create(
    db: TenantSession,
    allocation: EventFinancialAdjustmentAllocation,
) -> EventFinancialAdjustmentAllocation:
    db.add(allocation)
    db.flush()
    return allocation


def create_many(
    db: TenantSession,
    allocations: list[EventFinancialAdjustmentAllocation],
) -> list[EventFinancialAdjustmentAllocation]:
    db.add_all(allocations)
    db.flush()
    return allocations


def list_by_adjustment_id(
    db: TenantSession,
    adjustment_id: UUID,
) -> list[EventFinancialAdjustmentAllocation]:
    stmt = (
        select(EventFinancialAdjustmentAllocation)
        .where(
            EventFinancialAdjustmentAllocation.adjustment_id
            == adjustment_id,
        )
        .order_by(EventFinancialAdjustmentAllocation.created_at)
    )

    return list(db.scalars(stmt).all())


def list_by_installment_id(
    db: TenantSession,
    installment_id: UUID,
) -> list[EventFinancialAdjustmentAllocation]:
    stmt = (
        select(EventFinancialAdjustmentAllocation)
        .where(
            EventFinancialAdjustmentAllocation.installment_id
            == installment_id,
        )
        .order_by(EventFinancialAdjustmentAllocation.created_at)
    )

    return list(db.scalars(stmt).all())
