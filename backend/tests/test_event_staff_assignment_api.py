
from datetime import UTC, datetime
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
from app.db.tenant_session import TenantSession
from app.main import app
from app.models.client import Client
from app.models.employee import Employee
from app.models.event import Event
from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant
from app.models.user import User


def create_tenant(db_session: Session, name="Workforce Assignment Test Tenant"):
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


def create_client_for_tenant(db_session, tenant):
    client = Client(
        tenant_id=tenant.id,
        name="Test Client",
        email=f"{uuid4()}@example.com",
    )
    db_session.add(client)
    db_session.flush()
    return client


def create_event_for_tenant(db_session, tenant):
    client = create_client_for_tenant(db_session, tenant)

    event = Event(
        tenant_id=tenant.id,
        client_id=client.id,
        name="Corporate Event",
        starts_at=datetime(2026, 12, 15, 18, tzinfo=UTC),
        ends_at=datetime(2026, 12, 15, 23, tzinfo=UTC),
        guest_count=100,
        status="draft",
        country="ES",
    )
    db_session.add(event)
    db_session.flush()
    return event


def create_employee_for_tenant(db_session, tenant):
    employee = Employee(
        tenant_id=tenant.id,
        name="Maria Silva",
        employment_type="employee",
        position="Waiter",
        email=f"{uuid4()}@example.com",
    )
    db_session.add(employee)
    db_session.flush()
    return employee


