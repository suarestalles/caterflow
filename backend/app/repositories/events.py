
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.event import Event


def get_event_by_id(
    db: Session,
    *,
    event_id: UUID,
) -> Event | None:
    statement = select(Event).where(Event.id == event_id)
    return db.scalar(statement)


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
    statement = select(Event)

    if search:
        statement = statement.where(Event.name.ilike(f"%{search}%"))

    if client_id is not None:
        statement = statement.where(Event.client_id == client_id)

    if status is not None:
        statement = statement.where(Event.status == status)

    if starts_at_from is not None:
        statement = statement.where(Event.starts_at >= starts_at_from)

    if starts_at_to is not None:
        statement = statement.where(Event.starts_at <= starts_at_to)

    total_statement = select(func.count()).select_from(
        statement.order_by(None).subquery()
    )
    total = db.scalar(total_statement) or 0

    items_statement = (
        statement
        .order_by(Event.starts_at.asc(), Event.id.asc())
        .offset(offset)
        .limit(limit)
    )

    items = list(db.scalars(items_statement).all())

    return items, total


def create_event(
    db: Session,
    *,
    data: dict,
) -> Event:
    event = Event(**data)
    db.add(event)
    db.flush()
    db.refresh(event)
    return event


def update_event(
    db: Session,
    *,
    event: Event,
    data: dict,
) -> Event:
    for field, value in data.items():
        setattr(event, field, value)

    db.flush()
    db.refresh(event)
    return event
