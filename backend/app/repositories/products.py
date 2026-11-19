from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.product import Product, ProductType


def get_product_by_id(db: Session, *, product_id: UUID) -> Product | None:
    return db.scalar(select(Product).where(Product.id == product_id))


def list_products(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
    category_id: UUID | None = None,
    product_type: ProductType | None = None,
    is_active: bool | None = True,
) -> tuple[list[Product], int]:
    query = select(Product)

    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Product.name.ilike(term),
                Product.sku.ilike(term),
            )
        )

    if category_id is not None:
        query = query.where(Product.category_id == category_id)

    if product_type is not None:
        query = query.where(Product.type == product_type.value)

    if is_active is not None:
        query = query.where(Product.is_active.is_(is_active))

    total = db.scalar(
        select(func.count()).select_from(query.order_by(None).subquery())
    ) or 0

    products = db.scalars(
        query.order_by(Product.name.asc(), Product.id.asc())
        .offset(offset)
        .limit(limit)
    ).all()

    return list(products), total


def create_product(db: Session, *, data: dict) -> Product:
    product = Product(**data)
    db.add(product)
    db.flush()
    db.refresh(product)
    return product


def update_product(
    db: Session,
    *,
    product: Product,
    data: dict,
) -> Product:
    for field, value in data.items():
        setattr(product, field, value)

    db.flush()
    db.refresh(product)
    return product