
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class ClientType(str, Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"


class ClientBase(BaseModel):
    client_type: ClientType = ClientType.INDIVIDUAL

    name: str = Field(min_length=1, max_length=200)
    contact_person: str | None = Field(default=None, max_length=150)

    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)

    address_line: str | None = Field(default=None, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    postal_code: str | None = Field(default=None, max_length=20)
    city: str | None = Field(default=None, max_length=120)
    province: str | None = Field(default=None, max_length=120)
    country: str = Field(default="ES", min_length=2, max_length=2)

    notes: str | None = None

    @field_validator(
        "name",
        "contact_person",
        "phone",
        "address_line",
        "address_line_2",
        "postal_code",
        "city",
        "province",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            value = value.strip().lower()
            return value or None
        return value

    @field_validator("country", mode="before")
    @classmethod
    def normalize_country(cls, value):
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value:
            raise ValueError("Client name cannot be empty.")
        return value

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        if len(value) != 2:
            raise ValueError("Country must use a two-letter ISO code.")
        return value


class ClientCreate(ClientBase):
    @model_validator(mode="after")
    def validate_contact(self):
        if not self.email and not self.phone:
            raise ValueError(
                "At least one contact method (email or phone) is required."
            )
        return self


class ClientUpdate(BaseModel):
    client_type: ClientType | None = None

    name: str | None = Field(default=None, min_length=1, max_length=200)
    contact_person: str | None = Field(default=None, max_length=150)

    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)

    address_line: str | None = Field(default=None, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    postal_code: str | None = Field(default=None, max_length=20)
    city: str | None = Field(default=None, max_length=120)
    province: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, min_length=2, max_length=2)

    notes: str | None = None

    @field_validator(
        "name",
        "contact_person",
        "phone",
        "address_line",
        "address_line_2",
        "postal_code",
        "city",
        "province",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            value = value.strip().lower()
            return value or None
        return value

    @field_validator("country", mode="before")
    @classmethod
    def normalize_country(cls, value):
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @model_validator(mode="after")
    def validate_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self


class ClientResponse(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ClientListResponse(BaseModel):
    items: list[ClientResponse]
    total: int
    offset: int
    limit: int
