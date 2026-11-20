
import re

from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.event import Event
from app.models.product import Product
from app.models.quote import Quote, QuoteStatus
from app.models.quote_item import QuoteItem
from app.models.tenant import Tenant
from app.repositories import clients as client_repository
from app.repositories import events as event_repository
from app.repositories import products as product_repository
from app.repositories import quotes as quote_repository


class QuoteNotFoundError(Exception):
    pass


class QuoteClientNotFoundError(Exception):
    pass


class QuoteEventNotFoundError(Exception):
    pass


class QuoteProductNotFoundError(Exception):
    pass


class InvalidQuoteDataError(Exception):
    pass


CENT = Decimal("0.01")


def _money(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _calculate_totals(
    items: list[dict[str, Any]],
    discount_amount: Decimal,
    tax_amount: Decimal,
) -> dict[str, Decimal]:
    item_totals = [
        _money(
            Decimal(str(item["quantity"]))
            * Decimal(str(item["unit_price"]))
        )
        for item in items
    ]

    subtotal = _money(sum(item_totals, Decimal("0")))
    discount = _money(discount_amount)
    tax = _money(tax_amount)

    if discount > subtotal:
        raise InvalidQuoteDataError(
            "Discount cannot exceed the quote subtotal."
        )

    return {
        "subtotal": subtotal,
        "discount_amount": discount,
        "tax_amount": tax,
        "total_amount": _money(subtotal - discount + tax),
    }


def _validate_client(db: Session, *, client_id: UUID) -> Client:
    client = client_repository.get_client_by_id(
        db,
        client_id=client_id,
    )

    if client is None or client.archived_at is not None:
        raise QuoteClientNotFoundError("Client not found.")

    return client


def _validate_event(
    db: Session,
    *,
    event_id: UUID | None,
    client_id: UUID,
) -> Event | None:
    if event_id is None:
        return None

    event = event_repository.get_event_by_id(
        db,
        event_id=event_id,
    )

    if event is None:
        raise QuoteEventNotFoundError("Event not found.")

    if event.client_id != client_id:
        raise InvalidQuoteDataError(
            "The event must belong to the selected client."
        )

    return event


def _resolve_items(
    db: Session,
    *,
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    resolved_items = []

    for item in items:
        resolved = item.copy()
        product_id = resolved.get("product_id")

        if product_id is not None:
            product = product_repository.get_product_by_id(
                db,
                product_id=product_id,
            )

            if product is None:
                raise QuoteProductNotFoundError("Product not found.")

            if not product.is_active:
                raise InvalidQuoteDataError(
                    "Archived products cannot be added to new quotes."
                )

            name = resolved.get("name") or product.name
            description = resolved.get("description") or product.description
            unit = resolved.get("unit") or product.unit

            unit_price = resolved.get("unit_price")
            if unit_price is None:
                unit_price = product.sale_price

        else:
            name = resolved.get("name")
            description = resolved.get("description")
            unit = resolved.get("unit")
            unit_price = resolved.get("unit_price")

            if name is None:
                raise InvalidQuoteDataError(
                    "Item name is required when no catalog product is selected."
                )

            if unit_price is None:
                raise InvalidQuoteDataError(
                    "Unit price is required when no catalog product is selected."
                )

        if not name or not str(name).strip():
            raise InvalidQuoteDataError("Item name cannot be empty.")

        if unit_price is None:
            raise InvalidQuoteDataError("Item unit price is required.")

        resolved_items.append(
            {
                **resolved,
                "product_id": product_id,
                "name": str(name).strip(),
                "description": description,
                "unit": getattr(unit, "value", unit),
                "unit_price": unit_price,
            }
        )

    return resolved_items


def _generate_quote_number(db: Session) -> str:
    tenant_id = db.tenant_id

    # Serialize number generation for this tenant.
    db.execute(
        select(Tenant.id)
        .where(Tenant.id == tenant_id)
        .with_for_update()
    ).scalar_one()

    existing_numbers = db.scalars(
        select(Quote.quote_number)
        .order_by(Quote.created_at.desc())
    ).all()

    highest_number = 0

    for quote_number in existing_numbers:
        match = re.fullmatch(r"Q-(\d+)", quote_number)

        if match:
            highest_number = max(highest_number, int(match.group(1)))

    return f"Q-{highest_number + 1:06d}"


def _build_items(items: list[dict[str, Any]]) -> list[QuoteItem]:
    return [
        QuoteItem(
            product_id=item.get("product_id"),
            name=item["name"],
            description=item.get("description"),
            unit=item.get("unit"),
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            total_price=_money(
                Decimal(str(item["quantity"]))
                * Decimal(str(item["unit_price"]))
            ),
            position=item.get("position", 0),
        )
        for item in items
    ]


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
    return quote_repository.list_quotes(
        db,
        offset=offset,
        limit=limit,
        search=search,
        client_id=client_id,
        event_id=event_id,
        status=status,
    )


def get_quote(db: Session, *, quote_id: UUID) -> Quote:
    quote = quote_repository.get_quote_by_id(
        db,
        quote_id=quote_id,
    )

    if quote is None:
        raise QuoteNotFoundError("Quote not found.")

    return quote


def create_quote(
    db: Session,
    *,
    data: dict[str, Any],
) -> Quote:
    data = data.copy()

    try:
        client_id = data["client_id"]
        _validate_client(db, client_id=client_id)

        _validate_event(
            db,
            event_id=data.get("event_id"),
            client_id=client_id,
        )

        items_data = _resolve_items(
            db,
            items=data.pop("items"),
        )

        discount = data.get("discount_amount", Decimal("0"))
        tax = data.get("tax_amount", Decimal("0"))

        totals = _calculate_totals(items_data, discount, tax)

        quote = quote_repository.create_quote(
            db,
            data={
                **data,
                **totals,
                "quote_number": _generate_quote_number(db),
                "items": _build_items(items_data),
            },
        )

        db.commit()
        db.refresh(quote)
        return quote

    except Exception:
        db.rollback()
        raise


def update_quote(
    db: Session,
    *,
    quote_id: UUID,
    data: dict[str, Any],
) -> Quote:
    data = data.copy()

    try:
        quote = get_quote(db, quote_id=quote_id)

        if quote.status != QuoteStatus.DRAFT:
            raise InvalidQuoteDataError(
                "Only draft quotes can be updated."
            )

        if "client_id" in data:
            if data["client_id"] is None:
                raise InvalidQuoteDataError("Client is required.")

            _validate_client(db, client_id=data["client_id"])

        client_id = data.get("client_id", quote.client_id)
        event_id = data.get("event_id", quote.event_id)

        _validate_event(
            db,
            event_id=event_id,
            client_id=client_id,
        )

        items_data = data.pop("items", None)

        if items_data is not None:
            items_data = _resolve_items(
                db,
                items=items_data,
            )

            quote.items.clear()
            quote.items.extend(_build_items(items_data))

        discount = data.get("discount_amount", quote.discount_amount)
        tax = data.get("tax_amount", quote.tax_amount)

        if items_data is not None:
            totals_items = items_data
        else:
            totals_items = [
                {
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                }
                for item in quote.items
            ]

        totals = _calculate_totals(totals_items, discount, tax)

        quote_repository.update_quote(
            db,
            quote=quote,
            data={
                **data,
                **totals,
            },
        )

        db.commit()
        db.refresh(quote)
        return quote

    except Exception:
        db.rollback()
        raise


def send_quote(db: Session, *, quote_id: UUID) -> Quote:
    try:
        quote = get_quote(db, quote_id=quote_id)

        if quote.status != QuoteStatus.DRAFT:
            raise InvalidQuoteDataError(
                "Only draft quotes can be sent."
            )

        quote.status = QuoteStatus.SENT
        db.flush()
        db.commit()
        db.refresh(quote)
        return quote

    except Exception:
        db.rollback()
        raise


def duplicate_quote(
    db: Session,
    *,
    quote_id: UUID,
) -> Quote:
    try:
        original = get_quote(db, quote_id=quote_id)

        duplicated = quote_repository.duplicate_quote(
            db,
            original=original,
            quote_number=_generate_quote_number(db),
        )

        db.commit()
        db.refresh(duplicated)

        return duplicated

    except Exception:
        db.rollback()
        raise
