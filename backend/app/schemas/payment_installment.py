
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.payment_installment import InstallmentStatus, InstallmentType


class PaymentInstallmentCreate(BaseModel):
    installment_number: int = Field(gt=0)
    installment_type: InstallmentType
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    percentage: Decimal | None = Field(
        default=None,
        gt=0,
        le=100,
        max_digits=5,
        decimal_places=2,
    )
    due_date: date

    @model_validator(mode="after")
    def validate_installment(self):
        if self.installment_type == InstallmentType.PERCENTAGE:
            if self.percentage is None:
                raise ValueError(
                    "Percentage is required for percentage installments."
                )

        elif self.installment_type == InstallmentType.FIXED:
            if self.amount is None:
                raise ValueError(
                    "Amount is required for fixed installments."
                )

            if self.percentage is not None:
                raise ValueError(
                    "Percentage must be null for fixed installments."
                )

        return self


class PaymentInstallmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    payment_schedule_id: UUID
    installment_number: int
    installment_type: InstallmentType
    amount: Decimal
    percentage: Decimal | None
    due_date: date
    status: InstallmentStatus
    created_at: datetime
    updated_at: datetime
