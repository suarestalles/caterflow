
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import (
    AuthContext,
    get_auth_context,
    get_current_tenant_db,
)
from app.core.permissions import PermissionCode
from app.db.session import get_db
from app.db.tenant_session import TenantSession
from app.main import app
from app.models.client import Client
from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.permission import Permission
from app.models.product import Product, ProductType
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant
from app.models.user import User


def create_tenant(db_session: Session, name="Test Tenant"):
    tenant = Tenant(name=name)
    db_session.add(tenant)
    db_session.flush()
    return tenant


def create_user(db_session: Session):
    user = User(
        full_name="Test User",
        email=f"{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_client_for_tenant(db_session, tenant):
    client = Client(
        tenant_id=tenant.id,
        name="Maria Silva",
        email=f"{uuid4()}@example.com",
    )
    db_session.add(client)
    db_session.flush()
    return client

def create_product_for_tenant(db_session, tenant, **overrides):
    data = {
        "tenant_id": tenant.id,
        "name": "Mini sanduíche",
        "description": "Mini sanduíche natural",
        "type": ProductType.PRODUCT.value,
        "unit": "unit",
        "sku": None,
        "sale_price": Decimal("2.50"),
        "cost_price": Decimal("1.20"),
        "is_active": True,
        **overrides,
    }

    product = Product(**data)
    db_session.add(product)
    db_session.flush()

    return product


def assign_permissions(
    db_session,
    *,
    tenant,
    membership,
    permission_codes,
):
    role = Role(
        tenant_id=tenant.id,
        name="Test Role",
        is_system=False,
    )
    db_session.add(role)
    db_session.flush()

    db_session.add(
        MembershipRole(
            tenant_id=tenant.id,
            membership_id=membership.id,
            role_id=role.id,
        )
    )

    for permission_code in permission_codes:
        code = permission_code.value

        permission = db_session.scalar(
            select(Permission).where(Permission.code == code)
        )

        if permission is None:
            permission = Permission(
                code=code,
                description=f"Permission {code}",
            )
            db_session.add(permission)
            db_session.flush()

        db_session.add(
            RolePermission(
                tenant_id=tenant.id,
                role_id=role.id,
                permission_id=permission.id,
            )
        )

    db_session.flush()


def api_client_factory(db_session, permissions=None):
    tenant = create_tenant(db_session)
    user = create_user(db_session)

    membership = Membership(
        user_id=user.id,
        tenant_id=tenant.id,
    )
    db_session.add(membership)
    db_session.flush()

    assign_permissions(
        db_session,
        tenant=tenant,
        membership=membership,
        permission_codes=permissions or [],
    )

    def override_auth_context():
        return AuthContext(
            user=user,
            tenant_id=tenant.id,
        )

    def override_tenant_db():
        tenant_db = TenantSession(
            bind=db_session.connection(),
            join_transaction_mode="create_savepoint",
            tenant_id=tenant.id,
        )
        try:
            yield tenant_db
        finally:
            tenant_db.close()

    app.dependency_overrides[get_auth_context] = override_auth_context
    app.dependency_overrides[get_current_tenant_db] = override_tenant_db

    return TestClient(app), tenant, user


def create_quote_payload(client_id, **overrides):
    payload = {
        "client_id": str(client_id),
        "title": "Corporate Catering",
        "description": "Catering for a corporate event",
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
    payload.update(overrides)
    return payload


@pytest.fixture
def api_client(db_session):
    client, tenant, user = api_client_factory(
        db_session,
        permissions=[
            PermissionCode.QUOTES_READ,
            PermissionCode.QUOTES_CREATE,
            PermissionCode.QUOTES_UPDATE,
            PermissionCode.QUOTES_SEND,
        ],
    )

    try:
        yield client, tenant, user
    finally:
        app.dependency_overrides.clear()


def test_create_quote_returns_201(db_session, api_client):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)

    with client:
        response = client.post(
            "/api/v1/quotes/",
            json=create_quote_payload(quote_client.id),
        )

    assert response.status_code == 201
    body = response.json()

    assert body["title"] == "Corporate Catering"
    assert body["client_id"] == str(quote_client.id)
    assert body["tenant_id"] == str(tenant.id)
    assert body["quote_number"] == "Q-000001"
    assert body["status"] == "draft"
    assert float(body["subtotal"]) == 300
    assert float(body["total_amount"]) == 290


def test_create_quote_with_invalid_client_returns_404(api_client):
    client, _, _ = api_client

    with client:
        response = client.post(
            "/api/v1/quotes/",
            json=create_quote_payload(uuid4()),
        )

    assert response.status_code == 404


def test_create_quote_with_invalid_items_returns_422(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)

    with client:
        response = client.post(
            "/api/v1/quotes/",
            json=create_quote_payload(
                quote_client.id,
                items=[],
            ),
        )

    assert response.status_code == 422


def test_create_quote_without_permission_returns_403(db_session):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[],
    )

    try:
        quote_client = create_client_for_tenant(db_session, tenant)

        with client:
            response = client.post(
                "/api/v1/quotes/",
                json=create_quote_payload(quote_client.id),
            )

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions."
    finally:
        app.dependency_overrides.clear()


