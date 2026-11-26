
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db.tenant_session import TenantSession
from app.models.event_financial_adjustment import (
    EventFinancialAdjustment,
    FinancialAdjustmentType,
)
from app.models.payment import Payment
from app.models.payment_installment import PaymentInstallment
from app.models.payment_refund import (
    PaymentRefund,
    PaymentRefundStatus,
)
from app.repositories import payment_refunds
from app.schemas.payment_refund import PaymentRefundCreate


def _lock_payment_context(
    db: TenantSession,
    payment_id: UUID,
) -> tuple[Payment, PaymentInstallment]:
    payment_reference = db.scalar(
        select(Payment).where(Payment.id == payment_id)
    )

    if payment_reference is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    installment = db.scalar(
        select(PaymentInstallment)
        .where(
            PaymentInstallment.id == payment_reference.installment_id,
        )
        .with_for_update()
    )

    if installment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment installment not found.",
        )

    payment = db.scalar(
        select(Payment)
        .where(Payment.id == payment_id)
        .with_for_update()
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    return payment, installment


def _get_reserved_refund_total(
    db: TenantSession,
    payment_id: UUID,
) -> Decimal:
    total = db.scalar(
        select(
            func.coalesce(
                func.sum(PaymentRefund.amount),
                Decimal("0"),
            )
        ).where(
            PaymentRefund.payment_id == payment_id,
            PaymentRefund.status != PaymentRefundStatus.CANCELLED,
        )
    )

    return total or Decimal("0")


def create_refund(
    db: TenantSession,
    data: PaymentRefundCreate,
    recorded_by_user_id: UUID,
) -> PaymentRefund:
    try:
        payment, installment = _lock_payment_context(
            db,
            data.payment_id,
        )

        reserved_total = _get_reserved_refund_total(
            db,
            payment.id,
        )

        available_amount = payment.amount - reserved_total

        if data.amount > available_amount:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Refund exceeds the available refundable amount "
                    f"of {available_amount}."
                ),
            )

        if data.financial_adjustment_id is not None:
            adjustment = db.scalar(
                select(EventFinancialAdjustment).where(
                    EventFinancialAdjustment.id
                    == data.financial_adjustment_id,
                )
            )

            if adjustment is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Financial adjustment not found.",
                )

            if adjustment.adjustment_type != FinancialAdjustmentType.DISCOUNT:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Refund adjustment must be a discount.",
                )

            if adjustment.event_id != installment.payment_schedule.event_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Discount and payment must belong to the same event.",
                )

        refund = PaymentRefund(
            tenant_id=installment.tenant_id,
            payment_id=payment.id,
            financial_adjustment_id=data.financial_adjustment_id,
            amount=data.amount,
            refund_method=data.refund_method,
            status=PaymentRefundStatus.PENDING,
            reason=data.reason,
            external_reference=data.external_reference,
            notes=data.notes,
            recorded_by_user_id=recorded_by_user_id,
        )

        payment_refunds.create(db, refund)

        db.commit()
        db.refresh(refund)

        return refund

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not create the refund due to a conflicting record.",
        ) from exc

    except Exception:
        db.rollback()
        raise


def process_refund(
    db: TenantSession,
    refund_id: UUID,
    processed_by_user_id: UUID,
) -> PaymentRefund:
    try:
        refund_reference = db.scalar(
            select(PaymentRefund).where(
                PaymentRefund.id == refund_id,
            )
        )

        if refund_reference is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund not found.",
            )

        _lock_payment_context(db, refund_reference.payment_id)

        refund = db.scalar(
            select(PaymentRefund)
            .where(PaymentRefund.id == refund_id)
            .with_for_update()
        )

        if refund is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund not found.",
            )

        if refund.status != PaymentRefundStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only pending refunds can be processed.",
            )

        refund.status = PaymentRefundStatus.COMPLETED
        refund.refunded_at = datetime.now(timezone.utc)
        refund.processed_by_user_id = processed_by_user_id

        db.commit()
        db.refresh(refund)

        return refund

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not process the refund.",
        ) from exc

    except Exception:
        db.rollback()
        raise


def cancel_refund(
    db: TenantSession,
    refund_id: UUID,
) -> PaymentRefund:
    try:
        refund_reference = db.scalar(
            select(PaymentRefund).where(
                PaymentRefund.id == refund_id,
            )
        )

        if refund_reference is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund not found.",
            )

        _lock_payment_context(db, refund_reference.payment_id)

        refund = db.scalar(
            select(PaymentRefund)
            .where(PaymentRefund.id == refund_id)
            .with_for_update()
        )

        if refund is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund not found.",
            )

        if refund.status != PaymentRefundStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only pending refunds can be cancelled.",
            )

        refund.status = PaymentRefundStatus.CANCELLED

        db.commit()
        db.refresh(refund)

        return refund

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not cancel the refund.",
        ) from exc

    except Exception:
        db.rollback()
        raise


def get_refund(
    db: TenantSession,
    refund_id: UUID,
) -> PaymentRefund:
    refund = payment_refunds.get_by_id(
        db,
        refund_id,
    )

    if refund is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refund not found.",
        )

    return refund


def list_refunds_by_payment(
    db: TenantSession,
    payment_id: UUID,
) -> list[PaymentRefund]:
    return payment_refunds.list_by_payment_id(
        db,
        payment_id,
    )


def list_refunds_by_event(
    db: TenantSession,
    event_id: UUID,
) -> list[PaymentRefund]:
    return payment_refunds.list_by_event_id(
        db,
        event_id,
    )
