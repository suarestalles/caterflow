
from uuid import UUID

from sqlalchemy import func, select

from app.db.tenant_session import TenantSession
from app.models.payment_installment import PaymentInstallment


def create(
    db: TenantSession,
    installment: PaymentInstallment,
) -> PaymentInstallment:
    db.add(installment)
    db.flush()
    return installment


def create_many(
    db: TenantSession,
    installments: list[PaymentInstallment],
) -> list[PaymentInstallment]:
    db.add_all(installments)
    db.flush()
    return installments


def get_by_id(
    db: TenantSession,
    installment_id: UUID,
    *,
    for_update: bool = False,
) -> PaymentInstallment | None:
    stmt = select(PaymentInstallment).where(
        PaymentInstallment.id == installment_id,
    )

    if for_update:
        stmt = stmt.with_for_update()

    return db.scalar(stmt)


def list_by_schedule_id(
    db: TenantSession,
    payment_schedule_id: UUID,
    *,
    for_update: bool = False,
) -> list[PaymentInstallment]:
    stmt = (
        select(PaymentInstallment)
        .where(
            PaymentInstallment.payment_schedule_id
            == payment_schedule_id,
        )
        .order_by(PaymentInstallment.installment_number)
    )

    if for_update:
        stmt = stmt.with_for_update()

    return list(db.scalars(stmt).all())


def get_next_installment_number(
    db: TenantSession,
    payment_schedule_id: UUID,
) -> int:
    stmt = select(
        func.coalesce(
            func.max(PaymentInstallment.installment_number),
            0,
        ) + 1,
    ).where(
        PaymentInstallment.payment_schedule_id == payment_schedule_id,
    )

    return db.scalar(stmt) or 1
