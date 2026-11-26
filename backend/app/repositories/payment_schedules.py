
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.tenant_session import TenantSession
from app.models.payment_schedule import PaymentSchedule


def create(
    db: TenantSession,
    payment_schedule: PaymentSchedule,
) -> PaymentSchedule:
    db.add(payment_schedule)
    db.flush()
    return payment_schedule


def get_by_id(
    db: TenantSession,
    payment_schedule_id: UUID,
    *,
    with_installments: bool = False,
) -> PaymentSchedule | None:
    stmt = select(PaymentSchedule).where(
        PaymentSchedule.id == payment_schedule_id,
    )

    if with_installments:
        stmt = stmt.options(
            selectinload(PaymentSchedule.installments),
        )

    return db.scalar(stmt)


def get_by_event_id(
    db: TenantSession,
    event_id: UUID,
    *,
    with_installments: bool = False,
    for_update: bool = False,
) -> PaymentSchedule | None:
    stmt = select(PaymentSchedule).where(
        PaymentSchedule.event_id == event_id,
    )

    if with_installments:
        stmt = stmt.options(
            selectinload(PaymentSchedule.installments),
        )

    if for_update:
        stmt = stmt.with_for_update()

    return db.scalar(stmt)


def get_by_quote_id(
    db: TenantSession,
    quote_id: UUID,
    *,
    with_installments: bool = False,
) -> PaymentSchedule | None:
    stmt = select(PaymentSchedule).where(
        PaymentSchedule.quote_id == quote_id,
    )

    if with_installments:
        stmt = stmt.options(
            selectinload(PaymentSchedule.installments),
        )

    return db.scalar(stmt)


def list_all(
    db: TenantSession,
) -> list[PaymentSchedule]:
    stmt = (
        select(PaymentSchedule)
        .order_by(PaymentSchedule.created_at.desc())
    )

    return list(db.scalars(stmt).all())
