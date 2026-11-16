
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.v1.deps import get_current_tenant_db, require_permission
from app.core.permissions import PermissionCode
from app.db.tenant_session import TenantSession
from app.schemas.client import (
    ClientCreate,
    ClientListResponse,
    ClientResponse,
    ClientUpdate,
)
from app.services.clients import (
    ClientNotFoundError,
    InvalidClientDataError,
    archive_client,
    create_client,
    get_client,
    list_clients,
    update_client,
)

router = APIRouter(tags=["Clients"])


@router.post(
    "/",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission(PermissionCode.CLIENTS_CREATE))
    ],
)
def create_client_endpoint(
    payload: ClientCreate,
    db: TenantSession = Depends(get_current_tenant_db),
) -> ClientResponse:
    try:
        return create_client(
            db,
            data=payload.model_dump(),
        )
    except InvalidClientDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get(
    "/",
    response_model=ClientListResponse,
    dependencies=[
        Depends(require_permission(PermissionCode.CLIENTS_READ))
    ],
)
def list_clients_endpoint(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    db: TenantSession = Depends(get_current_tenant_db),
) -> ClientListResponse:
    clients, total = list_clients(
        db,
        offset=offset,
        limit=limit,
        search=search,
    )

    return ClientListResponse(
        items=clients,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    dependencies=[
        Depends(require_permission(PermissionCode.CLIENTS_READ))
    ],
)
def get_client_endpoint(
    client_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
) -> ClientResponse:
    try:
        return get_client(
            db,
            client_id=client_id,
        )
    except ClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        ) from None


@router.patch(
    "/{client_id}",
    response_model=ClientResponse,
    dependencies=[
        Depends(require_permission(PermissionCode.CLIENTS_UPDATE))
    ],
)
def update_client_endpoint(
    client_id: UUID,
    payload: ClientUpdate,
    db: TenantSession = Depends(get_current_tenant_db),
) -> ClientResponse:
    try:
        return update_client(
            db,
            client_id=client_id,
            data=payload.model_dump(exclude_unset=True),
        )
    except ClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        ) from None
    except InvalidClientDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(require_permission(PermissionCode.CLIENTS_ARCHIVE))
    ],
)
def archive_client_endpoint(
    client_id: UUID,
    db: TenantSession = Depends(get_current_tenant_db),
) -> Response:
    try:
        archive_client(
            db,
            client_id=client_id,
        )
    except ClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        ) from None

    return Response(status_code=status.HTTP_204_NO_CONTENT)
