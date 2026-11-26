
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlatformMembershipCreate(BaseModel):
    user_id: UUID
    role_id: UUID


class PlatformMembershipUpdate(BaseModel):
    role_id: UUID


class PlatformMembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    user_full_name: str
    user_email: str
    role_id: UUID
    role_name: str
    created_at: datetime
    updated_at: datetime


class PlatformMembershipListResponse(BaseModel):
    items: list[PlatformMembershipResponse]
    total: int
    offset: int
    limit: int
