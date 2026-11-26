
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.tenant_session import TenantSession
from app.models.event import Event
from app.models.payment_installment import PaymentInstallment
from app.models.payment_schedule import (
    PaymentSchedule,
    PaymentScheduleStatus,
)
from app.models.quote import Quote
from app.repositories import (
    payment_installments,
    payment_schedules,
)
from app.schemas.payment_schedule import PaymentScheduleCreate


CENT = Decimal("0.01")


def _calculate_installment_amounts(
    data: PaymentScheduleCreate,
) -> list[Decimal]:
    installments = sorted(
        data.installments,
        key=lambda item: item.installment_number,
    )

    amounts: list[Decimal] = []
    remaining = data.total_amount

    for index, installment in enumerate(installments):
        is_last = index == len(installments) - 1

        if installment.installment_type.value == "percentage":
            if is_last:
                amount = remaining
            else:
                amount = (
                    data.total_amount
                    * (installment.percentage or Decimal("0"))
                    / Decimal("100")
                ).quantize(CENT, rounding=ROUND_HALF_UP)
        else:
            amount = installment.amount or Decimal("0")

        if amount <= 0 or amount > remaining:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invalid installment amount.",
            )

        amounts.append(amount)
        remaining -= amount

    if remaining != Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Installment amounts do not match the schedule total.",
        )

    return amounts


def create_payment_schedule(
    db: TenantSession,
    data: PaymentScheduleCreate,
) -> PaymentSchedule:
    try:
        event = db.scalar(
            select(Event)
            .where(Event.id == data.event_id)
            .with_for_update()
        )

        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found.",
            )

        quote = db.scalar(
            select(Quote)
            .where(Quote.id == data.quote_id)
            .with_for_update()
        )

        if quote is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found.",
            )

        if quote.event_id != event.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Quote is not associated with this event.",
            )

        quote_status = getattr(quote.status, "value", quote.status)

        if quote_status != "accepted":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only accepted quotes can have a payment schedule.",
            )

        existing_event_schedule = (
            payment_schedules.get_by_event_id(
                db,
                event.id,
            )
        )

        if existing_event_schedule is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A payment schedule already exists for this event.",
            )

        existing_quote_schedule = (
            payment_schedules.get_by_quote_id(
                db,
                quote.id,
            )
        )

        if existing_quote_schedule is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A payment schedule already exists for this quote.",
            )

        installment_amounts = _calculate_installment_amounts(data)

        schedule = PaymentSchedule(
            tenant_id=event.tenant_id,
            event_id=event.id,
            quote_id=quote.id,
            total_amount=data.total_amount,
            currency=data.currency,
            payment_terms_snapshot=data.payment_terms_snapshot,
            status=PaymentScheduleStatus.ACTIVE,
        )

        payment_schedules.create(db, schedule)

        installments = [
            PaymentInstallment(
                tenant_id=event.tenant_id,
                payment_schedule_id=schedule.id,
                installment_number=installment.installment_number,
                installment_type=installment.installment_type,
                amount=amount,
                percentage=installment.percentage,
                due_date=installment.due_date,
            )
            for installment, amount in zip(
                sorted(
                    data.installments,
                    key=lambda item: item.installment_number,
                ),
                installment_amounts,
                strict=True,
            )
        ]

        payment_installments.create_many(
            db,
            installments,
        )

        db.commit()
        db.refresh(schedule)

        return schedule

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not create the payment schedule due to a conflicting record.",
        ) from exc

    except Exception:
        db.rollback()
        raise


def get_payment_schedule(
    db: TenantSession,
    payment_schedule_id: UUID,
) -> PaymentSchedule:
    schedule = payment_schedules.get_by_id(
        db,
        payment_schedule_id,
        with_installments=True,
    )

    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment schedule not found.",
        )

    return schedule


def get_payment_schedule_by_event(
    db: TenantSession,
    event_id: UUID,
) -> PaymentSchedule:
    schedule = payment_schedules.get_by_event_id(
        db,
        event_id,
        with_installments=True,
    )

    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment schedule not found for this event.",
        )

    return schedule
