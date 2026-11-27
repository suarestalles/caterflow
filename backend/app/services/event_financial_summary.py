
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select

from app.db.tenant_session import TenantSession
from app.models.event import Event
from app.models.event_financial_adjustment import (
    EventFinancialAdjustment,
    FinancialAdjustmentType,
)
from app.models.event_staff_assignment import (
    EventStaffAssignment,
    EventStaffAssignmentStatus,
)
from app.models.expense import Expense
from app.models.quote import Quote, QuoteStatus
from app.schemas.event_financial_summary import EventFinancialSummaryRead


ZERO = Decimal("0.00")


def get_event_financial_summary(
    db: TenantSession,
    event_id: UUID,
) -> EventFinancialSummaryRead:
    event = db.scalar(
        select(Event).where(Event.id == event_id)
    )

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )

    accepted_quotes = list(
        db.scalars(
            select(Quote).where(
                Quote.event_id == event_id,
                Quote.status == QuoteStatus.ACCEPTED.value,
            )
        ).all()
    )

    if len(accepted_quotes) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Multiple accepted quotes found for this event.",
        )

    contracted_revenue = (
        accepted_quotes[0].total_amount
        if accepted_quotes
        else None
    )

    adjustments = list(
        db.scalars(
            select(EventFinancialAdjustment).where(
                EventFinancialAdjustment.event_id == event_id,
            )
        ).all()
    )

    additional_revenue = sum(
        (
            adjustment.amount
            for adjustment in adjustments
            if adjustment.adjustment_type
            == FinancialAdjustmentType.ADDITIONAL.value
        ),
        ZERO,
    )

    discount_amount = sum(
        (
            adjustment.amount
            for adjustment in adjustments
            if adjustment.adjustment_type
            == FinancialAdjustmentType.DISCOUNT.value
        ),
        ZERO,
    )

    final_revenue = (
        contracted_revenue + additional_revenue - discount_amount
        if contracted_revenue is not None
        else None
    )

    assignments = list(
        db.scalars(
            select(EventStaffAssignment).where(
                EventStaffAssignment.event_id == event_id,
            )
        ).all()
    )

    realized_labor_cost = ZERO
    estimated_labor_cost = ZERO

    for assignment in assignments:
        if assignment.status == EventStaffAssignmentStatus.COMPLETED.value:
            realized_labor_cost += assignment.actual_compensation or ZERO
        elif assignment.status in {
            EventStaffAssignmentStatus.ASSIGNED.value,
            EventStaffAssignmentStatus.CONFIRMED.value,
        }:
            estimated_labor_cost += assignment.planned_compensation

        operational_expenses = db.scalar(
            select(func.coalesce(func.sum(Expense.amount), ZERO)).where(
                Expense.event_id == event_id,
            )
        ) or ZERO

    total_realized_cost = (
        realized_labor_cost + operational_expenses
    )

    total_estimated_cost = (
        total_realized_cost + estimated_labor_cost
    )

    realized_operating_result = (
        final_revenue - total_realized_cost
        if final_revenue is not None
        else None
    )

    estimated_operating_result = (
        final_revenue - total_estimated_cost
        if final_revenue is not None
        else None
    )

    return EventFinancialSummaryRead(
        event_id=event_id,
        contracted_revenue=contracted_revenue,
        additional_revenue=additional_revenue,
        discount_amount=discount_amount,
        final_revenue=final_revenue,
        realized_labor_cost=realized_labor_cost,
        estimated_labor_cost=estimated_labor_cost,
        operational_expenses=operational_expenses,
        total_realized_cost=total_realized_cost,
        total_estimated_cost=total_estimated_cost,
        realized_operating_result=realized_operating_result,
        estimated_operating_result=estimated_operating_result,
    )
