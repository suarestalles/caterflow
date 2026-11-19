
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import AuthContext, get_auth_context, get_current_tenant_db
from app.core.permissions import PermissionCode
from app.db.session import get_db
from app.db.tenant_session import TenantSession
from app.main import app
from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant
from app.models.user import User


def create_tenant(db_session: Session, name: str = "Test Tenant") -> Tenant:
    tenant = Tenant(name=name)
    db_session.add(tenant)
    db_session.flush()
    return tenant


def create_user(db_session: Session, email: str | None = None) -> User:
    user = User(
        full_name="Test User",
        email=email or f"user-{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_membership(
    db_session: Session,
    *,
    user: User,
    tenant: Tenant,
) -> Membership:
    membership = Membership(user_id=user.id, tenant_id=tenant.id)
    db_session.add(membership)
    db_session.flush()
    return membership


def assign_permissions(
    db_session: Session,
    *,
    tenant: Tenant,
    membership: Membership,
    permission_codes: list[PermissionCode],
) -> None:
    role = Role(
        tenant_id=tenant.id,
        name=f"Test Role {uuid4()}",
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


def api_client_factory(
    db_session: Session,
    permissions: list[PermissionCode] | None = None,
):
    tenant = create_tenant(db_session)
    user = create_user(db_session)
    membership = create_membership(
        db_session,
        user=user,
        tenant=tenant,
    )

    assign_permissions(
        db_session,
        tenant=tenant,
        membership=membership,
        permission_codes=permissions or [],
    )

    def override_auth_context():
        return AuthContext(user=user, tenant_id=tenant.id)

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


def create_product_payload(**overrides):
    payload = {
        "name": f"Product {uuid4().hex[:8]}",
        "description": "Test product description",
        "type": "product",
        "unit": "unit",
        "sku": f"SKU-{uuid4().hex[:8].upper()}",
        "sale_price": "25.90",
        "cost_price": "12.50",
    }
    payload.update(overrides)
    return payload


def create_persisted_category(
    db_session: Session,
    tenant: Tenant,
) -> ProductCategory:
    category = ProductCategory(
        tenant_id=tenant.id,
        name=f"Category {uuid4().hex[:8]}",
        is_active=True,
    )
    db_session.add(category)
    db_session.flush()
    return category


def create_persisted_product(
    db_session: Session,
    tenant: Tenant,
    **overrides,
) -> Product:
    data = {
        "tenant_id": tenant.id,
        "name": f"Product {uuid4().hex[:8]}",
        "description": "Existing product",
        "type": "product",
        "unit": "unit",
        "sku": f"SKU-{uuid4().hex[:8].upper()}",
        "sale_price": 25.90,
        "cost_price": 12.50,
        "is_active": True,
    }
    data.update(overrides)

    product = Product(**data)
    db_session.add(product)
    db_session.flush()
    return product


@pytest.fixture
def api_client(db_session):
    client, tenant, user = api_client_factory(
        db_session,
        permissions=[
            PermissionCode.PRODUCTS_READ,
            PermissionCode.PRODUCTS_CREATE,
            PermissionCode.PRODUCTS_UPDATE,
            PermissionCode.PRODUCTS_DELETE,
        ],
    )

    try:
        yield client, tenant, user
    finally:
        app.dependency_overrides.clear()


def test_create_product_returns_201(api_client):
    client, tenant, _ = api_client

    with client:
        response = client.post(
            "/api/v1/products/",
            json=create_product_payload(name="Água mineral"),
        )

    assert response.status_code == 201
    assert response.json()["name"] == "Água mineral"
    assert response.json()["tenant_id"] == str(tenant.id)
    assert response.json()["type"] == "product"
    assert response.json()["is_active"] is True


def test_create_service_returns_201(api_client):
    client, _, _ = api_client

    with client:
        response = client.post(
            "/api/v1/products/",
            json=create_product_payload(
                name="Garçom por hora",
                type="service",
                unit="hour",
            ),
        )

    assert response.status_code == 201
    assert response.json()["type"] == "service"
    assert response.json()["unit"] == "hour"


def test_create_product_with_category_returns_201(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    category = create_persisted_category(db_session, tenant)

    with client:
        response = client.post(
            "/api/v1/products/",
            json=create_product_payload(
                category_id=str(category.id),
            ),
        )

    assert response.status_code == 201
    assert response.json()["category_id"] == str(category.id)


def test_create_product_with_duplicate_sku_returns_409(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    create_persisted_product(
        db_session,
        tenant,
        sku="SKU-DUPLICATE",
    )

    with client:
        response = client.post(
            "/api/v1/products/",
            json=create_product_payload(sku="SKU-DUPLICATE"),
        )

    assert response.status_code == 409


def test_create_product_with_invalid_category_returns_422(api_client):
    client, _, _ = api_client

    with client:
        response = client.post(
            "/api/v1/products/",
            json=create_product_payload(category_id=str(uuid4())),
        )

    assert response.status_code == 422


def test_create_product_without_permission_returns_403(db_session):
    client, _, _ = api_client_factory(db_session, permissions=[])

    try:
        with client:
            response = client.post(
                "/api/v1/products/",
                json=create_product_payload(),
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_list_products_returns_200_and_pagination(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    create_persisted_product(db_session, tenant, name="Água mineral")
    create_persisted_product(db_session, tenant, name="Refrigerante")

    with client:
        response = client.get(
            "/api/v1/products/",
            params={"offset": 0, "limit": 1},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 1
    assert response.json()["offset"] == 0
    assert response.json()["limit"] == 1


def test_list_products_filters_by_search(db_session, api_client):
    client, tenant, _ = api_client
    create_persisted_product(db_session, tenant, name="Água mineral")
    create_persisted_product(db_session, tenant, name="Refrigerante")

    with client:
        response = client.get(
            "/api/v1/products/",
            params={"search": "Água"},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["name"] == "Água mineral"


def test_list_products_filters_by_type(db_session, api_client):
    client, tenant, _ = api_client
    create_persisted_product(
        db_session,
        tenant,
        name="Água mineral",
        type="product",
    )
    create_persisted_product(
        db_session,
        tenant,
        name="Serviço de buffet",
        type="service",
    )

    with client:
        response = client.get(
            "/api/v1/products/",
            params={"type": "service"},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["type"] == "service"


def test_list_products_filters_by_category(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    category = create_persisted_category(db_session, tenant)
    create_persisted_product(
        db_session,
        tenant,
        name="Produto categorizado",
        category_id=category.id,
    )
    create_persisted_product(
        db_session,
        tenant,
        name="Produto sem categoria",
    )

    with client:
        response = client.get(
            "/api/v1/products/",
            params={"category_id": str(category.id)},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["category_id"] == str(category.id)


def test_list_products_excludes_archived_products(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    create_persisted_product(
        db_session,
        tenant,
        name="Active product",
    )
    create_persisted_product(
        db_session,
        tenant,
        name="Archived product",
        is_active=False,
    )

    with client:
        response = client.get("/api/v1/products/")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["name"] == "Active product"


def test_list_products_without_permission_returns_403(db_session):
    client, _, _ = api_client_factory(db_session, permissions=[])

    try:
        with client:
            response = client.get("/api/v1/products/")

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_get_product_returns_200(db_session, api_client):
    client, tenant, _ = api_client
    product = create_persisted_product(
        db_session,
        tenant,
        name="Água mineral",
    )

    with client:
        response = client.get(f"/api/v1/products/{product.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(product.id)
    assert response.json()["name"] == "Água mineral"


def test_get_product_not_found_returns_404(api_client):
    client, _, _ = api_client

    with client:
        response = client.get(f"/api/v1/products/{uuid4()}")

    assert response.status_code == 404


def test_get_product_from_another_tenant_returns_404(
    db_session,
    api_client,
):
    client, _, _ = api_client
    other_tenant = create_tenant(db_session, name="Other Tenant")
    product = create_persisted_product(
        db_session,
        other_tenant,
        name="Private product",
    )

    with client:
        response = client.get(f"/api/v1/products/{product.id}")

    assert response.status_code == 404


def test_update_product_returns_200(db_session, api_client):
    client, tenant, _ = api_client
    product = create_persisted_product(
        db_session,
        tenant,
        name="Original product",
    )

    with client:
        response = client.patch(
            f"/api/v1/products/{product.id}",
            json={"name": "Updated product", "sale_price": "30.00"},
        )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated product"
    assert response.json()["sale_price"] == "30.00"


def test_update_product_duplicate_sku_returns_409(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    product = create_persisted_product(
        db_session,
        tenant,
        sku="SKU-FIRST",
    )
    create_persisted_product(
        db_session,
        tenant,
        sku="SKU-SECOND",
    )

    with client:
        response = client.patch(
            f"/api/v1/products/{product.id}",
            json={"sku": "SKU-SECOND"},
        )

    assert response.status_code == 409


def test_update_product_not_found_returns_404(api_client):
    client, _, _ = api_client

    with client:
        response = client.patch(
            f"/api/v1/products/{uuid4()}",
            json={"name": "Updated"},
        )

    assert response.status_code == 404


def test_update_archived_product_returns_404(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    product = create_persisted_product(
        db_session,
        tenant,
        is_active=False,
    )

    with client:
        response = client.patch(
            f"/api/v1/products/{product.id}",
            json={"name": "Updated"},
        )

    assert response.status_code == 404


def test_update_product_without_permission_returns_403(
    db_session,
):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.PRODUCTS_READ],
    )
    product = create_persisted_product(db_session, tenant)

    try:
        with client:
            response = client.patch(
                f"/api/v1/products/{product.id}",
                json={"name": "Updated"},
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_archive_product_returns_200(db_session, api_client):
    client, tenant, _ = api_client
    product = create_persisted_product(
        db_session,
        tenant,
        name="Product to archive",
    )

    with client:
        response = client.post(
            f"/api/v1/products/{product.id}/archive"
        )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_archive_product_not_found_returns_404(api_client):
    client, _, _ = api_client

    with client:
        response = client.post(
            f"/api/v1/products/{uuid4()}/archive"
        )

    assert response.status_code == 404


def test_archive_product_without_permission_returns_403(
    db_session,
):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.PRODUCTS_READ],
    )
    product = create_persisted_product(db_session, tenant)

    try:
        with client:
            response = client.post(
                f"/api/v1/products/{product.id}/archive"
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_products_without_authentication_return_401(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/products/")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()
