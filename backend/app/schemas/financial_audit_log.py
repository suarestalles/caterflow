
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FinancialAuditEntityType(StrEnum):
    EXPENSE = "expense"
    EVENT_STAFF_ASSIGNMENT = "event_staff_assignment"


class FinancialAuditLogCreate(BaseModel):
    event_id: UUID | None = None
    entity_type: FinancialAuditEntityType
    entity_id: UUID
    field_name: str = Field(max_length=100)
    old_value: str | None = None
    new_value: str | None = None
    reason: str


class FinancialAuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    event_id: UUID | None
    entity_type: FinancialAuditEntityType
    entity_id: UUID
    field_name: str
    old_value: str | None
    new_value: str | None
    reason: str
    recorded_by_user_id: UUID
    created_at: datetime
