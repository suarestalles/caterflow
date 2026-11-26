
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_platform_admin
from app.db.session import get_db
from app.schemas.platform_tenant import (
    PlatformTenantCreate,
    PlatformTenantListResponse,
    PlatformTenantResponse,
    PlatformTenantUpdate,
)
from app.services.platform_tenants import (
    PlatformTenantNotFoundError,
    create_tenant,
    get_tenant,
    list_tenants,
    set_tenant_active,
    update_tenant,
)

router = APIRouter(
    tags=["Platform - Tenants"],
    dependencies=[Depends(get_current_platform_admin)],
)


@router.post(
    "/",
    response_model=PlatformTenantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_endpoint(
    payload: PlatformTenantCreate,
    db: Session = Depends(get_db),
) -> PlatformTenantResponse:
    return create_tenant(db, name=payload.name)


@router.get(
    "/",
    response_model=PlatformTenantListResponse,
)
def list_tenants_endpoint(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=150),
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> PlatformTenantListResponse:
    tenants, total = list_tenants(
        db,
        offset=offset,
        limit=limit,
        search=search,
        is_active=is_active,
    )

    return PlatformTenantListResponse(
        items=tenants,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{tenant_id}",
    response_model=PlatformTenantResponse,
)
def get_tenant_endpoint(
    tenant_id: UUID,
    db: Session = Depends(get_db),
) -> PlatformTenantResponse:
    try:
        return get_tenant(db, tenant_id)
    except PlatformTenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        ) from None


@router.patch(
    "/{tenant_id}",
    response_model=PlatformTenantResponse,
)
def update_tenant_endpoint(
    tenant_id: UUID,
    payload: PlatformTenantUpdate,
    db: Session = Depends(get_db),
) -> PlatformTenantResponse:
    try:
        return update_tenant(
            db,
            tenant_id=tenant_id,
            data=payload.model_dump(exclude_unset=True),
        )
    except PlatformTenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        ) from None


@router.post(
    "/{tenant_id}/suspend",
    response_model=PlatformTenantResponse,
)
def suspend_tenant_endpoint(
    tenant_id: UUID,
    db: Session = Depends(get_db),
) -> PlatformTenantResponse:
    try:
        return set_tenant_active(
            db,
            tenant_id=tenant_id,
            is_active=False,
        )
    except PlatformTenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        ) from None


@router.post(
    "/{tenant_id}/activate",
    response_model=PlatformTenantResponse,
)
def activate_tenant_endpoint(
    tenant_id: UUID,
    db: Session = Depends(get_db),
) -> PlatformTenantResponse:
    try:
        return set_tenant_active(
            db,
            tenant_id=tenant_id,
            is_active=True,
        )
    except PlatformTenantNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        ) from None
