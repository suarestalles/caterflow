
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.event import Event, EventStatus
from app.repositories import clients as client_repository
from app.repositories import events as event_repository


class EventNotFoundError(Exception):
    pass


class EventClientNotFoundError(Exception):
    pass


class InvalidEventDataError(Exception):
    pass


ALLOWED_STATUS_TRANSITIONS = {
    EventStatus.DRAFT.value: {
        EventStatus.CONFIRMED.value,
    },
    EventStatus.CONFIRMED.value: {
        EventStatus.IN_PROGRESS.value,
    },
    EventStatus.IN_PROGRESS.value: {
        EventStatus.COMPLETED.value,
    },
}


def list_events(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
    client_id: UUID | None = None,
    status: str | None = None,
    starts_at_from: datetime | None = None,
    starts_at_to: datetime | None = None,
) -> tuple[list[Event], int]:
    if (
        starts_at_from is not None
        and starts_at_to is not None
        and starts_at_from > starts_at_to
    ):
        raise InvalidEventDataError(
            "The start date filter cannot be after the end date filter."
        )

    return event_repository.list_events(
        db,
        offset=offset,
        limit=limit,
        search=search,
        client_id=client_id,
        status=status,
        starts_at_from=starts_at_from,
        starts_at_to=starts_at_to,
    )


def get_event(
    db: Session,
    *,
    event_id: UUID,
) -> Event:
    event = event_repository.get_event_by_id(
        db,
        event_id=event_id,
    )

    if event is None:
        raise EventNotFoundError("Event not found.")

    return event


def create_event(
    db: Session,
    *,
    data: dict,
) -> Event:
    _validate_client(db, client_id=data["client_id"])

    event_data = data.copy()

    status = event_data.get("status", EventStatus.DRAFT)
    event_data["status"] = _normalize_status(status)

    _validate_date_range(
        starts_at=event_data["starts_at"],
        ends_at=event_data["ends_at"],
    )

    try:
        event = event_repository.create_event(
            db,
            data=event_data,
        )
        db.commit()
        db.refresh(event)
        return event
    except Exception:
        db.rollback()
        raise


def update_event(
    db: Session,
    *,
    event_id: UUID,
    data: dict,
) -> Event:
    event = get_event(db, event_id=event_id)

    updated_data = data.copy()

    if not updated_data:
        raise InvalidEventDataError(
            "At least one field must be provided."
        )

    if "client_id" in updated_data:
        _validate_client(
            db,
            client_id=updated_data["client_id"],
        )

    starts_at = updated_data.get("starts_at", event.starts_at)
    ends_at = updated_data.get("ends_at", event.ends_at)

    _validate_date_range(
        starts_at=starts_at,
        ends_at=ends_at,
    )

    if "status" in updated_data:
        new_status = _normalize_status(updated_data["status"])
        _validate_status_transition(
            current_status=event.status,
            new_status=new_status,
        )
        updated_data["status"] = new_status

    try:
        event = event_repository.update_event(
            db,
            event=event,
            data=updated_data,
        )
        db.commit()
        db.refresh(event)
        return event
    except Exception:
        db.rollback()
        raise


def cancel_event(
    db: Session,
    *,
    event_id: UUID,
) -> Event:
    event = get_event(db, event_id=event_id)

    if event.status in {
        EventStatus.COMPLETED.value,
        EventStatus.CANCELLED.value,
    }:
        raise InvalidEventDataError(
            "Completed or already cancelled events cannot be cancelled."
        )

    try:
        event = event_repository.update_event(
            db,
            event=event,
            data={"status": EventStatus.CANCELLED.value},
        )
        db.commit()
        db.refresh(event)
        return event
    except Exception:
        db.rollback()
        raise


def _validate_client(
    db: Session,
    *,
    client_id: UUID,
) -> None:
    client = client_repository.get_client_by_id(
        db,
        client_id=client_id,
    )

    if client is None or client.archived_at is not None:
        raise EventClientNotFoundError(
            "An active client from this tenant is required."
        )


def _validate_date_range(
    *,
    starts_at: datetime,
    ends_at: datetime,
) -> None:
    if starts_at.tzinfo is None or starts_at.utcoffset() is None:
        raise InvalidEventDataError(
            "Event start date must include timezone information."
        )

    if ends_at.tzinfo is None or ends_at.utcoffset() is None:
        raise InvalidEventDataError(
            "Event end date must include timezone information."
        )

    if starts_at >= ends_at:
        raise InvalidEventDataError(
            "Event end must be after event start."
        )


def _normalize_status(status: EventStatus | str) -> str:
    if isinstance(status, EventStatus):
        return status.value

    try:
        return EventStatus(status).value
    except ValueError as exc:
        raise InvalidEventDataError(
            "Invalid event status."
        ) from exc


def _validate_status_transition(
    *,
    current_status: str,
    new_status: str,
) -> None:
    if current_status == new_status:
        return

    allowed_statuses = ALLOWED_STATUS_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise InvalidEventDataError(
            f"Invalid event status transition: "
            f"{current_status} -> {new_status}."
        )
