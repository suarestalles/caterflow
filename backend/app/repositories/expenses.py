
from uuid import UUID

from sqlalchemy import func, select

from app.db.tenant_session import TenantSession
from app.models.expense import Expense


def create(
    db: TenantSession,
    expense: Expense,
) -> Expense:
    db.add(expense)
    db.flush()
    db.refresh(expense)
    return expense


def get_by_id(
    db: TenantSession,
    expense_id: UUID,
) -> Expense | None:
    stmt = select(Expense).where(Expense.id == expense_id)
    return db.scalar(stmt)


def list_all(
    db: TenantSession,
    *,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[Expense], int]:
    filters = []

    count_stmt = (
        select(func.count())
        .select_from(Expense)
        .where(*filters)
    )
    total = db.scalar(count_stmt) or 0

    stmt = (
        select(Expense)
        .where(*filters)
        .order_by(
            Expense.incurred_at.desc(),
            Expense.created_at.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(stmt).all()), total


def list_by_event_id(
    db: TenantSession,
    event_id: UUID,
) -> list[Expense]:
    stmt = (
        select(Expense)
        .where(Expense.event_id == event_id)
        .order_by(
            Expense.incurred_at.desc(),
            Expense.created_at.desc(),
        )
    )

    return list(db.scalars(stmt).all())


def update(
    db: TenantSession,
    expense: Expense,
    data: dict,
) -> Expense:
    for field, value in data.items():
        setattr(expense, field, value)

    db.flush()
    db.refresh(expense)
    return expense
