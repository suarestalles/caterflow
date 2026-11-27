
from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class PlatformUserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    is_platform_admin: bool = False
    tenant_ids: list[UUID] = Field(default_factory=list)

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_name(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @model_validator(mode="after")
    def validate_access(self):
        if not self.is_platform_admin and not self.tenant_ids:
            raise ValueError(
                "A user must be a platform admin or belong to at least one tenant."
            )

        if len(self.tenant_ids) != len(set(self.tenant_ids)):
            raise ValueError("Duplicate tenant IDs are not allowed.")

        return self


class PlatformUserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    is_platform_admin: bool | None = None
    tenant_ids: list[UUID] | None = None

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_name(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        if self.tenant_ids is not None:
            if len(self.tenant_ids) != len(set(self.tenant_ids)):
                raise ValueError("Duplicate tenant IDs are not allowed.")

        return self


class PlatformUserTenantResponse(BaseModel):
    id: UUID
    name: str


class PlatformUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr
    is_active: bool
    is_platform_admin: bool
    tenants: list[PlatformUserTenantResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PlatformUserListResponse(BaseModel):
    items: list[PlatformUserResponse]
    total: int
    offset: int
    limit: int
