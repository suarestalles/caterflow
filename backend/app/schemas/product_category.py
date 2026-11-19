from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductCategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    parent_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Category name cannot be empty.")
        return value


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    parent_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Category name cannot be empty.")
        return value


class ProductCategoryResponse(ProductCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    is_active: bool


class ProductCategoryListResponse(BaseModel):
    items: list[ProductCategoryResponse]
    total: int
    offset: int
    limit: int