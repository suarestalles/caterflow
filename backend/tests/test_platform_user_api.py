
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.api.v1.deps import (
    PlatformAdminContext,
    get_current_platform_admin,
)
from app.db.session import get_db
from app.main import app
from app.models.platform_admin import PlatformAdmin


@pytest.fixture
def platform_api_client_factory(db_session, user_factory):
    def create():
        admin = user_factory(
            full_name="Platform Admin",
            email="platform-admin@example.com",
        )

        platform_admin = PlatformAdmin(user_id=admin.id)
        db_session.add(platform_admin)
        db_session.flush()

        def override_db() -> Generator:
            yield db_session

        def override_platform_admin() -> PlatformAdminContext:
            return PlatformAdminContext(
                user=admin,
                platform_admin=platform_admin,
            )

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[
            get_current_platform_admin
        ] = override_platform_admin

        return TestClient(app), admin

    yield create
    app.dependency_overrides.clear()


def test_platform_users_api_requires_authentication(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/platform-users/")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_create_user_api_with_multiple_tenants(
    platform_api_client_factory,
    tenant_factory,
):
    client, _ = platform_api_client_factory()

    tenant_a = tenant_factory(name="Company A")
    tenant_b = tenant_factory(name="Company B")

    with client:
        response = client.post(
            "/api/v1/platform-users/",
            json={
                "full_name": "Multi Tenant User",
                "email": "multi@example.com",
                "password": "StrongPassword123!",
                "is_platform_admin": False,
                "tenant_ids": [
                    str(tenant_a.id),
                    str(tenant_b.id),
                ],
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Multi Tenant User"
    assert data["email"] == "multi@example.com"
    assert data["is_platform_admin"] is False
    assert {tenant["id"] for tenant in data["tenants"]} == {
        str(tenant_a.id),
        str(tenant_b.id),
    }


def test_create_platform_admin_without_tenant_api(
    platform_api_client_factory,
):
    client, _ = platform_api_client_factory()

    with client:
        response = client.post(
            "/api/v1/platform-users/",
            json={
                "full_name": "Platform Only",
                "email": "platform-only@example.com",
                "password": "StrongPassword123!",
                "is_platform_admin": True,
                "tenant_ids": [],
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["is_platform_admin"] is True
    assert data["tenants"] == []


def test_create_user_api_rejects_user_without_access(
    platform_api_client_factory,
):
    client, _ = platform_api_client_factory()

    with client:
        response = client.post(
            "/api/v1/platform-users/",
            json={
                "full_name": "No Access",
                "email": "no-access@example.com",
                "password": "StrongPassword123!",
                "is_platform_admin": False,
                "tenant_ids": [],
            },
        )

    assert response.status_code == 422


def test_create_user_api_rejects_duplicate_email(
    platform_api_client_factory,
    user_factory,
    tenant_factory,
):
    client, _ = platform_api_client_factory()

    user_factory(email="existing@example.com")
    tenant = tenant_factory()

    with client:
        response = client.post(
            "/api/v1/platform-users/",
            json={
                "full_name": "Duplicate User",
                "email": "existing@example.com",
                "password": "StrongPassword123!",
                "is_platform_admin": False,
                "tenant_ids": [str(tenant.id)],
            },
        )

    assert response.status_code == 409


def test_update_user_api_replaces_tenant_memberships(
    platform_api_client_factory,
    tenant_factory,
):
    client, _ = platform_api_client_factory()

    tenant_a = tenant_factory(name="Company A")
    tenant_b = tenant_factory(name="Company B")

    with client:
        create_response = client.post(
            "/api/v1/platform-users/",
            json={
                "full_name": "Tenant User",
                "email": "tenant-user@example.com",
                "password": "StrongPassword123!",
                "is_platform_admin": False,
                "tenant_ids": [str(tenant_a.id)],
            },
        )

        user_id = create_response.json()["id"]

        update_response = client.patch(
            f"/api/v1/platform-users/{user_id}",
            json={
                "tenant_ids": [str(tenant_b.id)],
            },
        )

    assert create_response.status_code == 201
    assert update_response.status_code == 200

    data = update_response.json()

    assert {tenant["id"] for tenant in data["tenants"]} == {
        str(tenant_b.id),
    }


def test_update_user_api_can_enable_platform_admin(
    platform_api_client_factory,
    tenant_factory,
):
    client, _ = platform_api_client_factory()
    tenant = tenant_factory()

    with client:
        create_response = client.post(
            "/api/v1/platform-users/",
            json={
                "full_name": "Tenant User",
                "email": "tenant-user@example.com",
                "password": "StrongPassword123!",
                "is_platform_admin": False,
                "tenant_ids": [str(tenant.id)],
            },
        )

        user_id = create_response.json()["id"]

        update_response = client.patch(
            f"/api/v1/platform-users/{user_id}",
            json={"is_platform_admin": True},
        )

    assert update_response.status_code == 200
    assert update_response.json()["is_platform_admin"] is True


def test_update_user_api_rejects_removing_all_access(
    platform_api_client_factory,
    tenant_factory,
):
    client, _ = platform_api_client_factory()
    tenant = tenant_factory()

    with client:
        create_response = client.post(
            "/api/v1/platform-users/",
            json={
                "full_name": "Tenant User",
                "email": "tenant-user@example.com",
                "password": "StrongPassword123!",
                "is_platform_admin": False,
                "tenant_ids": [str(tenant.id)],
            },
        )

        user_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/platform-users/{user_id}",
            json={
                "is_platform_admin": False,
                "tenant_ids": [],
            },
        )

    assert response.status_code == 422


def test_list_users_api_returns_tenant_details(
    platform_api_client_factory,
    tenant_factory,
):
    client, _ = platform_api_client_factory()
    tenant = tenant_factory()

    with client:
        client.post(
            "/api/v1/platform-users/",
            json={
                "full_name": "Listed User",
                "email": "listed@example.com",
                "password": "StrongPassword123!",
                "is_platform_admin": False,
                "tenant_ids": [str(tenant.id)],
            },
        )

        response = client.get(
            "/api/v1/platform-users/",
            params={"search": "listed@example.com"},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["email"] == "listed@example.com"
    assert data["items"][0]["tenants"][0]["id"] == str(tenant.id)
