from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Numeric

from app.models.abstract import Abstract
from app.models.tenant_scoped import TenantScoped

class ProductType(StrEnum):
    PRODUCT = "product"
    SERVICE = "service"


class ProductUnit(StrEnum):
    UNIT = "unit"
    KILOGRAM = "kg"
    GRAM = "g"
    LITER = "l"
    MILLILITER = "ml"
    PACKAGE = "package"
    PERSON = "person"
    HOUR = "hour"
    DAY = "day"
    SERVICE = "service"


class Product(Abstract, TenantScoped):
    __tablename__ = "products"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_products_tenant_id_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "category_id"],
            ["product_categories.tenant_id", "product_categories.id"],
            name="fk_products_tenant_category",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "type IN ('product', 'service')",
            name="ck_products_type",
        ),
        CheckConstraint(
            "unit IN ('unit', 'kg', 'g', 'l', 'ml', 'package', "
            "'person', 'hour', 'day', 'service')",
            name="ck_products_unit",
        ),
        CheckConstraint(
            "sale_price >= 0",
            name="ck_products_sale_price_nonnegative",
        ),
        CheckConstraint(
            "cost_price >= 0",
            name="ck_products_cost_price_nonnegative",
        ),
        Index(
            "uq_products_tenant_sku",
            "tenant_id",
            "sku",
            unique=True,
            postgresql_where=text("sku IS NOT NULL"),
        ),
    )

    category_id: Mapped[UUID | None] = mapped_column(nullable=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ProductType.PRODUCT.value,
        server_default=text("'product'"),
    )

    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ProductUnit.UNIT.value,
        server_default=text("'unit'"),
    )

    sku: Mapped[str | None] = mapped_column(String(50), nullable=True)

    sale_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0"),
    )

    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    category = relationship(
        "ProductCategory",
        back_populates="products",
        primaryjoin=(
            "and_("
            "foreign(Product.category_id) == ProductCategory.id, "
            "Product.tenant_id == ProductCategory.tenant_id"
            ")"
        ),
    )

    tenant = relationship("Tenant", back_populates="products")
