
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.tenant_session import TenantSession
from app.models.expense import Expense
from app.models.expense_payment import ExpensePayment
from app.repositories import expense_payments as payment_repository
from app.schemas.expense import ExpensePaymentStatus
from app.schemas.expense_payment import ExpensePaymentCreate


def create(
    db: TenantSession,
    data: ExpensePaymentCreate,
    recorded_by_user_id: UUID,
) -> ExpensePayment:
    try:
        stmt = (
            select(Expense)
            .where(Expense.id == data.expense_id)
            .with_for_update()
        )
        expense = db.scalar(stmt)

        if expense is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found.",
            )

        total_paid = payment_repository.get_total_paid(
            db,
            expense.id,
        )

        outstanding = expense.amount - total_paid

        if outstanding <= 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Expense has already been fully paid.",
            )

        if data.amount > outstanding:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Payment exceeds outstanding balance of {outstanding}.",
            )

        payment = ExpensePayment(
            tenant_id=db.tenant_id,
            expense_id=expense.id,
            amount=data.amount,
            paid_at=data.paid_at,
            payment_method=data.method.value,
            external_reference=data.external_reference,
            notes=data.notes,
            recorded_by_user_id=recorded_by_user_id,
        )

        payment = payment_repository.create(db, payment)

        db.commit()
        db.refresh(payment)

        return payment

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not register expense payment.",
        )


def get(
    db: TenantSession,
    payment_id: UUID,
) -> ExpensePayment:
    payment = payment_repository.get_by_id(db, payment_id)

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense payment not found.",
        )

    return payment


def list_by_expense_id(
    db: TenantSession,
    expense_id: UUID,
) -> list[ExpensePayment]:
    stmt = select(Expense).where(Expense.id == expense_id)

    if db.scalar(stmt) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found.",
        )

    return payment_repository.list_by_expense_id(
        db,
        expense_id,
    )


def get_balance(
    db: TenantSession,
    expense_id: UUID,
) -> dict:
    stmt = select(Expense).where(Expense.id == expense_id)
    expense = db.scalar(stmt)

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found.",
        )

    total_paid = payment_repository.get_total_paid(
        db,
        expense_id,
    )

    outstanding = expense.amount - total_paid

    if total_paid == 0:
        payment_status = ExpensePaymentStatus.PENDING
    elif outstanding == 0:
        payment_status = ExpensePaymentStatus.PAID
    else:
        payment_status = ExpensePaymentStatus.PARTIALLY_PAID

    return {
        "expense_id": expense.id,
        "expense_amount": expense.amount,
        "total_paid": total_paid,
        "outstanding": outstanding,
        "status": payment_status,
    }
