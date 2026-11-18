
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.db.tenant_session import TenantSession
from app.models.client import Client
from app.models.quote import Quote, QuoteStatus
from app.models.tenant import Tenant
from app.services.quotes import (
    InvalidQuoteDataError,
    QuoteClientNotFoundError,
    QuoteNotFoundError,
    create_quote,
    duplicate_quote,
    get_quote,
    send_quote,
    update_quote,
)


def create_tenant_session(db_session: Session, tenant_id):
    return TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant_id,
    )


def create_tenant_and_client(db_session: Session):
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.flush()

    client = Client(
        tenant_id=tenant.id,
        name="Maria Silva",
        email=f"{uuid4()}@example.com",
    )
    db_session.add(client)
    db_session.flush()

    return tenant, client


def quote_data(client_id, **overrides):
    data = {
        "client_id": client_id,
        "title": "Corporate Catering",
        "description": "Catering for a corporate event",
        "valid_until": None,
        "discount_amount": "20.00",
        "tax_amount": "10.00",
        "notes": "Contact before delivery",
        "terms": "Payment within 15 days",
        "items": [
            {
                "name": "Buffet",
                "description": "Complete buffet",
                "quantity": "2",
                "unit_price": "100.00",
                "position": 0,
            },
            {
                "name": "Waiter",
                "quantity": "2",
                "unit_price": "50.00",
                "position": 1,
            },
        ],
    }
    data.update(overrides)
    return data


def test_create_quote_calculates_totals(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        quote = create_quote(
            db,
            data=quote_data(client.id),
        )

        assert quote.quote_number == "Q-000001"
        assert quote.status == QuoteStatus.DRAFT
        assert quote.subtotal == 300
        assert quote.discount_amount == 20
        assert quote.tax_amount == 10
        assert quote.total_amount == 290
        assert len(quote.items) == 2
        assert quote.items[0].total_price == 200
        assert quote.items[1].total_price == 100
    finally:
        db.close()


def test_create_quote_generates_sequential_numbers(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        first = create_quote(db, data=quote_data(client.id))
        second = create_quote(
            db,
            data=quote_data(client.id, title="Second Quote"),
        )

        assert first.quote_number == "Q-000001"
        assert second.quote_number == "Q-000002"
    finally:
        db.close()


def test_create_quote_rejects_unknown_client(db_session):
    tenant, _ = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(QuoteClientNotFoundError):
            create_quote(
                db,
                data=quote_data(uuid4()),
            )
    finally:
        db.close()


def test_create_quote_rejects_discount_above_subtotal(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(InvalidQuoteDataError):
            create_quote(
                db,
                data=quote_data(
                    client.id,
                    discount_amount="500.00",
                ),
            )
    finally:
        db.close()


def test_get_quote_returns_quote(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        created = create_quote(db, data=quote_data(client.id))
        result = get_quote(db, quote_id=created.id)

        assert result.id == created.id
        assert result.quote_number == created.quote_number
    finally:
        db.close()


def test_get_quote_raises_when_not_found(db_session):
    tenant, _ = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(QuoteNotFoundError):
            get_quote(db, quote_id=uuid4())
    finally:
        db.close()


def test_update_quote_updates_draft_and_recalculates_totals(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        quote = create_quote(db, data=quote_data(client.id))

        updated = update_quote(
            db,
            quote_id=quote.id,
            data={
                "title": "Updated Catering",
                "items": [
                    {
                        "name": "Buffet",
                        "quantity": "3",
                        "unit_price": "100.00",
                        "position": 0,
                    }
                ],
                "discount_amount": "10.00",
                "tax_amount": "5.00",
            },
        )

        assert updated.title == "Updated Catering"
        assert updated.subtotal == 300
        assert updated.discount_amount == 10
        assert updated.tax_amount == 5
        assert updated.total_amount == 295
        assert len(updated.items) == 1
    finally:
        db.close()


def test_update_quote_rejects_non_draft_quote(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        quote = create_quote(db, data=quote_data(client.id))
        send_quote(db, quote_id=quote.id)

        with pytest.raises(InvalidQuoteDataError):
            update_quote(
                db,
                quote_id=quote.id,
                data={"title": "Cannot Update"},
            )
    finally:
        db.close()


def test_send_quote_changes_status_to_sent(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        quote = create_quote(db, data=quote_data(client.id))

        sent = send_quote(db, quote_id=quote.id)

        assert sent.status == QuoteStatus.SENT
    finally:
        db.close()


def test_duplicate_quote_creates_independent_draft(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        original = create_quote(db, data=quote_data(client.id))
        original_id = original.id
        original_number = original.quote_number

        duplicated = duplicate_quote(
            db,
            quote_id=original.id,
        )

        assert duplicated.id != original_id
        assert duplicated.quote_number != original_number
        assert duplicated.status == QuoteStatus.DRAFT
        assert duplicated.client_id == original.client_id
        assert duplicated.title == original.title
        assert len(duplicated.items) == len(original.items)
        assert duplicated.total_amount == original.total_amount
        assert original.status == QuoteStatus.DRAFT
    finally:
        db.close()


def test_duplicate_quote_does_not_change_original_items(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        original = create_quote(db, data=quote_data(client.id))
        original_items = [
            (item.name, item.quantity, item.unit_price)
            for item in original.items
        ]

        duplicated = duplicate_quote(
            db,
            quote_id=original.id,
        )

        duplicated.items[0].name = "Changed Item"
        db.flush()

        original_after = get_quote(
            db,
            quote_id=original.id,
        )

        assert [
            (item.name, item.quantity, item.unit_price)
            for item in original_after.items
        ] == original_items
    finally:
        db.close()
