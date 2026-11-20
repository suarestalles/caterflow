
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.db.tenant_session import TenantSession
from app.models.client import Client
from app.models.product import Product, ProductType
from app.models.quote import QuoteStatus
from app.models.tenant import Tenant
from app.services.quotes import (
    InvalidQuoteDataError,
    QuoteClientNotFoundError,
    QuoteNotFoundError,
    QuoteProductNotFoundError,
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

def create_product(db_session, tenant_id, **overrides):
    data = {
        "tenant_id": tenant_id,
        "name": "Mini sanduíche",
        "description": "Mini sanduíche natural",
        "type": ProductType.PRODUCT.value,
        "unit": "unit",
        "sku": None,
        "sale_price": Decimal("2.50"),
        "cost_price": Decimal("1.20"),
        **overrides,
    }

    product = Product(**data)
    db_session.add(product)
    db_session.flush()

    return product


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


def test_create_quote_with_catalog_product(db_session):
    tenant, client = create_tenant_and_client(db_session)

    product = create_product(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    try:
        quote = create_quote(
            db,
            data=quote_data(
                client.id,
                items=[
                    {
                        "product_id": product.id,
                        "quantity": "10",
                        "position": 0,
                    }
                ],
            ),
        )

        item = quote.items[0]

        assert item.product_id == product.id
        assert item.name == "Mini sanduíche"
        assert item.description == "Mini sanduíche natural"
        assert item.unit == "unit"
        assert item.quantity == 10
        assert item.unit_price == Decimal("2.50")
        assert item.total_price == Decimal("25.00")
        assert quote.subtotal == Decimal("25.00")

    finally:
        db.close()


def test_create_quote_with_negotiated_product_price(db_session):
    tenant, client = create_tenant_and_client(db_session)

    product = create_product(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    try:
        quote = create_quote(
            db,
            data=quote_data(
                client.id,
                items=[
                    {
                        "product_id": product.id,
                        "quantity": "10",
                        "unit_price": "2.30",
                        "position": 0,
                    }
                ],
            ),
        )

        item = quote.items[0]

        assert item.product_id == product.id
        assert item.unit_price == Decimal("2.30")
        assert item.total_price == Decimal("23.00")
        assert quote.subtotal == Decimal("23.00")

        # The catalog price remains unchanged.
        assert product.sale_price == Decimal("2.50")

    finally:
        db.close()


def test_create_quote_rejects_product_from_another_tenant(db_session):
    tenant, client = create_tenant_and_client(db_session)
    other_tenant = Tenant(name="Other Tenant")
    db_session.add(other_tenant)
    db_session.flush()

    product = create_product(db_session, other_tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(QuoteProductNotFoundError):
            create_quote(
                db,
                data=quote_data(
                    client.id,
                    items=[
                        {
                            "product_id": product.id,
                            "quantity": "2",
                            "position": 0,
                        }
                    ],
                ),
            )

    finally:
        db.close()


def test_create_quote_rejects_archived_product(db_session):
    tenant, client = create_tenant_and_client(db_session)

    product = create_product(
        db_session,
        tenant.id,
        is_active=False,
    )

    db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(InvalidQuoteDataError):
            create_quote(
                db,
                data=quote_data(
                    client.id,
                    items=[
                        {
                            "product_id": product.id,
                            "quantity": "2",
                            "position": 0,
                        }
                    ],
                ),
            )

    finally:
        db.close()


def test_quote_preserves_product_snapshot_after_catalog_update(db_session):
    tenant, client = create_tenant_and_client(db_session)

    product = create_product(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    try:
        quote = create_quote(
            db,
            data=quote_data(
                client.id,
                items=[
                    {
                        "product_id": product.id,
                        "quantity": "10",
                        "position": 0,
                    }
                ],
            ),
        )

        product.name = "Mini sanduíche atualizado"
        product.description = "Nova descrição"
        product.unit = "package"
        product.sale_price = Decimal("9.99")

        db_session.flush()

        updated_quote = get_quote(db, quote_id=quote.id)
        item = updated_quote.items[0]

        assert item.product_id == product.id
        assert item.name == "Mini sanduíche"
        assert item.description == "Mini sanduíche natural"
        assert item.unit == "unit"
        assert item.unit_price == Decimal("2.50")
        assert item.total_price == Decimal("25.00")

    finally:
        db.close()


def test_update_quote_replaces_items_with_catalog_product(db_session):
    tenant, client = create_tenant_and_client(db_session)

    product = create_product(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    try:
        quote = create_quote(db, data=quote_data(client.id))

        updated = update_quote(
            db,
            quote_id=quote.id,
            data={
                "items": [
                    {
                        "product_id": product.id,
                        "quantity": "4",
                        "position": 0,
                    }
                ],
                "discount_amount": "0.00",
            },
        )

        assert len(updated.items) == 1
        assert updated.items[0].product_id == product.id
        assert updated.items[0].name == "Mini sanduíche"
        assert updated.items[0].unit == "unit"
        assert updated.items[0].unit_price == Decimal("2.50")
        assert updated.items[0].total_price == Decimal("10.00")
        assert updated.subtotal == Decimal("10.00")

    finally:
        db.close()


def test_duplicate_quote_preserves_catalog_product_snapshot(db_session):
    tenant, client = create_tenant_and_client(db_session)

    product = create_product(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    try:
        original = create_quote(
            db,
            data=quote_data(
                client.id,
                items=[
                    {
                        "product_id": product.id,
                        "quantity": "10",
                        "unit_price": "2.30",
                        "position": 0,
                    }
                ],
            ),
        )

        original_item = original.items[0]

        product.name = "Novo nome"
        product.sale_price = Decimal("9.99")
        product.is_active = False
        db_session.flush()

        duplicated = duplicate_quote(
            db,
            quote_id=original.id,
        )

        duplicated_item = duplicated.items[0]

        assert duplicated.id != original.id
        assert duplicated.status == QuoteStatus.DRAFT
        assert duplicated_item.product_id == product.id
        assert duplicated_item.name == original_item.name
        assert duplicated_item.description == original_item.description
        assert duplicated_item.unit == original_item.unit
        assert duplicated_item.quantity == original_item.quantity
        assert duplicated_item.unit_price == original_item.unit_price
        assert duplicated_item.total_price == original_item.total_price

        assert duplicated.subtotal == original.subtotal
        assert duplicated.total_amount == original.total_amount

    finally:
        db.close()
