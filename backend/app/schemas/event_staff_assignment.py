
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class EventStaffAssignmentStatus(StrEnum):
    ASSIGNED = "assigned"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CompensationType(StrEnum):
    HOURLY = "hourly"
    FIXED = "fixed"


class EventStaffAssignmentCreate(BaseModel):
    event_id: UUID
    employee_id: UUID

    position: str = Field(min_length=1, max_length=120)

    planned_hours: Decimal = Field(
        ge=Decimal("0"),
        max_digits=8,
        decimal_places=2,
    )

    compensation_type: CompensationType
    compensation_rate: Decimal = Field(
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )

    notes: str | None = None

    @field_validator("position", "notes", mode="before")
    @classmethod
    def normalize_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("position")
    @classmethod
    def validate_position(cls, value: str) -> str:
        if not value:
            raise ValueError("Assignment position cannot be empty.")
        return value


class EventStaffAssignmentUpdate(BaseModel):
    position: str | None = Field(default=None, min_length=1, max_length=120)

    status: EventStaffAssignmentStatus | None = None

    planned_hours: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        max_digits=8,
        decimal_places=2,
    )

    actual_hours: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        max_digits=8,
        decimal_places=2,
    )

    compensation_type: CompensationType | None = None

    compensation_rate: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )

    actual_compensation: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
    )

    notes: str | None = None

    @field_validator("position", "notes", mode="before")
    @classmethod
    def normalize_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @model_validator(mode="after")
    def validate_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self


class EventStaffAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID

    event_id: UUID
    employee_id: UUID

    position: str
    status: EventStaffAssignmentStatus

    planned_hours: Decimal
    actual_hours: Decimal | None

    compensation_type: CompensationType
    compensation_rate: Decimal
    planned_compensation: Decimal
    actual_compensation: Decimal | None

    notes: str | None

    created_at: datetime
    updated_at: datetime


class EventStaffAssignmentListResponse(BaseModel):
    items: list[EventStaffAssignmentResponse]
    total: int
    offset: int
    limit: int
