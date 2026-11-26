
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db.tenant_session import TenantSession
from app.models.event_financial_adjustment_allocation import EventFinancialAdjustmentAllocation
from app.models.payment import Payment
from app.models.payment_installment import (
    InstallmentStatus,
    PaymentInstallment,
)
from app.models.payment_refund import (
    PaymentRefund,
    PaymentRefundStatus,
)
from app.models.payment_schedule import (
    PaymentSchedule,
    PaymentScheduleStatus,
)
from app.repositories import payments
from app.schemas.payment import PaymentCreate


def _get_installment_net_paid(
    db: TenantSession,
    installment_id: UUID,
) -> Decimal:
    payments_total = db.scalar(
        select(
            func.coalesce(
                func.sum(Payment.amount),
                Decimal("0"),
            )
        ).where(
            Payment.installment_id == installment_id,
        )
    ) or Decimal("0")

    discounts_total = db.scalar(
        select(
            func.coalesce(
                func.sum(EventFinancialAdjustmentAllocation.allocated_amount),
                Decimal("0"),
            )
        ).where(
            EventFinancialAdjustmentAllocation.installment_id
            == installment_id,
        )
    ) or Decimal("0")

    completed_refunds = db.scalar(
        select(
            func.coalesce(
                func.sum(PaymentRefund.amount),
                Decimal("0"),
            )
        )
        .join(
            Payment,
            PaymentRefund.payment_id == Payment.id,
        )
        .where(
            Payment.installment_id == installment_id,
            PaymentRefund.status == PaymentRefundStatus.COMPLETED,
        )
    ) or Decimal("0")

    return payments_total - completed_refunds + discounts_total



def create_payment(
    db: TenantSession,
    data: PaymentCreate,
    recorded_by_user_id: UUID,
) -> Payment:
    try:
        installment_reference = db.scalar(
            select(PaymentInstallment).where(
                PaymentInstallment.id == data.installment_id,
            )
        )

        if installment_reference is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment installment not found.",
            )

        schedule = db.scalar(
            select(PaymentSchedule)
            .where(
                PaymentSchedule.id == installment_reference.payment_schedule_id,
            )
            .with_for_update()
        )

        if schedule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment schedule not found.",
            )

        installment = db.scalar(
            select(PaymentInstallment)
            .where(
                PaymentInstallment.id == data.installment_id,
            )
            .with_for_update()
        )

        if installment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment installment not found.",
            )

        if schedule.status != PaymentScheduleStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot register payments on an inactive schedule.",
            )

        if installment.status == InstallmentStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot register payments on a cancelled installment.",
            )

        net_paid = _get_installment_net_paid(
            db,
            installment.id,
        )

        outstanding = installment.amount - net_paid

        if outstanding <= Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This installment has no outstanding balance.",
            )

        if data.amount > outstanding:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payment amount exceeds the outstanding installment balance.",
            )

        payment = Payment(
            tenant_id=db.tenant_id,
            installment_id=installment.id,
            amount=data.amount,
            received_at=data.received_at,
            payment_method=data.method,
            external_reference=data.external_reference,
            notes=data.notes,
            recorded_by_user_id=recorded_by_user_id,
        )

        payments.create(db, payment)

        updated_net_paid = net_paid + data.amount

        if updated_net_paid >= installment.amount:
            installment.status = InstallmentStatus.PAID
        else:
            installment.status = InstallmentStatus.PARTIALLY_PAID

        db.commit()
        db.refresh(payment)

        return payment

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not register the payment due to a conflicting record.",
        ) from exc

    except Exception:
        db.rollback()
        raise



def get_payment(
    db: TenantSession,
    payment_id: UUID,
) -> Payment:
    payment = payments.get_by_id(
        db,
        payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    return payment


def list_payments_by_installment(
    db: TenantSession,
    installment_id: UUID,
) -> list[Payment]:
    return payments.list_by_installment_id(
        db,
        installment_id,
    )


def list_payments_by_event(
    db: TenantSession,
    event_id: UUID,
) -> list[Payment]:
    return payments.list_by_event_id(
        db,
        event_id,
    )
