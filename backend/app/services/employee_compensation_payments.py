
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db.tenant_session import TenantSession
from app.models.employee_compensation_payment import (
    EmployeeCompensationPayment,
)
from app.models.event_staff_assignment import (
    EventStaffAssignment,
    EventStaffAssignmentStatus,
)
from app.repositories import employee_compensation_payments as payment_repository
from app.schemas.employee_compensation_payment import (
    CompensationPaymentStatus,
    EmployeeCompensationBalanceRead,
    EmployeeCompensationPaymentCreate,
)


def create_employee_compensation_payment(
    db: TenantSession,
    data: EmployeeCompensationPaymentCreate,
    recorded_by_user_id: UUID,
) -> EmployeeCompensationPayment:
    try:
        # Lock the assignment to serialize concurrent payment registrations.
        assignment = db.scalar(
            select(EventStaffAssignment)
            .where(
                EventStaffAssignment.id == data.assignment_id,
            )
            .with_for_update()
        )

        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event staff assignment not found.",
            )

        if assignment.status != EventStaffAssignmentStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee compensation can only be paid after assignment completion.",
            )

        if assignment.actual_compensation is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The assignment has no finalized compensation amount.",
            )

        total_paid = _get_total_paid(
            db,
            assignment.id,
        )

        outstanding = assignment.actual_compensation - total_paid

        if outstanding <= Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This assignment has no outstanding compensation.",
            )

        if data.amount > outstanding:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payment amount exceeds the outstanding compensation.",
            )

        payment = EmployeeCompensationPayment(
            tenant_id=db.tenant_id,
            assignment_id=assignment.id,
            amount=data.amount,
            paid_at=data.paid_at,
            payment_method=data.method.value,
            notes=data.notes,
            recorded_by_user_id=recorded_by_user_id,
        )

        payment_repository.create(db, payment)

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
            detail="Could not register the compensation payment due to a conflicting record.",
        ) from exc

    except Exception:
        db.rollback()
        raise


def get_employee_compensation_payment(
    db: TenantSession,
    payment_id: UUID,
) -> EmployeeCompensationPayment:
    payment = payment_repository.get_by_id(
        db,
        payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee compensation payment not found.",
        )

    return payment


def list_employee_compensation_payments(
    db: TenantSession,
    assignment_id: UUID,
) -> list[EmployeeCompensationPayment]:
    assignment = db.scalar(
        select(EventStaffAssignment).where(
            EventStaffAssignment.id == assignment_id,
        )
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event staff assignment not found.",
        )

    return payment_repository.list_by_assignment_id(
        db,
        assignment_id,
    )


def get_employee_compensation_balance(
    db: TenantSession,
    assignment_id: UUID,
) -> EmployeeCompensationBalanceRead:
    assignment = db.scalar(
        select(EventStaffAssignment).where(
            EventStaffAssignment.id == assignment_id,
        )
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event staff assignment not found.",
        )

    if assignment.actual_compensation is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The assignment has no finalized compensation amount.",
        )

    total_paid = _get_total_paid(
        db,
        assignment.id,
    )

    outstanding = assignment.actual_compensation - total_paid

    if total_paid <= Decimal("0"):
        payment_status = CompensationPaymentStatus.PENDING
    elif outstanding > Decimal("0"):
        payment_status = CompensationPaymentStatus.PARTIALLY_PAID
    else:
        payment_status = CompensationPaymentStatus.PAID

    return EmployeeCompensationBalanceRead(
        assignment_id=assignment.id,
        compensation_due=assignment.actual_compensation,
        total_paid=total_paid,
        outstanding=outstanding,
        status=payment_status,
    )


def _get_total_paid(
    db: TenantSession,
    assignment_id: UUID,
) -> Decimal:
    total = db.scalar(
        select(
            func.coalesce(
                func.sum(EmployeeCompensationPayment.amount),
                Decimal("0"),
            )
        ).where(
            EmployeeCompensationPayment.assignment_id == assignment_id,
        )
    )

    return total or Decimal("0")
