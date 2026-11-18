
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_tenant_db, require_permission
from app.models.quote import QuoteStatus
from app.schemas.quote import (
    QuoteCreate,
    QuoteListResponse,
    QuoteResponse,
    QuoteUpdate,
)
from app.services import quotes as quote_service
from app.services.quotes import (
    InvalidQuoteDataError,
    QuoteClientNotFoundError,
    QuoteEventNotFoundError,
    QuoteNotFoundError,
)

router = APIRouter(tags=["Quotes"])


@router.get(
    "/",
    response_model=QuoteListResponse,
    dependencies=[Depends(require_permission("quotes.read"))],
)
def list_quotes(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
    client_id: UUID | None = None,
    event_id: UUID | None = None,
    quote_status: QuoteStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_current_tenant_db),
):
    quotes, total = quote_service.list_quotes(
        db,
        offset=offset,
        limit=limit,
        search=search,
        client_id=client_id,
        event_id=event_id,
        status=quote_status.value if quote_status else None,
    )

    return QuoteListResponse(
        items=quotes,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/",
    response_model=QuoteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("quotes.create"))],
)
def create_quote(
    data: QuoteCreate,
    db: Session = Depends(get_current_tenant_db),
):
    try:
        return quote_service.create_quote(
            db,
            data=data.model_dump(),
        )
    except QuoteClientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except QuoteEventNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidQuoteDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get(
    "/{quote_id}",
    response_model=QuoteResponse,
    dependencies=[Depends(require_permission("quotes.read"))],
)
def get_quote(
    quote_id: UUID,
    db: Session = Depends(get_current_tenant_db),
):
    try:
        return quote_service.get_quote(db, quote_id=quote_id)
    except QuoteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{quote_id}",
    response_model=QuoteResponse,
    dependencies=[Depends(require_permission("quotes.update"))],
)
def update_quote(
    quote_id: UUID,
    data: QuoteUpdate,
    db: Session = Depends(get_current_tenant_db),
):
    try:
        return quote_service.update_quote(
            db,
            quote_id=quote_id,
            data=data.model_dump(exclude_unset=True),
        )
    except QuoteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except QuoteClientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except QuoteEventNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidQuoteDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{quote_id}/send",
    response_model=QuoteResponse,
    dependencies=[Depends(require_permission("quotes.send"))],
)
def send_quote(
    quote_id: UUID,
    db: Session = Depends(get_current_tenant_db),
):
    try:
        return quote_service.send_quote(db, quote_id=quote_id)
    except QuoteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidQuoteDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{quote_id}/duplicate",
    response_model=QuoteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("quotes.create"))],
)
def duplicate_quote(
    quote_id: UUID,
    db: Session = Depends(get_current_tenant_db),
):
    try:
        return quote_service.duplicate_quote(
            db,
            quote_id=quote_id,
        )
    except QuoteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
