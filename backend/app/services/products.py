from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product, ProductType
from app.repositories import products as product_repository
from app.services.product_categories import (
    ProductCategoryNotFoundError,
    get_category,
)


class ProductNotFoundError(Exception):
    pass


class ProductSKUAlreadyExistsError(Exception):
    pass


class InvalidProductDataError(Exception):
    pass


class ProductArchivedError(InvalidProductDataError):
    pass


def _validate_category(db: Session, *, category_id: UUID | None) -> None:
    if category_id is None:
        return

    try:
        category = get_category(db, category_id=category_id)
    except ProductCategoryNotFoundError as exc:
        raise InvalidProductDataError(
            "The selected category does not exist."
        ) from exc

    if not category.is_active:
        raise InvalidProductDataError(
            "The selected category is inactive."
        )


def _validate_sku(
    db: Session,
    *,
    sku: str | None,
    exclude_id: UUID | None = None,
) -> None:
    if sku is None:
        return

    query = select(Product.id).where(Product.sku == sku)

    if exclude_id is not None:
        query = query.where(Product.id != exclude_id)

    if db.scalar(query.limit(1)) is not None:
        raise ProductSKUAlreadyExistsError(
            "A product with this SKU already exists."
        )


def list_products(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
    category_id: UUID | None = None,
    product_type: ProductType | None =None,
    is_active: bool | None = True,
):
    return product_repository.list_products(
        db,
        offset=offset,
        limit=limit,
        search=search,
        category_id=category_id,
        product_type=product_type,
        is_active=is_active,
    )


def get_product(db: Session, *, product_id: UUID) -> Product:
    product = product_repository.get_product_by_id(
        db,
        product_id=product_id,
    )

    if product is None:
        raise ProductNotFoundError("Product not found.")

    return product


def create_product(
    db: Session,
    *,
    data: dict,
) -> Product:
    data = data.copy()

    try:
        _validate_category(db, category_id=data.get("category_id"))
        _validate_sku(db, sku=data.get("sku"))

        product = product_repository.create_product(db, data=data)
        db.commit()
        db.refresh(product)
        return product
    except Exception:
        db.rollback()
        raise


def update_product(
    db: Session,
    *,
    product_id: UUID,
    data: dict,
) -> Product:
    data = data.copy()

    try:
        product = get_product(db, product_id=product_id)

        if not product.is_active:
            raise ProductArchivedError("Product not found.")

        for field in (
            "name",
            "type",
            "unit",
            "sale_price",
            "cost_price",
        ):
            if field in data and data[field] is None:
                raise InvalidProductDataError(
                    f"Product field '{field}' cannot be null."
                )

        if "category_id" in data:
            _validate_category(db, category_id=data["category_id"])

        if "sku" in data:
            _validate_sku(
                db,
                sku=data["sku"],
                exclude_id=product.id,
            )

        product = product_repository.update_product(
            db,
            product=product,
            data=data,
        )

        db.commit()
        db.refresh(product)
        return product
    except Exception:
        db.rollback()
        raise


def archive_product(
    db: Session,
    *,
    product_id: UUID,
) -> Product:
    try:
        product = get_product(db, product_id=product_id)

        if not product.is_active:
            raise InvalidProductDataError(
                "Product is already archived."
            )

        product.is_active = False
        db.flush()
        db.commit()
        db.refresh(product)
        return product
    except Exception:
        db.rollback()
        raise