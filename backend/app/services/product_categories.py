from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_category import ProductCategory
from app.repositories import product_categories as category_repository


class ProductCategoryNotFoundError(Exception):
    pass


class ProductCategoryAlreadyExistsError(Exception):
    pass


class InvalidProductCategoryDataError(Exception):
    pass


class ProductCategoryInUseError(Exception):
    pass


def _validate_category_name(
    db: Session,
    *,
    name: str,
    exclude_id: UUID | None = None,
) -> None:
    query = select(ProductCategory.id).where(ProductCategory.name == name)

    if exclude_id is not None:
        query = query.where(ProductCategory.id != exclude_id)

    if db.scalar(query.limit(1)) is not None:
        raise ProductCategoryAlreadyExistsError(
            "A category with this name already exists."
        )


def _validate_parent(
    db: Session,
    *,
    parent_id: UUID | None,
    category_id: UUID | None = None,
) -> None:
    if parent_id is None:
        return

    if category_id == parent_id:
        raise InvalidProductCategoryDataError(
            "A category cannot be its own parent."
        )

    parent = category_repository.get_category_by_id(
        db,
        category_id=parent_id,
    )

    if parent is None:
        raise ProductCategoryNotFoundError("Parent category not found.")

    if not parent.is_active:
        raise InvalidProductCategoryDataError(
            "Cannot use an archived category as parent."
        )

    visited: set[UUID] = set()
    current = parent

    while current is not None:
        if current.id == category_id:
            raise InvalidProductCategoryDataError(
                "Category hierarchy cannot contain cycles."
            )

        if current.id in visited:
            raise InvalidProductCategoryDataError(
                "Existing category hierarchy contains a cycle."
            )

        visited.add(current.id)

        if current.parent_id is None:
            break

        current = category_repository.get_category_by_id(
            db,
            category_id=current.parent_id,
        )


def list_categories(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
    parent_id: UUID | None = None,
    is_active: bool | None = True,
):
    return category_repository.list_categories(
        db,
        offset=offset,
        limit=limit,
        search=search,
        parent_id=parent_id,
        is_active=is_active,
    )


def get_category(db: Session, *, category_id: UUID) -> ProductCategory:
    category = category_repository.get_category_by_id(
        db,
        category_id=category_id,
    )

    if category is None:
        raise ProductCategoryNotFoundError("Category not found.")

    return category


def create_category(
    db: Session,
    *,
    data: dict,
) -> ProductCategory:
    data = data.copy()

    try:
        _validate_category_name(db, name=data["name"])
        _validate_parent(db, parent_id=data.get("parent_id"))

        category = category_repository.create_category(db, data=data)
        db.commit()
        db.refresh(category)
        return category
    except Exception:
        db.rollback()
        raise


def update_category(
    db: Session,
    *,
    category_id: UUID,
    data: dict,
) -> ProductCategory:
    data = data.copy()

    try:
        category = get_category(db, category_id=category_id)

        if not category.is_active:
            raise InvalidProductCategoryDataError(
                "Archived categories cannot be updated."
            )

        if "name" in data:
            if data["name"] is None:
                raise InvalidProductCategoryDataError(
                    "Category name cannot be null."
                )

            _validate_category_name(
                db,
                name=data["name"],
                exclude_id=category.id,
            )

        if "parent_id" in data:
            _validate_parent(
                db,
                parent_id=data["parent_id"],
                category_id=category.id,
            )

        category = category_repository.update_category(
            db,
            category=category,
            data=data,
        )

        db.commit()
        db.refresh(category)
        return category
    except Exception:
        db.rollback()
        raise


def archive_category(
    db: Session,
    *,
    category_id: UUID,
) -> ProductCategory:
    try:
        category = get_category(db, category_id=category_id)

        if not category.is_active:
            raise InvalidProductCategoryDataError(
                "Category is already archived."
            )

        product_count = db.scalar(
            select(func.count())
            .select_from(Product)
            .where(Product.category_id == category.id)
        ) or 0

        child_count = db.scalar(
            select(func.count())
            .select_from(ProductCategory)
            .where(ProductCategory.parent_id == category.id)
        ) or 0

        if product_count or child_count:
            raise ProductCategoryInUseError(
                "Cannot archive a category that has products or subcategories."
            )

        category.is_active = False
        db.flush()
        db.commit()
        db.refresh(category)
        return category
    except Exception:
        db.rollback()
        raise