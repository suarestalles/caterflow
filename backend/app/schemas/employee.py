
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class EmploymentType(StrEnum):
    EMPLOYEE = "employee"
    FREELANCER = "freelancer"


class DefaultCompensationType(StrEnum):
    HOURLY = "hourly"
    FIXED = "fixed"


class EmployeeBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    employment_type: EmploymentType = EmploymentType.EMPLOYEE

    position: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    notes: str | None = None

    default_compensation_type: DefaultCompensationType | None = None
    default_compensation_rate: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )

    @field_validator("name", "position", "phone", "notes", mode="before")
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

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value:
            raise ValueError("Employee name cannot be empty.")
        return value

    @model_validator(mode="after")
    def validate_default_compensation(self):
        if (
            self.default_compensation_type is None
            and self.default_compensation_rate is None
        ):
            return self

        if (
            self.default_compensation_type is None
            or self.default_compensation_rate is None
        ):
            raise ValueError(
                "Default compensation type and rate must be provided together."
            )

        return self


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    employment_type: EmploymentType | None = None

    position: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    notes: str | None = None

    default_compensation_type: DefaultCompensationType | None = None
    default_compensation_rate: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )

    @field_validator("name", "position", "phone", "notes", mode="before")
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

    @model_validator(mode="after")
    def validate_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        compensation_fields = {
            "default_compensation_type",
            "default_compensation_rate",
        }

        provided_compensation_fields = (
            compensation_fields & self.model_fields_set
        )

        if provided_compensation_fields and (
            provided_compensation_fields != compensation_fields
        ):
            raise ValueError(
                "Default compensation type and rate must be updated together."
            )

        if (
            self.default_compensation_type is not None
            and self.default_compensation_rate is None
        ) or (
            self.default_compensation_type is None
            and self.default_compensation_rate is not None
        ):
            raise ValueError(
                "Default compensation type and rate must be provided together."
            )

        return self


class EmployeeResponse(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EmployeeListResponse(BaseModel):
    items: list[EmployeeResponse]
    total: int
    offset: int
    limit: int
