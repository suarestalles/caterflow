
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


def create_tenant(db_session: Session):
    tenant = Tenant(name=f"Compensation Tenant {uuid4()}")
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
        name="Compensation Test Role",
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


def create_event(db_session, tenant):
    client = Client(
        tenant_id=tenant.id,
        name="Test Client",
        email=f"{uuid4()}@example.com",
    )
    db_session.add(client)
    db_session.flush()

    event = Event(
        tenant_id=tenant.id,
        client_id=client.id,
        name="Test Event",
        starts_at=datetime(2026, 12, 15, 18, tzinfo=UTC),
        ends_at=datetime(2026, 12, 15, 23, tzinfo=UTC),
        guest_count=100,
        status="draft",
        country="ES",
    )
    db_session.add(event)
    db_session.flush()
    return event


def create_employee(db_session, tenant):
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


def create_assignment(client, db_session, tenant):
    event = create_event(db_session, tenant)
    employee = create_employee(db_session, tenant)

    response = client.post(
        "/api/v1/event-staff-assignments/",
        json={
            "event_id": str(event.id),
            "employee_id": str(employee.id),
            "position": "Waiter",
            "planned_hours": "5.00",
            "compensation_type": "hourly",
            "compensation_rate": "12.50",
        },
    )
    assert response.status_code == 201

    assignment_id = response.json()["id"]

    confirmed = client.patch(
        f"/api/v1/event-staff-assignments/{assignment_id}",
        json={"status": "confirmed"},
    )
    assert confirmed.status_code == 200, confirmed.text

    completed = client.patch(
        f"/api/v1/event-staff-assignments/{assignment_id}",
        json={
            "status": "completed",
            "actual_hours": "6.00",
        },
    )
    assert completed.status_code == 200, completed.text
    assert Decimal(completed.json()["actual_compensation"]) == Decimal(
        "75.00"
    )

    return assignment_id


@pytest.fixture
def api_client(db_session):
    client, tenant, user = api_client_factory(
        db_session,
        permissions=[
            PermissionCode.STAFF_READ,
            PermissionCode.STAFF_ASSIGN,
            PermissionCode.FINANCE_READ,
            PermissionCode.FINANCE_PAYMENTS_MANAGE,
        ],
    )

    try:
        yield client, tenant, user
    finally:
        app.dependency_overrides.clear()


def payment_payload(assignment_id, **overrides):
    payload = {
        "assignment_id": assignment_id,
        "amount": "40.00",
        "paid_at": "2026-11-27T10:00:00Z",
        "method": "bank_transfer",
        "notes": "Partial payment",
    }
    payload.update(overrides)
    return payload


def test_create_employee_compensation_payment_returns_201(
    db_session,
    api_client,
):
    client, tenant, user = api_client

    with client:
        assignment_id = create_assignment(client, db_session, tenant)

        response = client.post(
            "/api/v1/employee-compensation-payments/",
            json=payment_payload(assignment_id),
        )

    assert response.status_code == 201
    body = response.json()

    assert body["assignment_id"] == assignment_id
    assert body["amount"] == "40.00"
    assert body["method"] == "bank_transfer"
    assert body["recorded_by_user_id"] == str(user.id)


def test_list_payments_and_get_balance(
    db_session,
    api_client,
):
    client, tenant, _ = api_client

    with client:
        assignment_id = create_assignment(client, db_session, tenant)

        first = client.post(
            "/api/v1/employee-compensation-payments/",
            json=payment_payload(assignment_id, amount="40.00"),
        )
        second = client.post(
            "/api/v1/employee-compensation-payments/",
            json=payment_payload(
                assignment_id,
                amount="20.00",
                notes="Second payment",
            ),
        )

        assert first.status_code == 201
        assert second.status_code == 201

        payments = client.get(
            f"/api/v1/employee-compensation-payments/assignments/{assignment_id}"
        )
        balance = client.get(
            f"/api/v1/employee-compensation-payments/assignments/{assignment_id}/balance"
        )

    assert payments.status_code == 200
    assert len(payments.json()) == 2

    assert balance.status_code == 200
    assert balance.json()["compensation_due"] == "75.00"
    assert balance.json()["total_paid"] == "60.00"
    assert balance.json()["outstanding"] == "15.00"
    assert balance.json()["status"] == "partially_paid"


def test_get_employee_compensation_payment_returns_200(
    db_session,
    api_client,
):
    client, tenant, _ = api_client

    with client:
        assignment_id = create_assignment(client, db_session, tenant)

        created = client.post(
            "/api/v1/employee-compensation-payments/",
            json=payment_payload(assignment_id),
        )
        payment_id = created.json()["id"]

        response = client.get(
            f"/api/v1/employee-compensation-payments/{payment_id}"
        )

    assert response.status_code == 200
    assert response.json()["id"] == payment_id


def test_create_payment_above_outstanding_returns_409(
    db_session,
    api_client,
):
    client, tenant, _ = api_client

    with client:
        assignment_id = create_assignment(client, db_session, tenant)

        first = client.post(
            "/api/v1/employee-compensation-payments/",
            json=payment_payload(assignment_id, amount="60.00"),
        )
        second = client.post(
            "/api/v1/employee-compensation-payments/",
            json=payment_payload(assignment_id, amount="20.00"),
        )

    assert first.status_code == 201
    assert second.status_code == 409


def test_create_payment_without_permission_returns_403(db_session):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[
            PermissionCode.STAFF_READ,
            PermissionCode.STAFF_ASSIGN,
            PermissionCode.FINANCE_READ,
        ],
    )

    try:
        with client:
            assignment_id = create_assignment(client, db_session, tenant)

            response = client.post(
                "/api/v1/employee-compensation-payments/",
                json=payment_payload(assignment_id),
            )

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions."
    finally:
        app.dependency_overrides.clear()


def test_get_balance_without_finance_read_returns_403(db_session):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[
            PermissionCode.STAFF_READ,
            PermissionCode.STAFF_ASSIGN,
        ],
    )

    try:
        with client:
            assignment_id = create_assignment(client, db_session, tenant)

            response = client.get(
                f"/api/v1/employee-compensation-payments/assignments/{assignment_id}/balance"
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_get_balance_for_nonexistent_assignment_returns_404(api_client):
    client, _, _ = api_client

    with client:
        response = client.get(
            f"/api/v1/employee-compensation-payments/assignments/{uuid4()}/balance"
        )

    assert response.status_code == 404
