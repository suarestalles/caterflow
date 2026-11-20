
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.product import ProductUnit
from app.models.quote import QuoteStatus


class QuoteItemCreate(BaseModel):
    product_id: UUID | None = None

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    unit: ProductUnit | None = None

    quantity: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    unit_price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    position: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        if not value:
            raise ValueError("Item name cannot be empty.")

        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None

    @model_validator(mode="after")
    def validate_item_source(self):
        if self.product_id is None:
            if self.name is None:
                raise ValueError(
                    "Item name is required when no catalog product is selected."
                )

            if self.unit_price is None:
                raise ValueError(
                    "Unit price is required when no catalog product is selected."
                )

        return self


class QuoteItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    quote_id: UUID
    product_id: UUID | None
    name: str
    description: str | None
    unit: ProductUnit | None
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    position: int


class QuoteCreate(BaseModel):
    client_id: UUID
    event_id: UUID | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    valid_until: date | None = None
    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    tax_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    notes: str | None = None
    terms: str | None = None
    items: list[QuoteItemCreate] = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Quote title cannot be empty.")
        return value

    @field_validator("description", "notes", "terms")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None


class QuoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: UUID | None = None
    event_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    valid_until: date | None = None
    discount_amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    tax_amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    notes: str | None = None
    terms: str | None = None
    items: list[QuoteItemCreate] | None = Field(default=None, min_length=1)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        if not value:
            raise ValueError("Quote title cannot be empty.")

        return value

    @field_validator("description", "notes", "terms")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None


class QuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    client_id: UUID
    event_id: UUID | None
    quote_number: str
    title: str
    description: str | None
    status: QuoteStatus
    valid_until: date | None
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    notes: str | None
    terms: str | None
    created_at: datetime | None
    updated_at: datetime | None
    items: list[QuoteItemResponse]


class QuoteListResponse(BaseModel):
    items: list[QuoteResponse]
    total: int
    offset: int
    limit: int
