from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.product_category import ProductCategory


def get_category_by_id(
    db: Session,
    *,
    category_id: UUID,
) -> ProductCategory | None:
    return db.scalar(
        select(ProductCategory).where(ProductCategory.id == category_id)
    )


def list_categories(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
    parent_id: UUID | None = None,
    is_active: bool | None = True,
) -> tuple[list[ProductCategory], int]:
    query = select(ProductCategory)

    if search:
        query = query.where(
            ProductCategory.name.ilike(f"%{search.strip()}%")
        )

    if parent_id is not None:
        query = query.where(ProductCategory.parent_id == parent_id)

    if is_active is not None:
        query = query.where(ProductCategory.is_active.is_(is_active))

    total = db.scalar(
        select(func.count()).select_from(query.order_by(None).subquery())
    ) or 0

    categories = db.scalars(
        query.order_by(ProductCategory.name.asc(), ProductCategory.id.asc())
        .offset(offset)
        .limit(limit)
    ).all()

    return list(categories), total


def create_category(
    db: Session,
    *,
    data: dict,
) -> ProductCategory:
    category = ProductCategory(**data)
    db.add(category)
    db.flush()
    db.refresh(category)
    return category


def update_category(
    db: Session,
    *,
    category: ProductCategory,
    data: dict,
) -> ProductCategory:
    for field, value in data.items():
        setattr(category, field, value)

    db.flush()
    db.refresh(category)
    return category