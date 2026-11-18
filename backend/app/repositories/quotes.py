
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.client import Client
from app.models.quote import Quote
from app.models.quote_item import QuoteItem


def get_quote_by_id(db: Session, *, quote_id: UUID) -> Quote | None:
    statement = (
        select(Quote)
        .options(selectinload(Quote.items))
        .where(Quote.id == quote_id)
    )
    return db.scalar(statement)


def list_quotes(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
    client_id: UUID | None = None,
    event_id: UUID | None = None,
    status: str | None = None,
) -> tuple[list[Quote], int]:
    statement = select(Quote).join(Client, Quote.client_id == Client.id)

    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Quote.quote_number.ilike(term),
                Quote.title.ilike(term),
                Client.name.ilike(term),
            )
        )

    if client_id:
        statement = statement.where(Quote.client_id == client_id)

    if event_id:
        statement = statement.where(Quote.event_id == event_id)

    if status:
        statement = statement.where(Quote.status == status)

    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery()
    )
    total = db.scalar(count_statement) or 0

    statement = (
        statement.options(selectinload(Quote.items))
        .order_by(Quote.created_at.desc(), Quote.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).unique().all()), total


def create_quote(db: Session, *, data: dict[str, Any]) -> Quote:
    quote = Quote(**data)
    db.add(quote)
    db.flush()
    db.refresh(quote)
    return quote


def update_quote(
    db: Session,
    *,
    quote: Quote,
    data: dict[str, Any],
) -> Quote:
    for field, value in data.items():
        setattr(quote, field, value)

    db.flush()
    db.refresh(quote)
    return quote


def duplicate_quote(
    db: Session,
    *,
    original: Quote,
    quote_number: str,
) -> Quote:
    duplicated = Quote(
        client_id=original.client_id,
        event_id=original.event_id,
        quote_number=quote_number,
        title=original.title,
        description=original.description,
        status="draft",
        valid_until=original.valid_until,
        discount_amount=original.discount_amount,
        tax_amount=original.tax_amount,
        notes=original.notes,
        terms=original.terms,
        subtotal=original.subtotal,
        total_amount=original.total_amount,
        items=[
            QuoteItem(
                name=item.name,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                position=item.position,
            )
            for item in original.items
        ],
    )

    db.add(duplicated)
    db.flush()
    db.refresh(duplicated)

    return duplicated
