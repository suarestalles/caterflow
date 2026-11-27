
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExpenseCategory(StrEnum):
    FOOD = "food"
    BEVERAGES = "beverages"
    TRANSPORT = "transport"
    FUEL = "fuel"
    EQUIPMENT_RENTAL = "equipment_rental"
    DECORATION = "decoration"
    PARKING = "parking"
    DISPOSABLES = "disposables"
    EXTERNAL_SERVICES = "external_services"
    OTHER = "other"


class ExpenseBase(BaseModel):
    event_id: UUID | None = None
    category: ExpenseCategory
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    incurred_at: date
    due_date: date | None = None
    supplier_name: str | None = Field(default=None, max_length=150)
    invoice_reference: str | None = Field(default=None, max_length=150)
    notes: str | None = None


class ExpenseCreate(ExpenseBase):
    pass



class ExpenseUpdate(BaseModel):
    event_id: UUID | None = None
    category: ExpenseCategory | None = None
    description: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    incurred_at: date | None = None
    due_date: date | None = None
    supplier_name: str | None = Field(default=None, max_length=150)
    invoice_reference: str | None = Field(default=None, max_length=150)
    notes: str | None = None
    reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_update(self):
        required_fields = {
            "category",
            "description",
            "amount",
            "incurred_at",
        }

        for field in required_fields:
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")

        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

        return self



class ExpenseRead(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    recorded_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class ExpensePaymentStatus(StrEnum):
    PENDING = "pending"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"


class ExpenseBalanceRead(BaseModel):
    expense_id: UUID
    expense_amount: Decimal
    total_paid: Decimal
    outstanding: Decimal
    status: ExpensePaymentStatus


class ExpenseListRead(BaseModel):
    items: list[ExpenseRead]
    total: int
    offset: int
    limit: int
