from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, remote

from app.models.abstract import Abstract
from app.models.tenant_scoped import TenantScoped


class ProductCategory(Abstract, TenantScoped):
    __tablename__ = "product_categories"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_product_categories_tenant_id_id",
        ),
        UniqueConstraint(
            "tenant_id",
            "name",
            name="uq_product_categories_tenant_name",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "parent_id"],
            ["product_categories.tenant_id", "product_categories.id"],
            name="fk_product_categories_tenant_parent",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "parent_id IS NULL OR parent_id != id",
            name="ck_product_categories_not_own_parent",
        ),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    parent_id: Mapped[UUID | None] = mapped_column(nullable=True)

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    parent = relationship(
        "ProductCategory",
        back_populates="children",
        primaryjoin=(
            "and_("
            "foreign(ProductCategory.parent_id) == remote(ProductCategory.id), "
            "ProductCategory.tenant_id == remote(ProductCategory.tenant_id)"
            ")"
        ),
        remote_side="(ProductCategory.tenant_id, ProductCategory.id)",
        foreign_keys="ProductCategory.parent_id",
    )

    children = relationship(
        "ProductCategory",
        back_populates="parent",
        foreign_keys="ProductCategory.parent_id",
    )

    products = relationship(
        "Product",
        back_populates="category",
        primaryjoin=(
            "and_("
            "ProductCategory.id == foreign(Product.category_id), "
            "ProductCategory.tenant_id == Product.tenant_id"
            ")"
        ),
    )

    tenant = relationship("Tenant", back_populates="product_categories")