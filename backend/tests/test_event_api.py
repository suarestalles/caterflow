
from datetime import UTC, datetime
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
from app.models.client import Client
from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant
from app.models.user import User


def create_tenant(db_session: Session, name: str = "Test Tenant") -> Tenant:
    tenant = Tenant(name=name)
    db_session.add(tenant)
    db_session.flush()
    return tenant


def create_user(db_session: Session, email: str = "user@example.com") -> User:
    user = User(
        full_name="Test User",
        email=email,
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
    membership = Membership(
        user_id=user.id,
        tenant_id=tenant.id,
    )
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


def create_client_for_tenant(
    db_session: Session,
    tenant: Tenant,
) -> Client:
    client = Client(
        tenant_id=tenant.id,
        name="Maria Silva",
        email=f"maria-{uuid4()}@example.com",
    )
    db_session.add(client)
    db_session.flush()
    return client


def create_event_payload(client_id, **overrides):
    payload = {
        "client_id": str(client_id),
        "name": "Corporate Event",
        "starts_at": "2026-12-15T18:00:00Z",
        "ends_at": "2026-12-15T23:00:00Z",
        "guest_count": 100,
        "status": "draft",
        "country": "ES",
    }
    payload.update(overrides)
    return payload


def create_persisted_event(
    db_session: Session,
    tenant: Tenant,
    client: Client,
):
    from app.models.event import Event

    event = Event(
        tenant_id=tenant.id,
        client_id=client.id,
        name="Existing Event",
        starts_at=datetime(2026, 12, 15, 18, tzinfo=UTC),
        ends_at=datetime(2026, 12, 15, 23, tzinfo=UTC),
        guest_count=100,
        status="draft",
        country="ES",
    )
    db_session.add(event)
    db_session.flush()
    return event


@pytest.fixture
def api_client(db_session):
    client, tenant, user = api_client_factory(
        db_session,
        permissions=[
            PermissionCode.EVENTS_READ,
            PermissionCode.EVENTS_CREATE,
            PermissionCode.EVENTS_UPDATE,
            PermissionCode.EVENTS_CANCEL,
        ],
    )

    try:
        yield client, tenant, user
    finally:
        app.dependency_overrides.clear()


def test_create_event_returns_201(db_session, api_client):
    client, tenant, _ = api_client
    event_client = create_client_for_tenant(db_session, tenant)

    with client:
        response = client.post(
            "/api/v1/events/",
            json=create_event_payload(event_client.id),
        )

    print("STATUS:", response.status_code)
    print("BODY:", response.text)

    assert response.status_code == 201
    assert response.json()["name"] == "Corporate Event"
    assert response.json()["client_id"] == str(event_client.id)
    assert response.json()["tenant_id"] == str(tenant.id)
    assert response.json()["status"] == "draft"


def test_create_event_with_invalid_client_returns_404(api_client):
    client, _, _ = api_client

    with client:
        response = client.post(
            "/api/v1/events/",
            json=create_event_payload(uuid4()),
        )

    assert response.status_code == 404


def test_create_event_with_invalid_date_range_returns_422(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event_client = create_client_for_tenant(db_session, tenant)

    with client:
        response = client.post(
            "/api/v1/events/",
            json=create_event_payload(
                event_client.id,
                starts_at="2026-12-15T23:00:00Z",
                ends_at="2026-12-15T18:00:00Z",
            ),
        )

    assert response.status_code == 422


def test_create_event_without_permission_returns_403(db_session):
    client, tenant, _ = api_client_factory(db_session, permissions=[])

    try:
        event_client = create_client_for_tenant(db_session, tenant)

        with client:
            response = client.post(
                "/api/v1/events/",
                json=create_event_payload(event_client.id),
            )

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions."
    finally:
        app.dependency_overrides.clear()


def test_list_events_returns_200_and_pagination(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event_client = create_client_for_tenant(db_session, tenant)

    with client:
        client.post(
            "/api/v1/events/",
            json=create_event_payload(event_client.id),
        )
        response = client.get(
            "/api/v1/events/",
            params={"offset": 0, "limit": 10},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["offset"] == 0
    assert response.json()["limit"] == 10


def test_list_events_filters_by_status(db_session, api_client):
    client, tenant, _ = api_client
    event_client = create_client_for_tenant(db_session, tenant)

    with client:
        client.post(
            "/api/v1/events/",
            json=create_event_payload(event_client.id),
        )
        response = client.get(
            "/api/v1/events/",
            params={"status": "draft"},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["status"] == "draft"


def test_list_events_without_permission_returns_403(db_session):
    client, _, _ = api_client_factory(db_session, permissions=[])

    try:
        with client:
            response = client.get("/api/v1/events/")

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_get_event_returns_200(db_session, api_client):
    client, tenant, _ = api_client
    event_client = create_client_for_tenant(db_session, tenant)
    event = create_persisted_event(db_session, tenant, event_client)

    with client:
        response = client.get(f"/api/v1/events/{event.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(event.id)
    assert response.json()["name"] == "Existing Event"


def test_get_event_not_found_returns_404(api_client):
    client, _, _ = api_client

    with client:
        response = client.get(f"/api/v1/events/{uuid4()}")

    assert response.status_code == 404


def test_get_event_from_another_tenant_returns_404(
    db_session,
    api_client,
):
    client, _, _ = api_client

    other_tenant = create_tenant(db_session, name="Other Tenant")
    other_client = create_client_for_tenant(db_session, other_tenant)
    event = create_persisted_event(
        db_session,
        other_tenant,
        other_client,
    )

    with client:
        response = client.get(f"/api/v1/events/{event.id}")

    assert response.status_code == 404


def test_update_event_returns_200(db_session, api_client):
    client, tenant, _ = api_client
    event_client = create_client_for_tenant(db_session, tenant)
    event = create_persisted_event(db_session, tenant, event_client)

    with client:
        response = client.patch(
            f"/api/v1/events/{event.id}",
            json={"name": "Updated Corporate Event"},
        )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Corporate Event"


def test_update_event_with_invalid_transition_returns_422(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event_client = create_client_for_tenant(db_session, tenant)
    event = create_persisted_event(db_session, tenant, event_client)

    with client:
        response = client.patch(
            f"/api/v1/events/{event.id}",
            json={"status": "completed"},
        )

    assert response.status_code == 422


def test_update_event_without_permission_returns_403(db_session):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.EVENTS_READ],
    )

    try:
        event_client = create_client_for_tenant(db_session, tenant)
        event = create_persisted_event(db_session, tenant, event_client)

        with client:
            response = client.patch(
                f"/api/v1/events/{event.id}",
                json={"name": "Updated Event"},
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_cancel_event_returns_200(db_session, api_client):
    client, tenant, _ = api_client
    event_client = create_client_for_tenant(db_session, tenant)
    event = create_persisted_event(db_session, tenant, event_client)

    with client:
        response = client.post(
            f"/api/v1/events/{event.id}/cancel",
        )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cancel_event_without_permission_returns_403(db_session):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.EVENTS_READ],
    )

    try:
        event_client = create_client_for_tenant(db_session, tenant)
        event = create_persisted_event(db_session, tenant, event_client)

        with client:
            response = client.post(
                f"/api/v1/events/{event.id}/cancel",
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_cancel_completed_event_returns_422(db_session, api_client):
    client, tenant, _ = api_client
    event_client = create_client_for_tenant(db_session, tenant)
    event = create_persisted_event(db_session, tenant, event_client)
    event.status = "completed"
    db_session.flush()

    with client:
        response = client.post(
            f"/api/v1/events/{event.id}/cancel",
        )

    assert response.status_code == 422



def test_events_without_authentication_return_401(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/events/")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()
