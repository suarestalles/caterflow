
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select

from app.db.tenant_session import TenantSession
from app.models.expense_payment import ExpensePayment


def create(
    db: TenantSession,
    payment: ExpensePayment,
) -> ExpensePayment:
    db.add(payment)
    db.flush()
    db.refresh(payment)
    return payment


def get_by_id(
    db: TenantSession,
    payment_id: UUID,
) -> ExpensePayment | None:
    stmt = select(ExpensePayment).where(
        ExpensePayment.id == payment_id
    )
    return db.scalar(stmt)


def list_by_expense_id(
    db: TenantSession,
    expense_id: UUID,
) -> list[ExpensePayment]:
    stmt = (
        select(ExpensePayment)
        .where(ExpensePayment.expense_id == expense_id)
        .order_by(
            ExpensePayment.paid_at.desc(),
            ExpensePayment.created_at.desc(),
        )
    )

    return list(db.scalars(stmt).all())


def get_total_paid(
    db: TenantSession,
    expense_id: UUID,
) -> Decimal:
    stmt = select(
        func.coalesce(
            func.sum(ExpensePayment.amount),
            Decimal("0"),
        )
    ).where(
        ExpensePayment.expense_id == expense_id
    )

    return db.scalar(stmt) or Decimal("0")
