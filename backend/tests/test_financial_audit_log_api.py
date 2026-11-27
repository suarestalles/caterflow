
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
from app.models.client import Client
from app.models.event import Event
from app.models.financial_audit_log import FinancialAuditLog
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


def create_user(db_session: Session, name: str) -> User:
    user = User(
        full_name=name,
        email=f"{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def assign_permissions(
    db_session: Session,
    *,
    tenant: Tenant,
    membership: Membership,
    permission_codes: list[PermissionCode],
) -> None:
    role = Role(
        tenant_id=tenant.id,
        name="Audit Test Role",
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
    tenant = create_tenant(db_session, "Audit Test Tenant")
    user = create_user(db_session, "Audit Test User")

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
        permissions=[PermissionCode.FINANCE_READ],
    )

    try:
        yield client, tenant, user
    finally:
        app.dependency_overrides.clear()


def create_audit_log(
    db_session: Session,
    *,
    tenant: Tenant,
    user: User,
    entity_id=None,
    event_id=None,
    entity_type="expense",
    field_name="amount",
    old_value="100.00",
    new_value="120.00",
):
    audit_log = FinancialAuditLog(
        tenant_id=tenant.id,
        event_id=event_id,
        entity_type=entity_type,
        entity_id=entity_id or uuid4(),
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        reason="Correction after event completion.",
        recorded_by_user_id=user.id,
    )
    db_session.add(audit_log)
    db_session.flush()
    return audit_log


def create_event(db_session: Session, tenant: Tenant) -> Event:
    client = Client(
        tenant_id=tenant.id,
        name="Audit Test Client",
        email=f"{uuid4()}@example.com",
    )
    db_session.add(client)
    db_session.flush()

    event = Event(
        tenant_id=tenant.id,
        client_id=client.id,
        name="Audit Test Event",
        starts_at=datetime(2026, 12, 15, 18, tzinfo=UTC),
        ends_at=datetime(2026, 12, 15, 23, tzinfo=UTC),
        guest_count=100,
        status="completed",
        country="ES",
    )
    db_session.add(event)
    db_session.flush()
    return event


def test_list_entity_audit_logs_returns_200(
    api_client,
    db_session,
):
    client, tenant, user = api_client
    entity_id = uuid4()

    first = create_audit_log(
        db_session,
        tenant=tenant,
        user=user,
        entity_id=entity_id,
    )
    second = create_audit_log(
        db_session,
        tenant=tenant,
        user=user,
        entity_id=entity_id,
        field_name="description",
        old_value="Old description",
        new_value="New description",
    )

    create_audit_log(
        db_session,
        tenant=tenant,
        user=user,
    )

    with client:
        response = client.get(
            f"/api/v1/financial-audit-logs/entities/expense/{entity_id}"
        )

    assert response.status_code == 200
    body = response.json()

    assert len(body) == 2
    assert {item["id"] for item in body} == {
        str(first.id),
        str(second.id),
    }
    assert all(item["entity_id"] == str(entity_id) for item in body)


def test_list_event_audit_logs_returns_200(
    api_client,
    db_session,
):
    client, tenant, user = api_client

    event = create_event(db_session, tenant)
    other_event = create_event(db_session, tenant)

    first = create_audit_log(
        db_session,
        tenant=tenant,
        user=user,
        event_id=event.id,
    )
    second = create_audit_log(
        db_session,
        tenant=tenant,
        user=user,
        event_id=event.id,
        field_name="actual_compensation",
    )

    create_audit_log(
        db_session,
        tenant=tenant,
        user=user,
        event_id=other_event.id,
    )

    with client:
        response = client.get(
            f"/api/v1/financial-audit-logs/events/{event.id}"
        )

    assert response.status_code == 200
    body = response.json()

    assert len(body) == 2
    assert {item["id"] for item in body} == {
        str(first.id),
        str(second.id),
    }
    assert all(item["event_id"] == str(event.id) for item in body)


def test_list_audit_logs_without_permission_returns_403(db_session):
    client, tenant, user = api_client_factory(
        db_session,
        permissions=[],
    )

    entity_id = uuid4()
    create_audit_log(
        db_session,
        tenant=tenant,
        user=user,
        entity_id=entity_id,
    )

    try:
        with client:
            response = client.get(
                f"/api/v1/financial-audit-logs/entities/expense/{entity_id}"
            )

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions."
    finally:
        app.dependency_overrides.clear()


def test_list_entity_audit_logs_does_not_expose_other_tenant_data(
    db_session,
    api_client,
):
    client, _, _ = api_client

    other_tenant = create_tenant(db_session, "Other Audit Tenant")
    other_user = create_user(db_session, "Other Audit User")
    entity_id = uuid4()

    create_audit_log(
        db_session,
        tenant=other_tenant,
        user=other_user,
        entity_id=entity_id,
    )

    with client:
        response = client.get(
            f"/api/v1/financial-audit-logs/entities/expense/{entity_id}"
        )

    assert response.status_code == 200
    assert response.json() == []