def test_list_quotes_returns_200_and_pagination(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)

    with client:
        client.post(
            "/api/v1/quotes/",
            json=create_quote_payload(quote_client.id),
        )

        response = client.get(
            "/api/v1/quotes/",
            params={"offset": 0, "limit": 10},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["offset"] == 0
    assert response.json()["limit"] == 10


def test_list_quotes_without_permission_returns_403(db_session):
    client, _, _ = api_client_factory(
        db_session,
        permissions=[],
    )

    try:
        with client:
            response = client.get("/api/v1/quotes/")

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_get_quote_returns_200(db_session, api_client):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)

    with client:
        created = client.post(
            "/api/v1/quotes/",
            json=create_quote_payload(quote_client.id),
        )
        quote_id = created.json()["id"]

        response = client.get(f"/api/v1/quotes/{quote_id}")

    assert response.status_code == 200
    assert response.json()["id"] == quote_id


def test_get_quote_from_another_tenant_returns_404(
    db_session,
    api_client,
):
    client, _, _ = api_client

    other_tenant = create_tenant(
        db_session,
        name="Other Tenant",
    )
    other_client = create_client_for_tenant(
        db_session,
        other_tenant,
    )

    other_db = TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=other_tenant.id,
    )

    try:
        from app.services.quotes import create_quote

        quote = create_quote(
            other_db,
            data=create_quote_payload(other_client.id),
        )
        quote_id = quote.id
    finally:
        other_db.close()

    with client:
        response = client.get(f"/api/v1/quotes/{quote_id}")

    assert response.status_code == 404


def test_update_quote_returns_200(db_session, api_client):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)

    with client:
        created = client.post(
            "/api/v1/quotes/",
            json=create_quote_payload(quote_client.id),
        )
        quote_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/quotes/{quote_id}",
            json={"title": "Updated Catering Quote"},
        )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Catering Quote"


def test_update_quote_without_permission_returns_403(db_session):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.QUOTES_READ],
    )

    try:
        quote_client = create_client_for_tenant(db_session, tenant)

        with client:
            created = client.post(
                "/api/v1/quotes/",
                json=create_quote_payload(quote_client.id),
            )

        # Cria um orçamento diretamente para testar apenas a permissão.
        from app.services.quotes import create_quote

        db = TenantSession(
            bind=db_session.connection(),
            join_transaction_mode="create_savepoint",
            tenant_id=tenant.id,
        )
        try:
            quote = create_quote(
                db,
                data=create_quote_payload(quote_client.id),
            )
            quote_id = quote.id
        finally:
            db.close()

        with client:
            response = client.patch(
                f"/api/v1/quotes/{quote_id}",
                json={"title": "Updated"},
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_send_quote_returns_200(db_session, api_client):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)

    with client:
        created = client.post(
            "/api/v1/quotes/",
            json=create_quote_payload(quote_client.id),
        )
        quote_id = created.json()["id"]

        response = client.post(
            f"/api/v1/quotes/{quote_id}/send",
        )

    assert response.status_code == 200
    assert response.json()["status"] == "sent"


