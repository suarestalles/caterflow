
from collections.abc import Generator

import pytest
from fastapi import HTTPException
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
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant
from app.models.user import User


def create_tenant(db_session: Session, name: str) -> Tenant:
    tenant = Tenant(name=name)
    db_session.add(tenant)
    db_session.flush()
    return tenant


def create_user(
    db_session: Session,
    email: str = "client-api@example.com",
) -> User:
    user = User(
        full_name="Client API Test User",
        email=email,
        password_hash="test-password-hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_membership(
    db_session: Session,
    user: User,
    tenant: Tenant,
) -> Membership:
    membership = Membership(
        user_id=user.id,
        tenant_id=tenant.id,
    )
    db_session.add(membership)
    db_session.flush()
    return membership


def assign_permissions(
    db_session: Session,
    membership: Membership,
    tenant: Tenant,
    permission_codes: list[PermissionCode],
) -> None:
    role = Role(
        tenant_id=tenant.id,
        name="Client API Test Role",
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
                description=f"Test permission: {code}",
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


@pytest.fixture
def api_client_factory(
    db_session: Session,
) -> Generator:
    def create(
        permission_codes: list[PermissionCode] | None = None,
    ) -> tuple[TestClient, Tenant, User]:
        tenant = create_tenant(
            db_session,
            "Client API Test Tenant",
        )
        user = create_user(db_session)
        membership = create_membership(
            db_session,
            user,
            tenant,
        )

        assign_permissions(
            db_session,
            membership,
            tenant,
            permission_codes or [],
        )

        def override_auth_context() -> AuthContext:
            return AuthContext(
                user=user,
                tenant_id=tenant.id,
            )

        def override_tenant_db() -> Generator:
            tenant_db = TenantSession(
                bind=db_session.connection(),
                join_transaction_mode="create_savepoint",
                tenant_id=tenant.id,
            )

            try:
                yield tenant_db
            finally:
                tenant_db.close()

        app.dependency_overrides[get_auth_context] = (
            override_auth_context
        )
        app.dependency_overrides[get_current_tenant_db] = (
            override_tenant_db
        )

        return TestClient(app), tenant, user

    yield create

    app.dependency_overrides.clear()


def create_client_payload(**overrides) -> dict:
    payload = {
        "client_type": "individual",
        "name": "Maria Silva",
        "email": "maria@example.com",
        "phone": None,
        "country": "ES",
    }
    payload.update(overrides)
    return payload


def create_persisted_client(
    db_session: Session,
    tenant_id,
    **overrides,
) -> Client:
    client = Client(
        tenant_id=tenant_id,
        **create_client_payload(**overrides),
    )
    db_session.add(client)
    db_session.flush()
    return client


# ============================================================
# AUTHENTICATION
# ============================================================


def test_clients_api_requires_authentication(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/clients/")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


# ============================================================
# CREATE CLIENT
# ============================================================


def test_create_client_api(api_client_factory):
    client, tenant, _ = api_client_factory(
        [PermissionCode.CLIENTS_CREATE]
    )

    with client:
        response = client.post(
            "/api/v1/clients/",
            json=create_client_payload(),
        )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["tenant_id"] == str(tenant.id)
    assert data["name"] == "Maria Silva"
    assert data["email"] == "maria@example.com"
    assert data["client_type"] == "individual"


def test_create_company_client_api(api_client_factory):
    client, tenant, _ = api_client_factory(
        [PermissionCode.CLIENTS_CREATE]
    )

    with client:
        response = client.post(
            "/api/v1/clients/",
            json=create_client_payload(
                client_type="company",
                name="Empresa Exemplo SL",
                contact_person="João Silva",
                email=None,
                phone="+34600123456",
            ),
        )

    assert response.status_code == 201

    data = response.json()

    assert data["client_type"] == "company"
    assert data["name"] == "Empresa Exemplo SL"
    assert data["contact_person"] == "João Silva"
    assert data["phone"] == "+34600123456"


def test_create_client_api_without_contact_returns_422(
    api_client_factory,
):
    client, _, _ = api_client_factory(
        [PermissionCode.CLIENTS_CREATE]
    )

    with client:
        response = client.post(
            "/api/v1/clients/",
            json=create_client_payload(
                email=None,
                phone=None,
            ),
        )

    assert response.status_code == 422


def test_create_client_api_without_permission_returns_403(
    api_client_factory,
):
    client, _, _ = api_client_factory([])

    with client:
        response = client.post(
            "/api/v1/clients/",
            json=create_client_payload(),
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions."


# ============================================================
# LIST CLIENTS
# ============================================================


def test_list_clients_api(api_client_factory, db_session):
    client, tenant, _ = api_client_factory(
        [PermissionCode.CLIENTS_READ]
    )

    create_persisted_client(
        db_session,
        tenant.id,
        name="Maria Silva",
    )
    create_persisted_client(
        db_session,
        tenant.id,
        name="João Santos",
        email="joao@example.com",
    )

    with client:
        response = client.get("/api/v1/clients/")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["offset"] == 0
    assert data["limit"] == 20


def test_list_clients_api_with_search(api_client_factory, db_session):
    client, tenant, _ = api_client_factory(
        [PermissionCode.CLIENTS_READ]
    )

    create_persisted_client(
        db_session,
        tenant.id,
        name="Maria Silva",
    )
    create_persisted_client(
        db_session,
        tenant.id,
        name="João Santos",
        email="joao@example.com",
    )

    with client:
        response = client.get(
            "/api/v1/clients/",
            params={"search": "Maria"},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "Maria Silva"


def test_list_clients_api_validates_pagination(api_client_factory):
    client, _, _ = api_client_factory(
        [PermissionCode.CLIENTS_READ]
    )

    with client:
        response = client.get(
            "/api/v1/clients/",
            params={"limit": 0},
        )

    assert response.status_code == 422


def test_list_clients_api_without_permission_returns_403(
    api_client_factory,
):
    client, _, _ = api_client_factory([])

    with client:
        response = client.get("/api/v1/clients/")

    assert response.status_code == 403


# ============================================================
# GET CLIENT
# ============================================================


def test_get_client_api(api_client_factory, db_session):
    client, tenant, _ = api_client_factory(
        [PermissionCode.CLIENTS_READ]
    )

    persisted_client = create_persisted_client(
        db_session,
        tenant.id,
    )

    with client:
        response = client.get(
            f"/api/v1/clients/{persisted_client.id}"
        )

    assert response.status_code == 200
    assert response.json()["id"] == str(persisted_client.id)
    assert response.json()["name"] == "Maria Silva"


def test_get_nonexistent_client_api_returns_404(api_client_factory):
    client, _, _ = api_client_factory(
        [PermissionCode.CLIENTS_READ]
    )

    with client:
        response = client.get(
            "/api/v1/clients/00000000-0000-0000-0000-000000000001"
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found."


def test_get_client_from_another_tenant_api_returns_404(
    api_client_factory,
    db_session,
):
    client, _, _ = api_client_factory(
        [PermissionCode.CLIENTS_READ]
    )

    other_tenant = create_tenant(
        db_session,
        "Another API Tenant",
    )

    other_client = create_persisted_client(
        db_session,
        other_tenant.id,
        name="Private Client",
    )

    with client:
        response = client.get(
            f"/api/v1/clients/{other_client.id}"
        )

    assert response.status_code == 404


# ============================================================
# UPDATE CLIENT
# ============================================================


def test_update_client_api(api_client_factory, db_session):
    client, tenant, _ = api_client_factory(
        [PermissionCode.CLIENTS_UPDATE]
    )

    persisted_client = create_persisted_client(
        db_session,
        tenant.id,
    )

    with client:
        response = client.patch(
            f"/api/v1/clients/{persisted_client.id}",
            json={
                "name": "Maria Santos",
                "phone": "+34600123456",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Maria Santos"
    assert data["email"] == "maria@example.com"
    assert data["phone"] == "+34600123456"


def test_update_client_api_without_contact_returns_422(
    api_client_factory,
    db_session,
):
    client, tenant, _ = api_client_factory(
        [PermissionCode.CLIENTS_UPDATE]
    )

    persisted_client = create_persisted_client(
        db_session,
        tenant.id,
    )

    with client:
        response = client.patch(
            f"/api/v1/clients/{persisted_client.id}",
            json={
                "email": None,
                "phone": None,
            },
        )

    assert response.status_code == 422


def test_update_client_api_without_permission_returns_403(
    api_client_factory,
    db_session,
):
    client, tenant, _ = api_client_factory([])

    persisted_client = create_persisted_client(
        db_session,
        tenant.id,
    )

    with client:
        response = client.patch(
            f"/api/v1/clients/{persisted_client.id}",
            json={"name": "Unauthorized Update"},
        )

    assert response.status_code == 403


def test_update_nonexistent_client_api_returns_404(
    api_client_factory,
):
    client, _, _ = api_client_factory(
        [PermissionCode.CLIENTS_UPDATE]
    )

    with client:
        response = client.patch(
            "/api/v1/clients/00000000-0000-0000-0000-000000000001",
            json={"name": "Updated"},
        )

    assert response.status_code == 404


# ============================================================
# ARCHIVE CLIENT
# ============================================================


def test_archive_client_api(api_client_factory, db_session):
    client, tenant, _ = api_client_factory(
        [PermissionCode.CLIENTS_ARCHIVE]
    )

    persisted_client = create_persisted_client(
        db_session,
        tenant.id,
    )

    with client:
        response = client.delete(
            f"/api/v1/clients/{persisted_client.id}"
        )

    assert response.status_code == 204
    assert response.content == b""


def test_archive_client_api_without_permission_returns_403(
    api_client_factory,
    db_session,
):
    client, tenant, _ = api_client_factory([])

    persisted_client = create_persisted_client(
        db_session,
        tenant.id,
    )

    with client:
        response = client.delete(
            f"/api/v1/clients/{persisted_client.id}"
        )

    assert response.status_code == 403


def test_archive_nonexistent_client_api_returns_404(
    api_client_factory,
):
    client, _, _ = api_client_factory(
        [PermissionCode.CLIENTS_ARCHIVE]
    )

    with client:
        response = client.delete(
            "/api/v1/clients/00000000-0000-0000-0000-000000000001"
        )

    assert response.status_code == 404


def test_archived_client_is_not_available_through_api(
    api_client_factory,
    db_session,
):
    client, tenant, _ = api_client_factory(
        [
            PermissionCode.CLIENTS_READ,
            PermissionCode.CLIENTS_ARCHIVE,
        ]
    )

    persisted_client = create_persisted_client(
        db_session,
        tenant.id,
    )

    with client:
        archive_response = client.delete(
            f"/api/v1/clients/{persisted_client.id}"
        )

        get_response = client.get(
            f"/api/v1/clients/{persisted_client.id}"
        )

    assert archive_response.status_code == 204
    assert get_response.status_code == 404
