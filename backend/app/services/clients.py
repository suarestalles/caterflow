from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.client import Client
from app.repositories import clients as client_repository


class ClientNotFoundError(Exception):
    pass


class InvalidClientDataError(Exception):
    pass


def list_clients(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
) -> tuple[list[Client], int]:
    return client_repository.list_clients(
        db,
        offset=offset,
        limit=limit,
        search=search,
    )


def get_client(
    db: Session,
    *,
    client_id: UUID,
) -> Client:
    client = client_repository.get_client_by_id(
        db,
        client_id,
    )

    if client is None or client.archived_at is not None:
        raise ClientNotFoundError

    return client


def create_client(
    db: Session,
    *,
    data: dict,
) -> Client:
    _validate_contact(
        email=data.get("email"),
        phone=data.get("phone"),
    )

    try:
        client = client_repository.create_client(
            db,
            data=data,
        )

        db.commit()
        db.refresh(client)

        return client
    except Exception:
        db.rollback()
        raise


def update_client(
    db: Session,
    *,
    client_id: UUID,
    data: dict,
) -> Client:
    client = get_client(
        db,
        client_id=client_id,
    )

    updated_email = data.get("email", client.email)
    updated_phone = data.get("phone", client.phone)

    _validate_contact(
        email=updated_email,
        phone=updated_phone,
    )

    if data.get("name", client.name) is None:
        raise InvalidClientDataError("Client name cannot be null.")

    if data.get("client_type", client.client_type) is None:
        raise InvalidClientDataError("Client type cannot be null.")

    if data.get("country", client.country) is None:
        raise InvalidClientDataError("Client country cannot be null.")

    try:
        client = client_repository.update_client(
            db,
            client=client,
            data=data,
        )

        db.commit()
        db.refresh(client)

        return client
    except Exception:
        db.rollback()
        raise


def archive_client(
    db: Session,
    *,
    client_id: UUID,
) -> None:
    client = get_client(
        db,
        client_id=client_id,
    )

    try:
        client_repository.archive_client(
            db,
            client=client,
            archived_at=datetime.now(UTC),
        )

        db.commit()
    except Exception:
        db.rollback()
        raise


def _validate_contact(
    *,
    email: str | None,
    phone: str | None,
) -> None:
    if not email and not phone:
        raise InvalidClientDataError("At least one contact method (email or phone) is required.")
