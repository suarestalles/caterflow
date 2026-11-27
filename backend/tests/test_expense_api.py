
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
from app.models.event import Event
from app.models.expense import Expense
from app.models.financial_audit_log import FinancialAuditLog
from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant
from app.models.user import User


def create_tenant(db_session: Session):
    tenant = Tenant(name=f"Expense Tenant {uuid4()}")
    db_session.add(tenant)
    db_session.flush()
    return tenant


def create_user(db_session: Session):
    user = User(
        full_name="Expense Test User",
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
        name="Expense Test Role",
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


def create_event(db_session, tenant, status="draft"):
    client = Client(
        tenant_id=tenant.id,
        name="Expense Test Client",
        email=f"{uuid4()}@example.com",
    )
    db_session.add(client)
    db_session.flush()

    event = Event(
        tenant_id=tenant.id,
        client_id=client.id,
        name="Expense Test Event",
        starts_at=datetime(2026, 12, 15, 18, tzinfo=UTC),
        ends_at=datetime(2026, 12, 15, 23, tzinfo=UTC),
        guest_count=100,
        status=status,
        country="ES",
    )
    db_session.add(event)
    db_session.flush()
    return event


def expense_payload(**overrides):
    payload = {
        "category": "food",
        "description": "Food supplies",
        "amount": "300.00",
        "incurred_at": "2026-11-27",
        "supplier_name": "Local Supplier",
        "invoice_reference": "INV-001",
        "notes": "Test expense",
    }
    payload.update(overrides)
    return payload


def test_create_expense_returns_201(api_client):
    client, _, user = api_client

    with client:
        response = client.post(
            "/api/v1/expenses/",
            json=expense_payload(),
        )

    assert response.status_code == 201, response.text
    body = response.json()

    assert body["description"] == "Food supplies"
    assert body["amount"] == "300.00"
    assert body["category"] == "food"
    assert body["recorded_by_user_id"] == str(user.id)


def test_list_expenses_returns_items_and_total(api_client):
    client, _, _ = api_client

    with client:
        created = client.post(
            "/api/v1/expenses/",
            json=expense_payload(),
        )
        assert created.status_code == 201, created.text

        response = client.get("/api/v1/expenses/")

    assert response.status_code == 200
    body = response.json()

    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["description"] == "Food supplies"


def test_get_expense_returns_200(api_client):
    client, _, _ = api_client

    with client:
        created = client.post(
            "/api/v1/expenses/",
            json=expense_payload(),
        )
        expense_id = created.json()["id"]

        response = client.get(f"/api/v1/expenses/{expense_id}")

    assert response.status_code == 200
    assert response.json()["id"] == expense_id


def test_update_expense_returns_200(api_client):
    client, _, _ = api_client

    with client:
        created = client.post(
            "/api/v1/expenses/",
            json=expense_payload(),
        )
        expense_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/expenses/{expense_id}",
            json={
                "description": "Updated food supplies",
                "amount": "350.00",
            },
        )

    assert response.status_code == 200, response.text
    assert response.json()["description"] == "Updated food supplies"
    assert response.json()["amount"] == "350.00"


def test_get_expense_returns_404_when_not_found(api_client):
    client, _, _ = api_client

    with client:
        response = client.get(f"/api/v1/expenses/{uuid4()}")

    assert response.status_code == 404


def test_list_expenses_by_event(api_client, db_session):
    client, tenant, _ = api_client
    event = create_event(db_session, tenant)

    with client:
        response = client.post(
            "/api/v1/expenses/",
            json=expense_payload(event_id=str(event.id)),
        )
        assert response.status_code == 201, response.text

        listing = client.get(
            f"/api/v1/expenses/events/{event.id}"
        )

    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["event_id"] == str(event.id)


def test_get_expense_balance_starts_pending(api_client):
    client, _, _ = api_client

    with client:
        created = client.post(
            "/api/v1/expenses/",
            json=expense_payload(),
        )
        expense_id = created.json()["id"]

        response = client.get(
            f"/api/v1/expenses/{expense_id}/balance"
        )

    assert response.status_code == 200
    body = response.json()

    assert body["expense_amount"] == "300.00"
    assert body["total_paid"] == "0"
    assert body["outstanding"] == "300.00"
    assert body["status"] == "pending"


def test_create_expense_without_permission_returns_403(db_session):
    client, _, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.FINANCE_READ],
    )

    try:
        with client:
            response = client.post(
                "/api/v1/expenses/",
                json=expense_payload(),
            )

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions."
    finally:
        app.dependency_overrides.clear()


