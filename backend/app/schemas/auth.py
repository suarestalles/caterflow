from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    tenant_id: UUID

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class PlatformLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserSessionResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr


class TenantSessionInfo(BaseModel):
    id: UUID
    name: str


class TenantSessionResponse(BaseModel):
    user: UserSessionResponse
    tenant: TenantSessionInfo


class PlatformSessionResponse(BaseModel):
    user: UserSessionResponse
    is_platform_admin: bool = True