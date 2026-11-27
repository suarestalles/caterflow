
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.tenant_session import TenantSession
from app.models.event import Event, EventStatus
from app.models.expense import Expense
from app.repositories import expenses as expense_repository
from app.repositories import expense_payments as expense_payment_repository
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.schemas.financial_audit_log import (
    FinancialAuditEntityType,
    FinancialAuditLogCreate,
)
from app.services import financial_audit_logs


def create(
    db: TenantSession,
    data: ExpenseCreate,
    recorded_by_user_id: UUID,
) -> Expense:
    try:
        expense_data = data.model_dump()
        expense_data["category"] = data.category.value

        expense = Expense(
            **expense_data,
            tenant_id=db.tenant_id,
            recorded_by_user_id=recorded_by_user_id,
        )

        expense = expense_repository.create(db, expense)
        db.commit()
        db.refresh(expense)

        return expense

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not create expense. Check the event and related records.",
        )


def get(
    db: TenantSession,
    expense_id: UUID,
) -> Expense:
    expense = expense_repository.get_by_id(db, expense_id)

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found.",
        )

    return expense


def list_all(
    db: TenantSession,
    *,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[Expense], int]:
    return expense_repository.list_all(
        db,
        offset=offset,
        limit=limit,
    )


def list_by_event_id(
    db: TenantSession,
    event_id: UUID,
) -> list[Expense]:
    return expense_repository.list_by_event_id(db, event_id)


def get_balance(
    db: TenantSession,
    expense_id: UUID,
) -> dict:
    expense = get(db, expense_id)

    total_paid = expense_payment_repository.get_total_paid(
        db,
        expense_id,
    )

    outstanding = expense.amount - total_paid

    if total_paid == 0:
        payment_status = "pending"
    elif outstanding == 0:
        payment_status = "paid"
    else:
        payment_status = "partially_paid"

    return {
        "expense_id": expense.id,
        "expense_amount": expense.amount,
        "total_paid": total_paid,
        "outstanding": outstanding,
        "status": payment_status,
    }


def update(
    db: TenantSession,
    expense_id: UUID,
    data: ExpenseUpdate,
    recorded_by_user_id: UUID | None = None,
) -> Expense:
    try:
        stmt = (
            select(Expense)
            .where(Expense.id == expense_id)
            .with_for_update()
        )
        expense = db.scalar(stmt)

        if expense is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found.",
            )

        update_data = data.model_dump(exclude_unset=True)
        reason = update_data.pop("reason", None)

        if "category" in update_data and update_data["category"] is not None:
            update_data["category"] = update_data["category"].value

        new_amount = update_data.get("amount", expense.amount)
        amount_changed = new_amount != expense.amount

        total_paid = expense_payment_repository.get_total_paid(
            db,
            expense_id,
        )

        if new_amount < total_paid:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Expense amount cannot be lower than the total already paid.",
            )

        if amount_changed and expense.event_id is not None:
            event = db.scalar(
                select(Event).where(Event.id == expense.event_id)
            )

            if (
                event is not None
                and event.status == EventStatus.COMPLETED.value
            ):
                normalized_reason = reason.strip() if reason else ""

                if not normalized_reason:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail=(
                            "A reason is required to correct an expense "
                            "after the event has been completed."
                        ),
                    )

                if recorded_by_user_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="The user responsible for the correction is required.",
                    )

                financial_audit_logs.record(
                    db,
                    data=FinancialAuditLogCreate(
                        event_id=expense.event_id,
                        entity_type=FinancialAuditEntityType.EXPENSE,
                        entity_id=expense.id,
                        field_name="amount",
                        old_value=format(expense.amount, ".2f"),
                        new_value=format(new_amount, ".2f"),
                        reason=normalized_reason,
                    ),
                    recorded_by_user_id=recorded_by_user_id,
                )

        expense = expense_repository.update(
            db,
            expense,
            update_data,
        )

        db.commit()
        db.refresh(expense)

        return expense

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not update expense. Check the related records.",
        )
