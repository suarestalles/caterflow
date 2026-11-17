from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class EventStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EventBase(BaseModel):
    client_id: UUID
    name: str = Field(min_length=1, max_length=200)

    starts_at: datetime
    ends_at: datetime

    guest_count: int = Field(gt=0)

    status: EventStatus = EventStatus.DRAFT

    address_line: str | None = Field(default=None, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    postal_code: str | None = Field(default=None, max_length=20)
    city: str | None = Field(default=None, max_length=120)
    province: str | None = Field(default=None, max_length=120)
    country: str = Field(default="ES", min_length=2, max_length=2)

    notes: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError("Event name cannot be empty.")

        return value

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        value = value.strip().upper()

        if len(value) != 2:
            raise ValueError("Country must contain exactly two characters.")

        return value

    @field_validator("starts_at", "ends_at")
    @classmethod
    def validate_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Event dates must include timezone information.")

        return value

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.starts_at >= self.ends_at:
            raise ValueError("Event end must be after event start.")

        return self


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: UUID | None = None
    name: str | None = Field(default=None, max_length=200)

    starts_at: datetime | None = None
    ends_at: datetime | None = None

    guest_count: int | None = Field(default=None, gt=0)

    status: EventStatus | None = None

    address_line: str | None = Field(default=None, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    postal_code: str | None = Field(default=None, max_length=20)
    city: str | None = Field(default=None, max_length=120)
    province: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, min_length=2, max_length=2)

    notes: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = " ".join(value.split())

        if not value:
            raise ValueError("Event name cannot be empty.")

        return value

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip().upper()

        if len(value) != 2:
            raise ValueError("Country must contain exactly two characters.")

        return value

    @field_validator("starts_at", "ends_at")
    @classmethod
    def validate_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Event dates must include timezone information.")

        return value

    @model_validator(mode="after")
    def validate_update(self):
        required_fields = {
            "client_id",
            "name",
            "starts_at",
            "ends_at",
            "guest_count",
            "status",
            "country",
        }

        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        for field in required_fields.intersection(self.model_fields_set):
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null.")

        if self.starts_at is not None and self.ends_at is not None:
            if self.starts_at >= self.ends_at:
                raise ValueError("Event end must be after event start.")

        return self


class EventResponse(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int
    offset: int
    limit: int
