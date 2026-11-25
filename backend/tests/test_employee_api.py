
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
from app.db.tenant_session import TenantSession
from app.main import app
from app.models.employee import Employee
from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant
from app.models.user import User


def create_tenant(db_session: Session, name="Workforce Test Tenant"):
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


def create_employee_payload(**overrides):
    payload = {
        "name": "Maria Silva",
        "employment_type": "employee",
        "position": "Waiter",
        "email": "maria@example.com",
        "phone": "+34600123456",
        "notes": "Experienced waiter",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def api_client(db_session):
    client, tenant, user = api_client_factory(
        db_session,
        permissions=[
            PermissionCode.STAFF_READ,
            PermissionCode.STAFF_CREATE,
            PermissionCode.STAFF_UPDATE,
            PermissionCode.STAFF_ARCHIVE,
        ],
    )

    try:
        yield client, tenant, user
    finally:
        app.dependency_overrides.clear()


def test_create_employee_returns_201(api_client):
    client, tenant, _ = api_client

    with client:
        response = client.post(
            "/api/v1/employees/",
            json=create_employee_payload(),
        )

    assert response.status_code == 201
    body = response.json()

    assert body["name"] == "Maria Silva"
    assert body["employment_type"] == "employee"
    assert body["tenant_id"] == str(tenant.id)


def test_create_freelancer_returns_201(api_client):
    client, _, _ = api_client

    with client:
        response = client.post(
            "/api/v1/employees/",
            json=create_employee_payload(
                employment_type="freelancer",
            ),
        )

    assert response.status_code == 201
    assert response.json()["employment_type"] == "freelancer"


def test_create_employee_with_invalid_data_returns_422(api_client):
    client, _, _ = api_client

    with client:
        response = client.post(
            "/api/v1/employees/",
            json=create_employee_payload(name=""),
        )

    assert response.status_code == 422


def test_create_employee_without_permission_returns_403(db_session):
    client, _, _ = api_client_factory(db_session, permissions=[])

    try:
        with client:
            response = client.post(
                "/api/v1/employees/",
                json=create_employee_payload(),
            )

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions."
    finally:
        app.dependency_overrides.clear()


def test_list_employees_returns_200_and_pagination(
    db_session,
    api_client,
):
    client, _, _ = api_client

    with client:
        client.post(
            "/api/v1/employees/",
            json=create_employee_payload(),
        )
        response = client.get(
            "/api/v1/employees/",
            params={"offset": 0, "limit": 10},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["offset"] == 0
    assert response.json()["limit"] == 10


def test_list_employees_filters_by_search(api_client):
    client, _, _ = api_client

    with client:
        client.post(
            "/api/v1/employees/",
            json=create_employee_payload(),
        )
        response = client.get(
            "/api/v1/employees/",
            params={"search": "Maria"},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["name"] == "Maria Silva"


def test_get_employee_returns_200(api_client):
    client, _, _ = api_client

    with client:
        created = client.post(
            "/api/v1/employees/",
            json=create_employee_payload(),
        )
        employee_id = created.json()["id"]

        response = client.get(
            f"/api/v1/employees/{employee_id}",
        )

    assert response.status_code == 200
    assert response.json()["id"] == employee_id


def test_get_nonexistent_employee_returns_404(api_client):
    client, _, _ = api_client

    with client:
        response = client.get(
            f"/api/v1/employees/{uuid4()}",
        )

    assert response.status_code == 404


def test_update_employee_returns_200(api_client):
    client, _, _ = api_client

    with client:
        created = client.post(
            "/api/v1/employees/",
            json=create_employee_payload(),
        )
        employee_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/employees/{employee_id}",
            json={"position": "Head Waiter"},
        )

    assert response.status_code == 200
    assert response.json()["position"] == "Head Waiter"


def test_update_employee_without_permission_returns_403(db_session):
    client, _, _ = api_client_factory(
        db_session,
        permissions=[
            PermissionCode.STAFF_CREATE,
            PermissionCode.STAFF_READ,
        ],
    )

    try:
        with client:
            created = client.post(
                "/api/v1/employees/",
                json=create_employee_payload(),
            )
            employee_id = created.json()["id"]

            response = client.patch(
                f"/api/v1/employees/{employee_id}",
                json={"position": "Manager"},
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_archive_employee_returns_204_and_get_returns_404(api_client):
    client, _, _ = api_client

    with client:
        created = client.post(
            "/api/v1/employees/",
            json=create_employee_payload(),
        )
        employee_id = created.json()["id"]

        archived = client.delete(
            f"/api/v1/employees/{employee_id}",
        )
        retrieved = client.get(
            f"/api/v1/employees/{employee_id}",
        )

    assert archived.status_code == 204
    assert retrieved.status_code == 404


def test_employee_from_another_tenant_returns_404(
    db_session,
    api_client,
):
    client, tenant, _ = api_client

    other_tenant = create_tenant(
        db_session,
        name="Another Workforce Tenant",
    )
    employee = Employee(
        tenant_id=other_tenant.id,
        name="Other Employee",
        employment_type="employee",
        position="Waiter",
    )
    db_session.add(employee)
    db_session.flush()

    with client:
        response = client.get(
            f"/api/v1/employees/{employee.id}",
        )

    assert response.status_code == 404
    assert employee.tenant_id != tenant.id
