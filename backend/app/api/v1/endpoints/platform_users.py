
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps import PlatformAdminContext, get_current_platform_admin
from app.db.session import get_db
from app.schemas.platform_user import (
    PlatformUserCreate,
    PlatformUserListResponse,
    PlatformUserResponse,
)
from app.services.platform_users import (
    PlatformUserAlreadyExistsError,
    PlatformUserNotFoundError,
    PlatformUserValidationError,
    create_user,
    get_user,
    list_users,
    deactivate_user,
    activate_user,
)

router = APIRouter(
    tags=["Platform - Users"],
    dependencies=[Depends(get_current_platform_admin)],
)


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
        return create_user(
            db,
            full_name=payload.full_name,
            email=str(payload.email),
            password=payload.password,
        )
    except PlatformUserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        ) from None


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
    users, total = list_users(
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
        return get_user(db, user_id)
    except PlatformUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        ) from None

@router.post("/{user_id}/activate", response_model=PlatformUserResponse)
def activate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return activate_user(db, user_id)
    except PlatformUserNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        ) from None


@router.post("/{user_id}/deactivate", response_model=PlatformUserResponse)
def deactivate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_admin: PlatformAdminContext = Depends(
        get_current_platform_admin
    ),
):
    try:
        return deactivate_user(
            db,
            user_id,
            current_admin.user.id,
        )
    except PlatformUserNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        ) from None
    except PlatformUserValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc