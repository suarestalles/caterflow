
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_tenant_db, require_permission
from app.core.permissions import PermissionCode
from app.models.event import EventStatus
from app.schemas.event import (
    EventCreate,
    EventListResponse,
    EventResponse,
    EventUpdate,
)
from app.services.events import (
    EventClientNotFoundError,
    EventNotFoundError,
    InvalidEventDataError,
    cancel_event,
    create_event,
    get_event,
    list_events,
    update_event,
)

router = APIRouter(tags=["Events"])


def _handle_event_error(error: Exception) -> None:
    if isinstance(error, EventNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    if isinstance(error, EventClientNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    if isinstance(error, InvalidEventDataError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    raise error


@router.post(
    "/",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PermissionCode.EVENTS_CREATE))],
)
def create_event_endpoint(
    payload: EventCreate,
    db: Session = Depends(get_current_tenant_db),
):
    try:
        return create_event(db, data=payload.model_dump())
    except (EventClientNotFoundError, InvalidEventDataError) as error:
        _handle_event_error(error)


@router.get(
    "/",
    response_model=EventListResponse,
    dependencies=[Depends(require_permission(PermissionCode.EVENTS_READ))],
)
def list_events_endpoint(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    client_id: UUID | None = None,
    event_status: EventStatus | None = Query(default=None, alias="status"),
    starts_at_from: datetime | None = None,
    starts_at_to: datetime | None = None,
    db: Session = Depends(get_current_tenant_db),
):
    try:
        items, total = list_events(
            db,
            offset=offset,
            limit=limit,
            search=search,
            client_id=client_id,
            status=event_status,
            starts_at_from=starts_at_from,
            starts_at_to=starts_at_to,
        )

        return EventListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )
    except InvalidEventDataError as error:
        _handle_event_error(error)


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    dependencies=[Depends(require_permission(PermissionCode.EVENTS_READ))],
)
def get_event_endpoint(
    event_id: UUID,
    db: Session = Depends(get_current_tenant_db),
):
    try:
        return get_event(db, event_id=event_id)
    except EventNotFoundError as error:
        _handle_event_error(error)


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
    dependencies=[Depends(require_permission(PermissionCode.EVENTS_UPDATE))],
)
def update_event_endpoint(
    event_id: UUID,
    payload: EventUpdate,
    db: Session = Depends(get_current_tenant_db),
):
    try:
        return update_event(
            db,
            event_id=event_id,
            data=payload.model_dump(exclude_unset=True),
        )
    except (
        EventNotFoundError,
        EventClientNotFoundError,
        InvalidEventDataError,
    ) as error:
        _handle_event_error(error)


@router.post(
    "/{event_id}/cancel",
    response_model=EventResponse,
    dependencies=[Depends(require_permission(PermissionCode.EVENTS_CANCEL))],
)
def cancel_event_endpoint(
    event_id: UUID,
    db: Session = Depends(get_current_tenant_db),
):
    try:
        return cancel_event(db, event_id=event_id)
    except (EventNotFoundError, InvalidEventDataError) as error:
        _handle_event_error(error)