def test_send_quote_without_permission_returns_403(db_session):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.QUOTES_READ],
    )

    try:
        quote_client = create_client_for_tenant(db_session, tenant)

        from app.services.quotes import create_quote

        db = TenantSession(
            bind=db_session.connection(),
            join_transaction_mode="create_savepoint",
            tenant_id=tenant.id,
        )
        try:
            quote = create_quote(
                db,
                data=create_quote_payload(quote_client.id),
            )
            quote_id = quote.id
        finally:
            db.close()

        with client:
            response = client.post(
                f"/api/v1/quotes/{quote_id}/send",
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_duplicate_quote_returns_201_and_creates_draft(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)

    with client:
        created = client.post(
            "/api/v1/quotes/",
            json=create_quote_payload(quote_client.id),
        )
        original = created.json()

        response = client.post(
            f"/api/v1/quotes/{original['id']}/duplicate",
        )

    assert response.status_code == 201

    duplicated = response.json()

    assert duplicated["id"] != original["id"]
    assert duplicated["quote_number"] != original["quote_number"]
    assert duplicated["status"] == "draft"
    assert duplicated["client_id"] == original["client_id"]
    assert float(duplicated["total_amount"]) == float(
        original["total_amount"]
    )


def test_duplicate_quote_without_create_permission_returns_403(
    db_session,
):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.QUOTES_READ],
    )

    try:
        quote_client = create_client_for_tenant(db_session, tenant)

        from app.services.quotes import create_quote

        db = TenantSession(
            bind=db_session.connection(),
            join_transaction_mode="create_savepoint",
            tenant_id=tenant.id,
        )
        try:
            quote = create_quote(
                db,
                data=create_quote_payload(quote_client.id),
            )
            quote_id = quote.id
        finally:
            db.close()

        with client:
            response = client.post(
                f"/api/v1/quotes/{quote_id}/duplicate",
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_quotes_without_authentication_return_401(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/quotes/")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_create_quote_with_catalog_product_returns_201(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)
    product = create_product_for_tenant(db_session, tenant)

    payload = create_quote_payload(
        quote_client.id,
        discount_amount="0.00",
        tax_amount="0.00",
        items=[
            {
                "product_id": str(product.id),
                "quantity": "10",
                "position": 0,
            }
        ],
    )

    with client:
        response = client.post(
            "/api/v1/quotes/",
            json=payload,
        )

    assert response.status_code == 201

    body = response.json()
    item = body["items"][0]

    assert item["product_id"] == str(product.id)
    assert item["name"] == "Mini sanduíche"
    assert item["description"] == "Mini sanduíche natural"
    assert item["unit"] == "unit"
    assert Decimal(item["quantity"]) == Decimal("10")
    assert Decimal(item["unit_price"]) == Decimal("2.50")
    assert Decimal(item["total_price"]) == Decimal("25.00")
    assert Decimal(body["subtotal"]) == Decimal("25.00")


def test_create_quote_with_negotiated_product_price_returns_201(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)
    product = create_product_for_tenant(db_session, tenant)

    payload = create_quote_payload(
        quote_client.id,
        discount_amount="0.00",
        tax_amount="0.00",
        items=[
            {
                "product_id": str(product.id),
                "quantity": "10",
                "unit_price": "2.30",
                "position": 0,
            }
        ],
    )

    with client:
        response = client.post(
            "/api/v1/quotes/",
            json=payload,
        )

    assert response.status_code == 201

    item = response.json()["items"][0]

    assert Decimal(item["unit_price"]) == Decimal("2.30")
    assert Decimal(item["total_price"]) == Decimal("23.00")

    # Negotiated price must not change the catalog price.
    assert product.sale_price == Decimal("2.50")


def test_create_quote_with_nonexistent_product_returns_404(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)

    payload = create_quote_payload(
        quote_client.id,
        items=[
            {
                "product_id": str(uuid4()),
                "quantity": "2",
                "position": 0,
            }
        ],
    )

    with client:
        response = client.post(
            "/api/v1/quotes/",
            json=payload,
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found."


def test_create_quote_with_product_from_another_tenant_returns_404(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)

    other_tenant = create_tenant(
        db_session,
        name="Other Tenant",
    )
    product = create_product_for_tenant(
        db_session,
        other_tenant,
    )

    payload = create_quote_payload(
        quote_client.id,
        items=[
            {
                "product_id": str(product.id),
                "quantity": "2",
                "position": 0,
            }
        ],
    )

    with client:
        response = client.post(
            "/api/v1/quotes/",
            json=payload,
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found."


def test_create_quote_with_archived_product_returns_422(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)

    product = create_product_for_tenant(
        db_session,
        tenant,
        is_active=False,
    )

    payload = create_quote_payload(
        quote_client.id,
        items=[
            {
                "product_id": str(product.id),
                "quantity": "2",
                "position": 0,
            }
        ],
    )

    with client:
        response = client.post(
            "/api/v1/quotes/",
            json=payload,
        )

    assert response.status_code == 422
    assert "Archived products" in response.json()["detail"]


def test_update_quote_with_catalog_product_returns_200(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)
    product = create_product_for_tenant(db_session, tenant)

    with client:
        created = client.post(
            "/api/v1/quotes/",
            json=create_quote_payload(quote_client.id),
        )

        assert created.status_code == 201

        quote_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/quotes/{quote_id}",
            json={
                "items": [
                    {
                        "product_id": str(product.id),
                        "quantity": "4",
                        "position": 0,
                    }
                ],
                "discount_amount": "0.00",
                "tax_amount": "0.00",
            },
        )

    assert response.status_code == 200

    body = response.json()
    item = body["items"][0]

    assert len(body["items"]) == 1
    assert item["product_id"] == str(product.id)
    assert item["name"] == "Mini sanduíche"
    assert item["unit"] == "unit"
    assert Decimal(item["unit_price"]) == Decimal("2.50")
    assert Decimal(item["total_price"]) == Decimal("10.00")
    assert Decimal(body["subtotal"]) == Decimal("10.00")


def test_duplicate_quote_preserves_catalog_product_snapshot(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    quote_client = create_client_for_tenant(db_session, tenant)
    product = create_product_for_tenant(db_session, tenant)

    payload = create_quote_payload(
        quote_client.id,
        discount_amount="0.00",
        tax_amount="0.00",
        items=[
            {
                "product_id": str(product.id),
                "quantity": "10",
                "unit_price": "2.30",
                "position": 0,
            }
        ],
    )

    with client:
        created = client.post(
            "/api/v1/quotes/",
            json=payload,
        )

        assert created.status_code == 201

        original = created.json()
        original_item = original["items"][0]

        # Change the catalog after creating the original quote.
        product.name = "Novo nome"
        product.sale_price = Decimal("9.99")
        product.is_active = False
        db_session.flush()

        response = client.post(
            f"/api/v1/quotes/{original['id']}/duplicate",
        )

    assert response.status_code == 201

    duplicated = response.json()
    duplicated_item = duplicated["items"][0]

    assert duplicated["id"] != original["id"]
    assert duplicated["status"] == "draft"

    assert duplicated_item["product_id"] == str(product.id)
    assert duplicated_item["name"] == original_item["name"]
    assert duplicated_item["description"] == original_item["description"]
    assert duplicated_item["unit"] == original_item["unit"]
    assert duplicated_item["quantity"] == original_item["quantity"]
    assert duplicated_item["unit_price"] == original_item["unit_price"]
    assert duplicated_item["total_price"] == original_item["total_price"]

    assert duplicated["subtotal"] == original["subtotal"]
    assert duplicated["total_amount"] == original["total_amount"]
