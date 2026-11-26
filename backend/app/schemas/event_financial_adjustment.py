
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.models.event_financial_adjustment import (
    FinancialAdjustmentType,
)
from app.schemas.event_financial_adjustment_allocation import (
    EventFinancialAdjustmentAllocationRead,
)


class EventFinancialAdjustmentCreate(BaseModel):
    event_id: UUID
    adjustment_type: FinancialAdjustmentType
    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    reason: str = Field(min_length=1, max_length=1000)
    due_date: date | None = None

    @model_validator(mode="after")
    def validate_adjustment(self):
        if self.adjustment_type == FinancialAdjustmentType.ADDITIONAL:
            if self.due_date is None:
                raise ValueError(
                    "Due date is required for additional charges."
                )

        elif self.adjustment_type == FinancialAdjustmentType.DISCOUNT:
            if self.due_date is not None:
                raise ValueError(
                    "Due date must be null for discounts."
                )

        return self


class EventFinancialAdjustmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    event_id: UUID
    adjustment_type: FinancialAdjustmentType
    amount: Decimal
    reason: str
    recorded_by_user_id: UUID
    created_installment_id: UUID | None
    allocations: list[EventFinancialAdjustmentAllocationRead] = Field(
        default_factory=list
    )
    created_at: datetime
    updated_at: datetime