def create_assignment_payload(event_id, employee_id, **overrides):
    payload = {
        "event_id": str(event_id),
        "employee_id": str(employee_id),
        "position": "Waiter",
        "planned_hours": "5.00",
        "compensation_type": "hourly",
        "compensation_rate": "12.50",
        "notes": "Evening shift",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def api_client(db_session):
    client, tenant, user = api_client_factory(
        db_session,
        permissions=[
            PermissionCode.STAFF_READ,
            PermissionCode.STAFF_ASSIGN,
        ],
    )

    try:
        yield client, tenant, user
    finally:
        app.dependency_overrides.clear()


def test_create_assignment_returns_201_and_calculates_compensation(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event = create_event_for_tenant(db_session, tenant)
    employee = create_employee_for_tenant(db_session, tenant)

    with client:
        response = client.post(
            "/api/v1/event-staff-assignments/",
            json=create_assignment_payload(event.id, employee.id),
        )

    assert response.status_code == 201
    body = response.json()

    assert body["event_id"] == str(event.id)
    assert body["employee_id"] == str(employee.id)
    assert body["tenant_id"] == str(tenant.id)
    assert body["status"] == "assigned"
    assert Decimal(body["planned_compensation"]) == Decimal("62.50")


def test_create_fixed_assignment_returns_201(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event = create_event_for_tenant(db_session, tenant)
    employee = create_employee_for_tenant(db_session, tenant)

    with client:
        response = client.post(
            "/api/v1/event-staff-assignments/",
            json=create_assignment_payload(
                event.id,
                employee.id,
                planned_hours="8.00",
                compensation_type="fixed",
                compensation_rate="150.00",
            ),
        )

    assert response.status_code == 201
    assert Decimal(response.json()["planned_compensation"]) == Decimal(
        "150.00"
    )


def test_create_assignment_with_nonexistent_employee_returns_404(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event = create_event_for_tenant(db_session, tenant)

    with client:
        response = client.post(
            "/api/v1/event-staff-assignments/",
            json=create_assignment_payload(event.id, uuid4()),
        )

    assert response.status_code == 404


def test_create_assignment_with_nonexistent_event_returns_404(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    employee = create_employee_for_tenant(db_session, tenant)

    with client:
        response = client.post(
            "/api/v1/event-staff-assignments/",
            json=create_assignment_payload(uuid4(), employee.id),
        )

    assert response.status_code == 404


def test_create_assignment_with_invalid_data_returns_422(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event = create_event_for_tenant(db_session, tenant)
    employee = create_employee_for_tenant(db_session, tenant)

    with client:
        response = client.post(
            "/api/v1/event-staff-assignments/",
            json=create_assignment_payload(
                event.id,
                employee.id,
                planned_hours="-1",
            ),
        )

    assert response.status_code == 422


def test_create_assignment_without_permission_returns_403(db_session):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.STAFF_READ],
    )
    event = create_event_for_tenant(db_session, tenant)
    employee = create_employee_for_tenant(db_session, tenant)

    try:
        with client:
            response = client.post(
                "/api/v1/event-staff-assignments/",
                json=create_assignment_payload(event.id, employee.id),
            )

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions."
    finally:
        app.dependency_overrides.clear()


def test_create_duplicate_assignment_returns_422(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event = create_event_for_tenant(db_session, tenant)
    employee = create_employee_for_tenant(db_session, tenant)
    payload = create_assignment_payload(event.id, employee.id)

    with client:
        first = client.post(
            "/api/v1/event-staff-assignments/",
            json=payload,
        )
        second = client.post(
            "/api/v1/event-staff-assignments/",
            json=payload,
        )

    assert first.status_code == 201
    assert second.status_code == 422


def test_list_assignments_returns_200_and_pagination(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event = create_event_for_tenant(db_session, tenant)
    employee = create_employee_for_tenant(db_session, tenant)

    with client:
        client.post(
            "/api/v1/event-staff-assignments/",
            json=create_assignment_payload(event.id, employee.id),
        )
        response = client.get(
            "/api/v1/event-staff-assignments/",
            params={"offset": 0, "limit": 10},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["offset"] == 0
    assert response.json()["limit"] == 10


def test_list_assignments_filters_by_event(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event = create_event_for_tenant(db_session, tenant)
    employee = create_employee_for_tenant(db_session, tenant)

    with client:
        client.post(
            "/api/v1/event-staff-assignments/",
            json=create_assignment_payload(event.id, employee.id),
        )
        response = client.get(
            "/api/v1/event-staff-assignments/",
            params={"event_id": str(event.id)},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_get_assignment_returns_200(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event = create_event_for_tenant(db_session, tenant)
    employee = create_employee_for_tenant(db_session, tenant)

    with client:
        created = client.post(
            "/api/v1/event-staff-assignments/",
            json=create_assignment_payload(event.id, employee.id),
        )
        assignment_id = created.json()["id"]

        response = client.get(
            f"/api/v1/event-staff-assignments/{assignment_id}",
        )

    assert response.status_code == 200
    assert response.json()["id"] == assignment_id


def test_get_nonexistent_assignment_returns_404(api_client):
    client, _, _ = api_client

    with client:
        response = client.get(
            f"/api/v1/event-staff-assignments/{uuid4()}",
        )

    assert response.status_code == 404


def test_update_assignment_returns_200(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event = create_event_for_tenant(db_session, tenant)
    employee = create_employee_for_tenant(db_session, tenant)

    with client:
        created = client.post(
            "/api/v1/event-staff-assignments/",
            json=create_assignment_payload(event.id, employee.id),
        )
        assignment_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/event-staff-assignments/{assignment_id}",
            json={"position": "Head Waiter"},
        )

    assert response.status_code == 200
    assert response.json()["position"] == "Head Waiter"


def test_assignment_status_can_be_confirmed_and_completed(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event = create_event_for_tenant(db_session, tenant)
    employee = create_employee_for_tenant(db_session, tenant)

    with client:
        created = client.post(
            "/api/v1/event-staff-assignments/",
            json=create_assignment_payload(event.id, employee.id),
        )
        assignment_id = created.json()["id"]

        confirmed = client.patch(
            f"/api/v1/event-staff-assignments/{assignment_id}",
            json={"status": "confirmed"},
        )
        completed = client.patch(
            f"/api/v1/event-staff-assignments/{assignment_id}",
            json={
                "status": "completed",
                "actual_hours": "6.00",
            },
        )

    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"

    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert Decimal(completed.json()["actual_compensation"]) == Decimal(
        "75.00"
    )


def test_assignment_can_be_cancelled(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event = create_event_for_tenant(db_session, tenant)
    employee = create_employee_for_tenant(db_session, tenant)

    with client:
        created = client.post(
            "/api/v1/event-staff-assignments/",
            json=create_assignment_payload(event.id, employee.id),
        )
        assignment_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/event-staff-assignments/{assignment_id}",
            json={"status": "cancelled"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
