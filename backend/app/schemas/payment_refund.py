
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentMethod
from app.models.payment_refund import PaymentRefundStatus


class PaymentRefundCreate(BaseModel):
    payment_id: UUID
    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    refund_method: PaymentMethod
    reason: str = Field(min_length=1, max_length=1000)
    external_reference: str | None = Field(
        default=None,
        max_length=255,
    )
    notes: str | None = None
    financial_adjustment_id: UUID | None = None


class PaymentRefundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    payment_id: UUID
    financial_adjustment_id: UUID | None
    amount: Decimal
    refunded_at: datetime | None
    refund_method: PaymentMethod
    status: PaymentRefundStatus
    reason: str
    external_reference: str | None
    notes: str | None
    recorded_by_user_id: UUID
    processed_by_user_id: UUID | None
    created_at: datetime
    updated_at: datetime
