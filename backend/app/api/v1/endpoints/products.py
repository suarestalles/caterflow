
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import get_current_tenant_db, require_permission
from app.core.permissions import PermissionCode
from app.db.tenant_session import TenantSession
from app.models.product import ProductType
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services.products import (
    InvalidProductDataError,
    ProductArchivedError,
    ProductNotFoundError,
    ProductSKUAlreadyExistsError,
    archive_product,
    create_product,
    get_product,
    list_products,
    update_product,
)

router = APIRouter(tags=["Products"])


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PermissionCode.PRODUCTS_CREATE))],
)
def create_new_product(
    data: ProductCreate,
    db: TenantSession = Depends(get_current_tenant_db),
):
    try:
        return create_product(
            db,
            data=data.model_dump(),
        )
    except ProductSKUAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except InvalidProductDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get(
    "/",
    response_model=ProductListResponse,
    dependencies=[Depends(require_permission(PermissionCode.PRODUCTS_READ))],
)
def get_products(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    category_id: UUID | None = Query(default=None),
    product_type: ProductType | None = Query(default=None, alias="type"),
    db: TenantSession = Depends(get_current_tenant_db),
):
    items, total = list_products(
        db,
        offset=offset,
        limit=limit,
        search=search,
        category_id=category_id,
        product_type=product_type,
    )

    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_permission(PermissionCode.PRODUCTS_READ))],
)
def get_product_by_id(
    product_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    try:
        return get_product(db, product_id=product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_permission(PermissionCode.PRODUCTS_UPDATE))],
)
def update_existing_product(
    product_id: UUID,
    data: ProductUpdate,
    db: TenantSession = Depends(get_current_tenant_db),
):
    try:
        return update_product(
            db,
            product_id=product_id,
            data=data.model_dump(exclude_unset=True),
        )
    except ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ProductSKUAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ProductArchivedError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidProductDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{product_id}/archive",
    response_model=ProductResponse,
    dependencies=[Depends(require_permission(PermissionCode.PRODUCTS_DELETE))],
)
def archive_existing_product(
    product_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
):
    try:
        return archive_product(db, product_id=product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
