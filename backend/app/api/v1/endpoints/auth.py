from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    PlatformLoginRequest,
    TokenResponse,
)
from app.services.auth import (
    InvalidCredentialsError,
    PlatformAccessDeniedError,
    TenantAccessDeniedError,
    login_platform,
    login_tenant,
)

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    try:
        token = login_tenant(
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

    return TokenResponse(access_token=token)


@router.post("/platform/login", response_model=TokenResponse)
def platform_login_endpoint(
    payload: PlatformLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    try:
        token = login_platform(
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

    return TokenResponse(access_token=token)