def test_list_expenses_without_finance_read_returns_403(db_session):
    client, _, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.FINANCE_EXPENSES_MANAGE],
    )

    try:
        with client:
            response = client.get("/api/v1/expenses/")

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_expense_from_another_tenant_returns_404(
    db_session,
    api_client,
):
    client, _, _ = api_client

    other_tenant = create_tenant(db_session)
    other_user = create_user(db_session)

    foreign_expense = Expense(
        tenant_id=other_tenant.id,
        category="food",
        description="Foreign expense",
        amount=Decimal("100.00"),
        incurred_at=datetime(2026, 11, 27).date(),
        recorded_by_user_id=other_user.id,
    )
    db_session.add(foreign_expense)
    db_session.flush()

    with client:
        response = client.get(
            f"/api/v1/expenses/{foreign_expense.id}"
        )

    assert response.status_code == 404


def test_completed_event_expense_amount_update_requires_reason(
    api_client,
    db_session,
):
    client, tenant, _ = api_client
    event = create_event(db_session, tenant, status="completed")

    with client:
        created = client.post(
            "/api/v1/expenses/",
            json=expense_payload(event_id=str(event.id)),
        )
        assert created.status_code == 201, created.text

        expense_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/expenses/{expense_id}",
            json={"amount": "350.00"},
        )

    assert response.status_code == 422

    expense = db_session.get(Expense, uuid4()) if False else db_session.scalar(
        select(Expense).where(Expense.id == expense_id)
    )
    assert expense is not None
    assert expense.amount == Decimal("300.00")

    audit_logs = db_session.scalars(
        select(FinancialAuditLog).where(
            FinancialAuditLog.entity_id == expense.id,
        )
    ).all()
    assert audit_logs == []


def test_completed_event_expense_amount_update_creates_audit_log(
    api_client,
    db_session,
):
    client, tenant, user = api_client
    event = create_event(db_session, tenant, status="completed")

    with client:
        created = client.post(
            "/api/v1/expenses/",
            json=expense_payload(event_id=str(event.id)),
        )
        assert created.status_code == 201, created.text

        expense_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/expenses/{expense_id}",
            json={
                "amount": "350.00",
                "reason": "Additional supplies were required.",
            },
        )

    assert response.status_code == 200, response.text
    assert response.json()["amount"] == "350.00"

    audit_log = db_session.scalar(
        select(FinancialAuditLog).where(
            FinancialAuditLog.entity_type == "expense",
            FinancialAuditLog.entity_id == expense_id,
        )
    )

    assert audit_log is not None
    assert audit_log.event_id == event.id
    assert audit_log.entity_type == "expense"
    assert audit_log.field_name == "amount"
    assert audit_log.old_value == "300.00"
    assert audit_log.new_value == "350.00"
    assert audit_log.reason == "Additional supplies were required."
    assert audit_log.recorded_by_user_id == user.id


def test_non_completed_event_expense_amount_update_does_not_create_audit_log(
    api_client,
    db_session,
):
    client, tenant, _ = api_client
    event = create_event(db_session, tenant, status="draft")

    with client:
        created = client.post(
            "/api/v1/expenses/",
            json=expense_payload(event_id=str(event.id)),
        )
        assert created.status_code == 201, created.text

        expense_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/expenses/{expense_id}",
            json={"amount": "350.00"},
        )

    assert response.status_code == 200, response.text
    assert response.json()["amount"] == "350.00"

    audit_logs = db_session.scalars(
        select(FinancialAuditLog).where(
            FinancialAuditLog.entity_id == expense_id,
        )
    ).all()

    assert audit_logs == []


def test_completed_event_expense_description_update_does_not_create_audit_log(
    api_client,
    db_session,
):
    client, tenant, _ = api_client
    event = create_event(db_session, tenant, status="completed")

    with client:
        created = client.post(
            "/api/v1/expenses/",
            json=expense_payload(event_id=str(event.id)),
        )
        assert created.status_code == 201, created.text

        expense_id = created.json()["id"]

        response = client.patch(
            f"/api/v1/expenses/{expense_id}",
            json={"description": "Updated food supplies"},
        )

    assert response.status_code == 200, response.text
    assert response.json()["description"] == "Updated food supplies"

    audit_logs = db_session.scalars(
        select(FinancialAuditLog).where(
            FinancialAuditLog.entity_id == expense_id,
        )
    ).all()

    assert audit_logs == []
