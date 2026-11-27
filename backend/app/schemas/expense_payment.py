
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.payment import PaymentMethod

from app.schemas.expense import ExpensePaymentStatus


class ExpensePaymentCreate(BaseModel):
    expense_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    paid_at: datetime
    method: PaymentMethod = Field(
        validation_alias=AliasChoices("method", "payment_method"),
    )
    external_reference: str | None = Field(default=None, max_length=150)
    notes: str | None = None


class ExpensePaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    expense_id: UUID
    amount: Decimal
    paid_at: datetime
    method: PaymentMethod = Field(
        validation_alias=AliasChoices("method", "payment_method"),
    )
    external_reference: str | None
    notes: str | None
    recorded_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
