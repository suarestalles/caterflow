
from uuid import UUID

from sqlalchemy import select

from app.db.tenant_session import TenantSession
from app.models.payment import Payment
from app.models.payment_installment import PaymentInstallment
from app.models.payment_schedule import PaymentSchedule


def create(
    db: TenantSession,
    payment: Payment,
) -> Payment:
    db.add(payment)
    db.flush()
    return payment


def get_by_id(
    db: TenantSession,
    payment_id: UUID,
    *,
    for_update: bool = False,
) -> Payment | None:
    stmt = select(Payment).where(
        Payment.id == payment_id,
    )

    if for_update:
        stmt = stmt.with_for_update()

    return db.scalar(stmt)


def list_by_installment_id(
    db: TenantSession,
    installment_id: UUID,
) -> list[Payment]:
    stmt = (
        select(Payment)
        .where(Payment.installment_id == installment_id)
        .order_by(Payment.received_at.desc())
    )

    return list(db.scalars(stmt).all())


def list_by_event_id(
    db: TenantSession,
    event_id: UUID,
) -> list[Payment]:
    stmt = (
        select(Payment)
        .join(
            PaymentInstallment,
            Payment.installment_id == PaymentInstallment.id,
        )
        .join(
            PaymentSchedule,
            PaymentInstallment.payment_schedule_id
            == PaymentSchedule.id,
        )
        .where(PaymentSchedule.event_id == event_id)
        .order_by(Payment.received_at.desc())
    )

    return list(db.scalars(stmt).all())
