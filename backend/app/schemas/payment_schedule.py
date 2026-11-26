
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.payment_schedule import PaymentScheduleStatus
from app.schemas.payment_installment import (
    PaymentInstallmentCreate,
    PaymentInstallmentRead,
)


class PaymentScheduleCreate(BaseModel):
    event_id: UUID
    quote_id: UUID
    total_amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    payment_terms_snapshot: str | None = None
    installments: list[PaymentInstallmentCreate] = Field(min_length=1)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.upper()

        if not value.isalpha():
            raise ValueError("Currency must contain three letters.")

        return value

    @model_validator(mode="after")
    def validate_installments(self):
        numbers = [
            installment.installment_number
            for installment in self.installments
        ]

        if len(numbers) != len(set(numbers)):
            raise ValueError(
                "Installment numbers must be unique."
            )

        types = {
            installment.installment_type
            for installment in self.installments
        }

        if len(types) > 1:
            raise ValueError(
                "All installments must use the same calculation type."
            )

        installment_type = next(iter(types))

        if installment_type.value == "percentage":
            total_percentage = sum(
                installment.percentage or Decimal("0")
                for installment in self.installments
            )

            if total_percentage != Decimal("100"):
                raise ValueError(
                    "Percentage installments must total 100%."
                )

        else:
            total_installments = sum(
                (
                    installment.amount or Decimal("0")
                    for installment in self.installments
                ),
                Decimal("0"),
            )

            if total_installments != self.total_amount:
                raise ValueError(
                    "Fixed installments must equal the schedule total."
                )

        return self


class PaymentScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    event_id: UUID
    quote_id: UUID
    total_amount: Decimal
    currency: str
    payment_terms_snapshot: str | None
    status: PaymentScheduleStatus
    installments: list[PaymentInstallmentRead] = []
    created_at: datetime
    updated_at: datetime
