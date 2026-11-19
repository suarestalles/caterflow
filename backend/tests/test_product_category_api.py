
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
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


def create_category_payload(**overrides):
    payload = {
        "name": f"Category {uuid4().hex[:8]}",
        "description": "Test category description",
    }
    payload.update(overrides)
    return payload


def create_persisted_category(
    db_session: Session,
    tenant: Tenant,
    **overrides,
) -> ProductCategory:
    data = {
        "tenant_id": tenant.id,
        "name": f"Category {uuid4().hex[:8]}",
        "description": "Existing category",
        "is_active": True,
    }
    data.update(overrides)

    category = ProductCategory(**data)
    db_session.add(category)
    db_session.flush()
    return category


@pytest.fixture
def api_client(db_session):
    client, tenant, user = api_client_factory(
        db_session,
        permissions=[
            PermissionCode.PRODUCT_CATEGORIES_READ,
            PermissionCode.PRODUCT_CATEGORIES_CREATE,
            PermissionCode.PRODUCT_CATEGORIES_UPDATE,
            PermissionCode.PRODUCT_CATEGORIES_DELETE,
        ],
    )

    try:
        yield client, tenant, user
    finally:
        app.dependency_overrides.clear()


def test_create_category_returns_201(api_client):
    client, tenant, _ = api_client

    with client:
        response = client.post(
            "/api/v1/product-categories/",
            json=create_category_payload(name="Bebidas"),
        )

    assert response.status_code == 201
    assert response.json()["name"] == "Bebidas"
    assert response.json()["tenant_id"] == str(tenant.id)
    assert response.json()["is_active"] is True


def test_create_category_with_parent_returns_201(db_session, api_client):
    client, tenant, _ = api_client
    parent = create_persisted_category(
        db_session,
        tenant,
        name="Alimentos",
    )

    with client:
        response = client.post(
            "/api/v1/product-categories/",
            json=create_category_payload(
                name="Massas",
                parent_id=str(parent.id),
            ),
        )

    assert response.status_code == 201
    assert response.json()["parent_id"] == str(parent.id)


def test_create_category_with_duplicate_name_returns_409(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    create_persisted_category(db_session, tenant, name="Bebidas")

    with client:
        response = client.post(
            "/api/v1/product-categories/",
            json=create_category_payload(name="Bebidas"),
        )

    assert response.status_code == 409


def test_create_category_without_permission_returns_403(db_session):
    client, _, _ = api_client_factory(db_session, permissions=[])

    try:
        with client:
            response = client.post(
                "/api/v1/product-categories/",
                json=create_category_payload(),
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_list_categories_returns_200_and_pagination(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    create_persisted_category(db_session, tenant, name="Bebidas")
    create_persisted_category(db_session, tenant, name="Sobremesas")

    with client:
        response = client.get(
            "/api/v1/product-categories/",
            params={"offset": 0, "limit": 1},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 1
    assert response.json()["offset"] == 0
    assert response.json()["limit"] == 1


def test_list_categories_filters_by_search(db_session, api_client):
    client, tenant, _ = api_client
    create_persisted_category(db_session, tenant, name="Bebidas")
    create_persisted_category(db_session, tenant, name="Sobremesas")

    with client:
        response = client.get(
            "/api/v1/product-categories/",
            params={"search": "Bebidas"},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["name"] == "Bebidas"


def test_list_categories_without_permission_returns_403(db_session):
    client, _, _ = api_client_factory(db_session, permissions=[])

    try:
        with client:
            response = client.get("/api/v1/product-categories/")

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_get_category_returns_200(db_session, api_client):
    client, tenant, _ = api_client
    category = create_persisted_category(
        db_session,
        tenant,
        name="Bebidas",
    )

    with client:
        response = client.get(
            f"/api/v1/product-categories/{category.id}"
        )

    assert response.status_code == 200
    assert response.json()["id"] == str(category.id)
    assert response.json()["name"] == "Bebidas"


def test_get_category_not_found_returns_404(api_client):
    client, _, _ = api_client

    with client:
        response = client.get(
            f"/api/v1/product-categories/{uuid4()}"
        )

    assert response.status_code == 404


def test_get_category_from_another_tenant_returns_404(
    db_session,
    api_client,
):
    client, _, _ = api_client
    other_tenant = create_tenant(db_session, name="Other Tenant")
    category = create_persisted_category(
        db_session,
        other_tenant,
        name="Private Category",
    )

    with client:
        response = client.get(
            f"/api/v1/product-categories/{category.id}"
        )

    assert response.status_code == 404


def test_update_category_returns_200(db_session, api_client):
    client, tenant, _ = api_client
    category = create_persisted_category(
        db_session,
        tenant,
        name="Bebidas",
    )

    with client:
        response = client.patch(
            f"/api/v1/product-categories/{category.id}",
            json={"name": "Bebidas não alcoólicas"},
        )

    assert response.status_code == 200
    assert response.json()["name"] == "Bebidas não alcoólicas"


def test_update_category_duplicate_name_returns_409(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    category = create_persisted_category(
        db_session,
        tenant,
        name="Bebidas",
    )
    create_persisted_category(
        db_session,
        tenant,
        name="Sobremesas",
    )

    with client:
        response = client.patch(
            f"/api/v1/product-categories/{category.id}",
            json={"name": "Sobremesas"},
        )

    assert response.status_code == 409


def test_update_category_not_found_returns_404(api_client):
    client, _, _ = api_client

    with client:
        response = client.patch(
            f"/api/v1/product-categories/{uuid4()}",
            json={"name": "Updated"},
        )

    assert response.status_code == 404


def test_update_category_without_permission_returns_403(
    db_session,
):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.PRODUCT_CATEGORIES_READ],
    )
    category = create_persisted_category(
        db_session,
        tenant,
        name="Bebidas",
    )

    try:
        with client:
            response = client.patch(
                f"/api/v1/product-categories/{category.id}",
                json={"name": "Updated"},
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_archive_category_returns_200(db_session, api_client):
    client, tenant, _ = api_client
    category = create_persisted_category(
        db_session,
        tenant,
        name="Bebidas",
    )

    with client:
        response = client.post(
            f"/api/v1/product-categories/{category.id}/archive"
        )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_archive_category_in_use_returns_422(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    category = create_persisted_category(
        db_session,
        tenant,
        name="Bebidas",
    )
    product = Product(
        tenant_id=tenant.id,
        category_id=category.id,
        name="Água mineral",
        type="product",
        unit="unit",
        sale_price=2.50,
        cost_price=1.00,
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()

    with client:
        response = client.post(
            f"/api/v1/product-categories/{category.id}/archive"
        )

    assert response.status_code == 422


def test_archive_category_with_children_returns_422(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    parent = create_persisted_category(
        db_session,
        tenant,
        name="Alimentos",
    )
    create_persisted_category(
        db_session,
        tenant,
        name="Massas",
        parent_id=parent.id,
    )

    with client:
        response = client.post(
            f"/api/v1/product-categories/{parent.id}/archive"
        )

    assert response.status_code == 422


def test_archive_category_not_found_returns_404(api_client):
    client, _, _ = api_client

    with client:
        response = client.post(
            f"/api/v1/product-categories/{uuid4()}/archive"
        )

    assert response.status_code == 404


def test_archive_category_without_permission_returns_403(
    db_session,
):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.PRODUCT_CATEGORIES_READ],
    )
    category = create_persisted_category(
        db_session,
        tenant,
        name="Bebidas",
    )

    try:
        with client:
            response = client.post(
                f"/api/v1/product-categories/{category.id}/archive"
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_categories_without_authentication_return_401(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/product-categories/")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()
