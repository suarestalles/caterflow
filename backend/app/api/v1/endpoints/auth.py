from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import (
    AuthContext,
    PlatformAdminContext,
    get_auth_context,
    get_current_platform_admin,
)
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.tenant import Tenant
from app.schemas.auth import (
    LoginRequest,
    PlatformLoginRequest,
    PlatformSessionResponse,
    RefreshTokenRequest,
    TenantSessionInfo,
    TenantSessionResponse,
    TokenResponse,
    UserSessionResponse,
)
from app.services.auth import (
    InvalidCredentialsError,
    PlatformAccessDeniedError,
    TenantAccessDeniedError,
    login_platform,
    login_tenant,
)
from app.services.refresh_tokens import (
    InvalidRefreshTokenError,
    RefreshTokenReuseError,
    create_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    try:
        access_token = login_tenant(
            db=db,
            email=str(payload.email),
            password=payload.password,
            tenant_id=payload.tenant_id,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except TenantAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this tenant.",
        ) from None

    user_id = UUID(decode_access_token(access_token)["sub"])

    refresh_token = create_refresh_token(
        db=db,
        user_id=user_id,
        tenant_id=payload.tenant_id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/platform/login", response_model=TokenResponse)
def platform_login_endpoint(
    payload: PlatformLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    try:
        access_token = login_platform(
            db=db,
            email=str(payload.email),
            password=payload.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except PlatformAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have platform administrator access.",
        ) from None

    user_id = UUID(decode_access_token(access_token)["sub"])

    refresh_token = create_refresh_token(
        db=db,
        user_id=user_id,
        tenant_id=None,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    try:
        access_token, refresh_token = rotate_refresh_token(
            db=db,
            raw_token=payload.refresh_token,
        )
    except RefreshTokenReuseError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected. Please sign in again.",
        ) from None
    except InvalidRefreshTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        ) from None

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> Response:
    revoke_refresh_token(
        db=db,
        raw_token=payload.refresh_token,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=TenantSessionResponse)
def get_tenant_session(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> TenantSessionResponse:
    tenant = db.scalar(
        select(Tenant).where(Tenant.id == auth.tenant_id)
    )

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant session is no longer valid.",
        )

    return TenantSessionResponse(
        user=UserSessionResponse(
            id=auth.user.id,
            full_name=auth.user.full_name,
            email=auth.user.email,
        ),
        tenant=TenantSessionInfo(
            id=tenant.id,
            name=tenant.name,
        ),
    )


@router.get("/platform/me", response_model=PlatformSessionResponse)
def get_platform_session(
    auth: PlatformAdminContext = Depends(get_current_platform_admin),
) -> PlatformSessionResponse:
    return PlatformSessionResponse(
        user=UserSessionResponse(
            id=auth.user.id,
            full_name=auth.user.full_name,
            email=auth.user.email,
        ),
    )