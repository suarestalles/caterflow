
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import get_current_tenant_db, require_permission
from app.core.permissions import PermissionCode
from app.db.tenant_session import TenantSession
from app.schemas.product_category import (
    ProductCategoryCreate,
    ProductCategoryListResponse,
    ProductCategoryResponse,
    ProductCategoryUpdate,
)
from app.services.product_categories import (
    InvalidProductCategoryDataError,
    ProductCategoryAlreadyExistsError,
    ProductCategoryInUseError,
    ProductCategoryNotFoundError,
    archive_category,
    create_category,
    get_category,
    list_categories,
    update_category,
)

router = APIRouter(tags=["Product Categories"])


@router.post(
    "/",
    response_model=ProductCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PermissionCode.PRODUCT_CATEGORIES_CREATE))],
)
def create_product_category(
    data: ProductCategoryCreate,
    db: TenantSession = Depends(get_current_tenant_db),
):
    try:
        return create_category(db, data=data.model_dump())
    except ProductCategoryAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except InvalidProductCategoryDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get(
    "/",
    response_model=ProductCategoryListResponse,
    dependencies=[Depends(require_permission(PermissionCode.PRODUCT_CATEGORIES_READ))],
)
def get_product_categories(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    db: TenantSession = Depends(get_current_tenant_db),
):
    items, total = list_categories(
        db,
        offset=offset,
        limit=limit,
        search=search,
    )

    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get(
    "/{category_id}",
    response_model=ProductCategoryResponse,
    dependencies=[Depends(require_permission(PermissionCode.PRODUCT_CATEGORIES_READ))],
)
def get_product_category(
    category_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    try:
        return get_category(db, category_id=category_id)
    except ProductCategoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{category_id}",
    response_model=ProductCategoryResponse,
    dependencies=[Depends(require_permission(PermissionCode.PRODUCT_CATEGORIES_UPDATE))],
)
def update_product_category(
    category_id: UUID,
    data: ProductCategoryUpdate,
    db: TenantSession = Depends(get_current_tenant_db),
):
    try:
        return update_category(
            db,
            category_id=category_id,
            data=data.model_dump(exclude_unset=True),
        )
    except ProductCategoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ProductCategoryAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except InvalidProductCategoryDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{category_id}/archive",
    response_model=ProductCategoryResponse,
    dependencies=[Depends(require_permission(PermissionCode.PRODUCT_CATEGORIES_DELETE))],
)
def archive_product_category(
    category_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    try:
        return archive_category(db, category_id=category_id)
    except ProductCategoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ProductCategoryInUseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
