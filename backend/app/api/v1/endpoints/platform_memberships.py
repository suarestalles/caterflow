
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import get_current_platform_admin
from app.db.tenant_session import TenantSession, get_platform_db
from app.schemas.platform_membership import (
    PlatformMembershipCreate,
    PlatformMembershipListResponse,
    PlatformMembershipResponse,
    PlatformMembershipUpdate,
)
from app.services.platform_memberships import (
    LastOwnerError,
    PlatformMembershipConflictError,
    PlatformMembershipNotFoundError,
    PlatformMembershipValidationError,
    create_membership,
    delete_membership,
    list_memberships,
    update_membership_role,
    list_tenant_roles,
)

router = APIRouter(
    tags=["Platform - Memberships"],
    dependencies=[Depends(get_current_platform_admin)],
)


@router.get(
    "/tenants/{tenant_id}/memberships",
    response_model=PlatformMembershipListResponse,
)
def list_tenant_memberships(
    tenant_id: UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: TenantSession = Depends(get_platform_db),
):
    try:
        items, total = list_memberships(
            db,
            tenant_id,
            offset=offset,
            limit=limit,
        )
    except PlatformMembershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
    except PlatformMembershipValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from None

    return PlatformMembershipListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/tenants/{tenant_id}/memberships",
    response_model=PlatformMembershipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_membership(
    tenant_id: UUID,
    payload: PlatformMembershipCreate,
    db: TenantSession = Depends(get_platform_db),
):
    try:
        return create_membership(
            db,
            tenant_id=tenant_id,
            user_id=payload.user_id,
            role_id=payload.role_id,
        )
    except PlatformMembershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
    except PlatformMembershipConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None
    except PlatformMembershipValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from None


@router.patch(
    "/tenants/{tenant_id}/memberships/{membership_id}",
    response_model=PlatformMembershipResponse,
)
def update_tenant_membership(
    tenant_id: UUID,
    membership_id: UUID,
    payload: PlatformMembershipUpdate,
    db: TenantSession = Depends(get_platform_db),
):
    try:
        return update_membership_role(
            db,
            tenant_id=tenant_id,
            membership_id=membership_id,
            role_id=payload.role_id,
        )
    except PlatformMembershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
    except PlatformMembershipValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from None
    except LastOwnerError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None


@router.delete(
    "/tenants/{tenant_id}/memberships/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tenant_membership(
    tenant_id: UUID,
    membership_id: UUID,
    db: TenantSession = Depends(get_platform_db),
):
    try:
        delete_membership(
            db,
            tenant_id=tenant_id,
            membership_id=membership_id,
        )
    except PlatformMembershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
    except LastOwnerError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None

@router.get("/tenants/{tenant_id}/roles")
def list_tenant_roles(
    tenant_id: UUID,
    db: TenantSession = Depends(get_platform_db),
):
    try:
        return list_tenant_roles(db, tenant_id)
    except PlatformMembershipNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except PlatformMembershipValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc