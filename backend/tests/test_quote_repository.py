
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.tenant_session import TenantSession
from app.models.client import Client
from app.models.quote import Quote
from app.models.tenant import Tenant
from app.repositories import quotes as quote_repository
from app.models.quote_item import QuoteItem


def create_tenant_session(db_session: Session, tenant_id):
    return TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant_id,
    )


def create_tenant_and_client(db_session: Session, name="Maria Silva"):
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.flush()

    client = Client(
        tenant_id=tenant.id,
        name=name,
        email=f"{uuid4()}@example.com",
    )
    db_session.add(client)
    db_session.flush()

    return tenant, client


def quote_data(client_id, **overrides):
    data = {
        "client_id": client_id,
        "quote_number": "Q-000001",
        "title": "Corporate Catering",
        "description": "Catering for a corporate event",
        "status": "draft",
        "subtotal": 200.00,
        "discount_amount": 20.00,
        "tax_amount": 10.00,
        "total_amount": 190.00,
    }
    data.update(overrides)
    return data


def create_persisted_quote(db, client_id, **overrides):
    data = quote_data(client_id, **overrides)

    items_data = data.pop("items", [])

    quote = Quote(
        **data,
        items=[
            QuoteItem(**item)
            for item in items_data
        ],
    )

    db.add(quote)
    db.flush()

    return quote


def test_create_quote_persists_quote_and_items(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        quote = quote_repository.create_quote(
            db,
            data=quote_data(
                client.id,
                items=[
                    QuoteItem(
                        name="Buffet",
                        quantity=2,
                        unit_price=100.00,
                        total_price=200.00,
                        position=0,
                    )
                ],
            ),
        )

        assert quote.id is not None
        assert quote.client_id == client.id
        assert quote.quote_number == "Q-000001"
        assert len(quote.items) == 1
        assert quote.items[0].name == "Buffet"
    finally:
        db.close()


def test_get_quote_by_id_returns_quote_with_items(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        quote = create_persisted_quote(
            db,
            client.id,
            items=[
                {
                    "name": "Buffet",
                    "quantity": 2,
                    "unit_price": 100,
                    "total_price": 200,
                    "position": 0,
                }
            ],
        )
        db.flush()

        result = quote_repository.get_quote_by_id(
            db,
            quote_id=quote.id,
        )

        assert result is not None
        assert result.id == quote.id
        assert len(result.items) == 1
    finally:
        db.close()


def test_get_quote_by_id_returns_none_for_unknown_quote(db_session):
    tenant, _ = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        result = quote_repository.get_quote_by_id(
            db,
            quote_id=uuid4(),
        )

        assert result is None
    finally:
        db.close()


def test_list_quotes_returns_quotes_and_total(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        create_persisted_quote(
            db,
            client.id,
            quote_number="Q-000001",
            title="First Quote",
        )
        create_persisted_quote(
            db,
            client.id,
            quote_number="Q-000002",
            title="Second Quote",
        )
        db.flush()

        quotes, total = quote_repository.list_quotes(db)

        assert total == 2
        assert len(quotes) == 2
    finally:
        db.close()


def test_list_quotes_filters_by_client(db_session):
    tenant, first_client = create_tenant_and_client(db_session)
    second_client = Client(
        tenant_id=tenant.id,
        name="Another Client",
        email=f"{uuid4()}@example.com",
    )
    db_session.add(second_client)
    db_session.flush()

    db = create_tenant_session(db_session, tenant.id)

    try:
        create_persisted_quote(db, first_client.id)
        create_persisted_quote(
            db,
            second_client.id,
            quote_number="Q-000002",
        )
        db.flush()

        quotes, total = quote_repository.list_quotes(
            db,
            client_id=first_client.id,
        )

        assert total == 1
        assert len(quotes) == 1
        assert quotes[0].client_id == first_client.id
    finally:
        db.close()


def test_list_quotes_filters_by_status(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        create_persisted_quote(db, client.id)
        create_persisted_quote(
            db,
            client.id,
            quote_number="Q-000002",
            status="sent",
        )
        db.flush()

        quotes, total = quote_repository.list_quotes(
            db,
            status="sent",
        )

        assert total == 1
        assert quotes[0].status == "sent"
    finally:
        db.close()


def test_list_quotes_searches_by_quote_number_and_title(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        create_persisted_quote(
            db,
            client.id,
            title="Wedding Catering",
        )
        create_persisted_quote(
            db,
            client.id,
            quote_number="Q-000002",
            title="Corporate Lunch",
        )
        db.flush()

        quotes, total = quote_repository.list_quotes(
            db,
            search="Wedding",
        )

        assert total == 1
        assert quotes[0].title == "Wedding Catering"
    finally:
        db.close()


def test_list_quotes_applies_pagination(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        for number in range(1, 4):
            create_persisted_quote(
                db,
                client.id,
                quote_number=f"Q-{number:06d}",
            )
        db.flush()

        quotes, total = quote_repository.list_quotes(
            db,
            offset=1,
            limit=1,
        )

        assert total == 3
        assert len(quotes) == 1
    finally:
        db.close()


def test_list_quotes_does_not_return_other_tenant_quotes(db_session):
    tenant, client = create_tenant_and_client(db_session)

    other_tenant, other_client = create_tenant_and_client(
        db_session,
        name="Other Client",
    )

    create_persisted_quote(
        create_tenant_session(db_session, other_tenant.id),
        other_client.id,
    )

    db = create_tenant_session(db_session, tenant.id)

    try:
        create_persisted_quote(db, client.id)

        quotes, total = quote_repository.list_quotes(db)

        assert total == 1
        assert len(quotes) == 1
        assert quotes[0].tenant_id == tenant.id
    finally:
        db.close()


def test_update_quote_updates_fields(db_session):
    tenant, client = create_tenant_and_client(db_session)
    db = create_tenant_session(db_session, tenant.id)

    try:
        quote = create_persisted_quote(db, client.id)

        updated = quote_repository.update_quote(
            db,
            quote=quote,
            data={"title": "Updated Quote"},
        )

        assert updated.title == "Updated Quote"
    finally:
        db.close()
