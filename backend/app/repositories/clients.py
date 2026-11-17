from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.client import Client


def get_client_by_id(
    db: Session,
    client_id: UUID,
) -> Client | None:
    statement = select(Client).where(Client.id == client_id)
    return db.scalar(statement)


def list_clients(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
) -> tuple[list[Client], int]:
    statement = select(Client).where(Client.archived_at.is_(None))

    if search:
        search_term = f"%{search.strip()}%"

        statement = statement.where(
            or_(
                Client.name.ilike(search_term),
                Client.email.ilike(search_term),
                Client.phone.ilike(search_term),
            )
        )

    count_statement = select(func.count()).select_from(statement.order_by(None).subquery())

    total = db.scalar(count_statement) or 0

    statement = statement.order_by(Client.name.asc(), Client.id.asc()).offset(offset).limit(limit)

    clients = list(db.scalars(statement).all())

    return clients, total


def create_client(
    db: Session,
    *,
    data: dict,
) -> Client:
    client = Client(**data)

    db.add(client)
    db.flush()
    db.refresh(client)

    return client


def update_client(
    db: Session,
    *,
    client: Client,
    data: dict,
) -> Client:
    for field, value in data.items():
        setattr(client, field, value)

    db.flush()
    db.refresh(client)

    return client


def archive_client(
    db: Session,
    *,
    client: Client,
    archived_at,
) -> Client:
    client.archived_at = archived_at

    db.flush()
    db.refresh(client)

    return client
