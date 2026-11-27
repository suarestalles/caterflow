
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventFinancialSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID

    contracted_revenue: Decimal | None
    additional_revenue: Decimal
    discount_amount: Decimal
    final_revenue: Decimal | None

    realized_labor_cost: Decimal
    estimated_labor_cost: Decimal

    operational_expenses: Decimal
    total_realized_cost: Decimal
    total_estimated_cost: Decimal

    realized_operating_result: Decimal | None
    estimated_operating_result: Decimal | None
