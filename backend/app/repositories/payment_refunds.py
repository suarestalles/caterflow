
from uuid import UUID

from sqlalchemy import select

from app.db.tenant_session import TenantSession
from app.models.payment import Payment
from app.models.payment_installment import PaymentInstallment
from app.models.payment_refund import PaymentRefund
from app.models.payment_schedule import PaymentSchedule


def create(
    db: TenantSession,
    refund: PaymentRefund,
) -> PaymentRefund:
    db.add(refund)
    db.flush()
    return refund


def get_by_id(
    db: TenantSession,
    refund_id: UUID,
    *,
    for_update: bool = False,
) -> PaymentRefund | None:
    stmt = select(PaymentRefund).where(
        PaymentRefund.id == refund_id,
    )

    if for_update:
        stmt = stmt.with_for_update()

    return db.scalar(stmt)


def list_by_payment_id(
    db: TenantSession,
    payment_id: UUID,
) -> list[PaymentRefund]:
    stmt = (
        select(PaymentRefund)
        .where(PaymentRefund.payment_id == payment_id)
        .order_by(PaymentRefund.created_at.desc())
    )

    return list(db.scalars(stmt).all())


def list_by_event_id(
    db: TenantSession,
    event_id: UUID,
) -> list[PaymentRefund]:
    stmt = (
        select(PaymentRefund)
        .join(
            Payment,
            PaymentRefund.payment_id == Payment.id,
        )
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
        .order_by(PaymentRefund.created_at.desc())
    )

    return list(db.scalars(stmt).all())
