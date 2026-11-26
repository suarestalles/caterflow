
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.tenant_session import TenantSession
from app.models.event_financial_adjustment import (
    EventFinancialAdjustment,
)


def create(
    db: TenantSession,
    adjustment: EventFinancialAdjustment,
) -> EventFinancialAdjustment:
    db.add(adjustment)
    db.flush()
    return adjustment


def get_by_id(
    db: TenantSession,
    adjustment_id: UUID,
    *,
    with_allocations: bool = False,
) -> EventFinancialAdjustment | None:
    stmt = select(EventFinancialAdjustment).where(
        EventFinancialAdjustment.id == adjustment_id,
    )

    if with_allocations:
        stmt = stmt.options(
            selectinload(EventFinancialAdjustment.allocations),
        )

    return db.scalar(stmt)


def list_by_event_id(
    db: TenantSession,
    event_id: UUID,
    *,
    with_allocations: bool = False,
) -> list[EventFinancialAdjustment]:
    stmt = (
        select(EventFinancialAdjustment)
        .where(EventFinancialAdjustment.event_id == event_id)
        .order_by(EventFinancialAdjustment.created_at.desc())
    )

    if with_allocations:
        stmt = stmt.options(
            selectinload(EventFinancialAdjustment.allocations),
        )

    return list(db.scalars(stmt).all())
