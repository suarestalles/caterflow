
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps import (
    PlatformAdminContext,
    get_current_platform_admin,
)
from app.db.session import get_db
from app.schemas.platform_user import (
    PlatformUserCreate,
    PlatformUserListResponse,
    PlatformUserResponse,
    PlatformUserUpdate,
)
from app.services.platform_users import (
    PlatformUserAlreadyExistsError,
    PlatformUserNotFoundError,
    PlatformUserValidationError,
    activate_user as activate_user_service,
    create_user as create_user_service,
    deactivate_user as deactivate_user_service,
    get_user as get_user_service,
    list_users as list_users_service,
    update_user as update_user_service,
)

router = APIRouter(
    tags=["Platform - Users"],
    dependencies=[Depends(get_current_platform_admin)],
)


def _handle_service_error(exc: Exception) -> None:
    if isinstance(exc, PlatformUserNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        ) from exc

    if isinstance(exc, PlatformUserAlreadyExistsError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        ) from exc

    if isinstance(exc, PlatformUserValidationError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    raise exc


@router.post(
    "/",
    response_model=PlatformUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_endpoint(
    payload: PlatformUserCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_user_service(
            db,
            full_name=payload.full_name,
            email=str(payload.email),
            password=payload.password,
            is_platform_admin=payload.is_platform_admin,
            tenant_ids=payload.tenant_ids,
        )
    except (
        PlatformUserAlreadyExistsError,
        PlatformUserValidationError,
    ) as exc:
        _handle_service_error(exc)


@router.get(
    "/",
    response_model=PlatformUserListResponse,
)
def list_users_endpoint(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    is_active: bool | None = None,
    db: Session = Depends(get_db),
):
    users, total = list_users_service(
        db,
        offset=offset,
        limit=limit,
        search=search,
        is_active=is_active,
    )

    return PlatformUserListResponse(
        items=users,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{user_id}",
    response_model=PlatformUserResponse,
)
def get_user_endpoint(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return get_user_service(db, user_id)
    except PlatformUserNotFoundError as exc:
        _handle_service_error(exc)


@router.patch(
    "/{user_id}",
    response_model=PlatformUserResponse,
)
def update_user_endpoint(
    user_id: UUID,
    payload: PlatformUserUpdate,
    db: Session = Depends(get_db),
    current_admin: PlatformAdminContext = Depends(
        get_current_platform_admin
    ),
):
    try:
        return update_user_service(
            db,
            user_id=user_id,
            current_admin_id=current_admin.user.id,
            full_name=payload.full_name,
            email=str(payload.email) if payload.email is not None else None,
            is_platform_admin=payload.is_platform_admin,
            tenant_ids=payload.tenant_ids,
        )
    except (
        PlatformUserNotFoundError,
        PlatformUserAlreadyExistsError,
        PlatformUserValidationError,
    ) as exc:
        _handle_service_error(exc)


@router.post(
    "/{user_id}/activate",
    response_model=PlatformUserResponse,
)
def activate_user_endpoint(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return activate_user_service(db, user_id)
    except PlatformUserNotFoundError as exc:
        _handle_service_error(exc)


@router.post(
    "/{user_id}/deactivate",
    response_model=PlatformUserResponse,
)
def deactivate_user_endpoint(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_admin: PlatformAdminContext = Depends(
        get_current_platform_admin
    ),
):
    try:
        return deactivate_user_service(
            db,
            user_id,
            current_admin.user.id,
        )
    except (
        PlatformUserNotFoundError,
        PlatformUserValidationError,
    ) as exc:
        _handle_service_error(exc)
