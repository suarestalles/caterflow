
from datetime import UTC, datetime
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
from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant
from app.models.user import User


def create_tenant(db_session: Session):
    tenant = Tenant(name=f"Expense Payment Tenant {uuid4()}")
    db_session.add(tenant)
    db_session.flush()
    return tenant


def create_user(db_session: Session):
    user = User(
        full_name="Expense Payment Test User",
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
        name="Expense Payment Test Role",
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


@pytest.fixture
def api_client(db_session):
    client, tenant, user = api_client_factory(
        db_session,
        permissions=[
            PermissionCode.FINANCE_READ,
            PermissionCode.FINANCE_EXPENSES_MANAGE,
        ],
    )

    try:
        yield client, tenant, user
    finally:
        app.dependency_overrides.clear()


def expense_payload(**overrides):
    payload = {
        "category": "food",
        "description": "Food supplies",
        "amount": "300.00",
        "incurred_at": "2026-11-27",
    }
    payload.update(overrides)
    return payload


def payment_payload(expense_id, **overrides):
    payload = {
        "expense_id": expense_id,
        "amount": "100.00",
        "paid_at": "2026-11-27T10:00:00Z",
        "method": "bank_transfer",
        "external_reference": "TRANSFER-001",
        "notes": "Partial payment",
    }
    payload.update(overrides)
    return payload


def create_expense(client):
    response = client.post(
        "/api/v1/expenses/",
        json=expense_payload(),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_create_expense_payment_returns_201(api_client):
    client, _, user = api_client

    with client:
        expense_id = create_expense(client)

        response = client.post(
            "/api/v1/expense-payments/",
            json=payment_payload(expense_id),
        )

    assert response.status_code == 201, response.text
    body = response.json()

    assert body["expense_id"] == expense_id
    assert body["amount"] == "100.00"
    assert body["method"] == "bank_transfer"
    assert body["recorded_by_user_id"] == str(user.id)


def test_list_payments_and_get_balance(api_client):
    client, _, _ = api_client

    with client:
        expense_id = create_expense(client)

        first = client.post(
            "/api/v1/expense-payments/",
            json=payment_payload(expense_id, amount="100.00"),
        )
        second = client.post(
            "/api/v1/expense-payments/",
            json=payment_payload(
                expense_id,
                amount="150.00",
                notes="Second payment",
            ),
        )

        assert first.status_code == 201, first.text
        assert second.status_code == 201, second.text

        payments = client.get(
            f"/api/v1/expense-payments/expenses/{expense_id}"
        )
        balance = client.get(
            f"/api/v1/expense-payments/expenses/{expense_id}/balance"
        )

    assert payments.status_code == 200
    assert len(payments.json()) == 2

    assert balance.status_code == 200
    body = balance.json()

    assert body["expense_amount"] == "300.00"
    assert body["total_paid"] == "250.00"
    assert body["outstanding"] == "50.00"
    assert body["status"] == "partially_paid"


def test_full_payment_changes_status_to_paid(api_client):
    client, _, _ = api_client

    with client:
        expense_id = create_expense(client)

        response = client.post(
            "/api/v1/expense-payments/",
            json=payment_payload(expense_id, amount="300.00"),
        )
        assert response.status_code == 201, response.text

        balance = client.get(
            f"/api/v1/expense-payments/expenses/{expense_id}/balance"
        )

    assert balance.status_code == 200
    assert balance.json()["total_paid"] == "300.00"
    assert balance.json()["outstanding"] == "0.00"
    assert balance.json()["status"] == "paid"


def test_payment_above_outstanding_returns_409(api_client):
    client, _, _ = api_client

    with client:
        expense_id = create_expense(client)

        first = client.post(
            "/api/v1/expense-payments/",
            json=payment_payload(expense_id, amount="250.00"),
        )
        second = client.post(
            "/api/v1/expense-payments/",
            json=payment_payload(expense_id, amount="60.00"),
        )

    assert first.status_code == 201
    assert second.status_code == 409


def test_payment_after_full_payment_returns_409(api_client):
    client, _, _ = api_client

    with client:
        expense_id = create_expense(client)

        first = client.post(
            "/api/v1/expense-payments/",
            json=payment_payload(expense_id, amount="300.00"),
        )
        second = client.post(
            "/api/v1/expense-payments/",
            json=payment_payload(expense_id, amount="1.00"),
        )

    assert first.status_code == 201
    assert second.status_code == 409


def test_get_payment_returns_200(api_client):
    client, _, _ = api_client

    with client:
        expense_id = create_expense(client)

        created = client.post(
            "/api/v1/expense-payments/",
            json=payment_payload(expense_id),
        )
        assert created.status_code == 201, created.text

        payment_id = created.json()["id"]

        response = client.get(
            f"/api/v1/expense-payments/{payment_id}"
        )

    assert response.status_code == 200
    assert response.json()["id"] == payment_id


def test_create_payment_for_nonexistent_expense_returns_404(api_client):
    client, _, _ = api_client

    with client:
        response = client.post(
            "/api/v1/expense-payments/",
            json=payment_payload(str(uuid4())),
        )

    assert response.status_code == 404



def test_create_payment_without_permission_returns_403(db_session):
    client, _, _ = api_client_factory(
        db_session,
        permissions=[
            PermissionCode.FINANCE_READ,
            PermissionCode.FINANCE_EXPENSES_MANAGE,
        ],
    )

    try:
        with client:
            expense_id = create_expense(client)

        # Remove apenas a permissão de escrita após criar a despesa.
        membership = db_session.scalar(
            select(Membership).where(
                Membership.tenant_id == client.app.dependency_overrides[
                    get_auth_context
                ]().tenant_id
            )
        )
        role = db_session.scalar(
            select(Role)
            .join(MembershipRole, MembershipRole.role_id == Role.id)
            .where(MembershipRole.membership_id == membership.id)
        )

        permission = db_session.scalar(
            select(Permission).where(
                Permission.code == PermissionCode.FINANCE_EXPENSES_MANAGE.value
            )
        )

        role_permission = db_session.scalar(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id,
            )
        )
        db_session.delete(role_permission)
        db_session.flush()

        with client:
            response = client.post(
                "/api/v1/expense-payments/",
                json=payment_payload(expense_id),
            )

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions."
    finally:
        app.dependency_overrides.clear()



def test_get_balance_without_finance_read_returns_403(db_session):
    client, _, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.FINANCE_EXPENSES_MANAGE],
    )

    try:
        with client:
            expense_id = create_expense(client)

            response = client.get(
                f"/api/v1/expense-payments/expenses/{expense_id}/balance"
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
