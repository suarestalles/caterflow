
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.payment import PaymentMethod


class CompensationPaymentStatus(StrEnum):
    PENDING = "pending"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"


class EmployeeCompensationPaymentCreate(BaseModel):
    assignment_id: UUID

    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    paid_at: datetime
    method: PaymentMethod
    notes: str | None = None


class EmployeeCompensationPaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    assignment_id: UUID
    amount: Decimal
    paid_at: datetime

    method: PaymentMethod = Field(
        validation_alias=AliasChoices("method", "payment_method"),
    )

    notes: str | None
    recorded_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class EmployeeCompensationBalanceRead(BaseModel):
    assignment_id: UUID
    compensation_due: Decimal
    total_paid: Decimal
    outstanding: Decimal
    status: CompensationPaymentStatus
