
from datetime import UTC, datetime, timedelta

import pytest

from app.db.tenant_session import TenantSession
from app.models.client import Client
from app.models.event import Event, EventStatus
from app.models.tenant import Tenant
from app.repositories import events as event_repository
from app.services.events import (
    EventClientNotFoundError,
    EventNotFoundError,
    InvalidEventDataError,
    cancel_event,
    create_event,
    get_event,
    list_events,
    update_event,
)


def create_tenant_session(db_session, tenant_id):
    return TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant_id,
    )


def create_tenant_and_client(db_session, name="Test Client"):
    tenant = Tenant(name=f"Tenant {name}")
    db_session.add(tenant)
    db_session.flush()

    client = Client(
        tenant_id=tenant.id,
        name=name,
        email=f"{name.lower().replace(' ', '.')}@example.com",
    )
    db_session.add(client)
    db_session.flush()

    return tenant, client


def event_data(client_id, **overrides):
    data = {
        "client_id": client_id,
        "name": "Corporate Event",
        "starts_at": datetime(2026, 12, 15, 18, 0, tzinfo=UTC),
        "ends_at": datetime(2026, 12, 15, 23, 0, tzinfo=UTC),
        "guest_count": 100,
        "status": EventStatus.DRAFT.value,
        "country": "ES",
    }
    data.update(overrides)
    return data


def test_create_event(db_session):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = create_event(
            tenant_db,
            data=event_data(client.id),
        )

        assert event.id is not None
        assert event.tenant_id == tenant.id
        assert event.client_id == client.id
        assert event.status == EventStatus.DRAFT.value
    finally:
        tenant_db.close()


def test_create_event_with_company_client(db_session):
    tenant = Tenant(name="Company Tenant")
    db_session.add(tenant)
    db_session.flush()

    client = Client(
        tenant_id=tenant.id,
        name="Example Company",
        client_type="company",
        email="company@example.com",
    )
    db_session.add(client)
    db_session.flush()

    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = create_event(
            tenant_db,
            data=event_data(client.id),
        )

        assert event.client_id == client.id
    finally:
        tenant_db.close()


def test_create_event_rejects_nonexistent_client(db_session):
    tenant, _ = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(EventClientNotFoundError):
            create_event(
                tenant_db,
                data=event_data(
                    __import__("uuid").uuid4(),
                ),
            )
    finally:
        tenant_db.close()


def test_create_event_rejects_client_from_another_tenant(db_session):
    tenant, _ = create_tenant_and_client(db_session)
    other_tenant, other_client = create_tenant_and_client(
        db_session,
        name="Other Client",
    )
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(EventClientNotFoundError):
            create_event(
                tenant_db,
                data=event_data(other_client.id),
            )
    finally:
        tenant_db.close()

        # The other tenant is only used to prepare the test data.
        assert other_tenant.id != tenant.id


def test_create_event_rejects_archived_client(db_session):
    tenant, client = create_tenant_and_client(db_session)
    client.archived_at = datetime.now(UTC)
    db_session.flush()

    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(EventClientNotFoundError):
            create_event(
                tenant_db,
                data=event_data(client.id),
            )
    finally:
        tenant_db.close()


@pytest.mark.parametrize(
    ("starts_at", "ends_at"),
    [
        (
            datetime(2026, 12, 15, 23, tzinfo=UTC),
            datetime(2026, 12, 15, 18, tzinfo=UTC),
        ),
        (
            datetime(2026, 12, 15, 18, tzinfo=UTC),
            datetime(2026, 12, 15, 18, tzinfo=UTC),
        ),
    ],
)
def test_create_event_rejects_invalid_date_range(
    db_session,
    starts_at,
    ends_at,
):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(InvalidEventDataError):
            create_event(
                tenant_db,
                data=event_data(
                    client.id,
                    starts_at=starts_at,
                    ends_at=ends_at,
                ),
            )
    finally:
        tenant_db.close()


def test_create_event_rejects_naive_datetime(db_session):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(InvalidEventDataError):
            create_event(
                tenant_db,
                data=event_data(
                    client.id,
                    starts_at=datetime(2026, 12, 15, 18),
                ),
            )
    finally:
        tenant_db.close()


def test_get_event(db_session):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = create_event(
            tenant_db,
            data=event_data(client.id),
        )

        result = get_event(tenant_db, event_id=event.id)

        assert result.id == event.id
    finally:
        tenant_db.close()


def test_get_nonexistent_event_raises_error(db_session):
    from uuid import uuid4

    tenant, _ = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(EventNotFoundError):
            get_event(tenant_db, event_id=uuid4())
    finally:
        tenant_db.close()


def test_update_event(db_session):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = create_event(
            tenant_db,
            data=event_data(client.id),
        )

        updated = update_event(
            tenant_db,
            event_id=event.id,
            data={"name": "Updated Event"},
        )

        assert updated.name == "Updated Event"
    finally:
        tenant_db.close()


def test_update_event_validates_complete_date_range(db_session):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = create_event(
            tenant_db,
            data=event_data(client.id),
        )

        with pytest.raises(InvalidEventDataError):
            update_event(
                tenant_db,
                event_id=event.id,
                data={
                    "ends_at": datetime(
                        2026,
                        12,
                        15,
                        17,
                        tzinfo=UTC,
                    )
                },
            )
    finally:
        tenant_db.close()


def test_update_event_rejects_empty_data(db_session):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = create_event(
            tenant_db,
            data=event_data(client.id),
        )

        with pytest.raises(InvalidEventDataError):
            update_event(
                tenant_db,
                event_id=event.id,
                data={},
            )
    finally:
        tenant_db.close()


def test_update_event_rejects_client_from_another_tenant(db_session):
    tenant, client = create_tenant_and_client(db_session)
    _, other_client = create_tenant_and_client(
        db_session,
        name="Other Client",
    )
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = create_event(
            tenant_db,
            data=event_data(client.id),
        )

        with pytest.raises(EventClientNotFoundError):
            update_event(
                tenant_db,
                event_id=event.id,
                data={"client_id": other_client.id},
            )
    finally:
        tenant_db.close()


@pytest.mark.parametrize(
    ("initial_status", "new_status"),
    [
        ("draft", "confirmed"),
        ("confirmed", "in_progress"),
        ("in_progress", "completed"),
    ],
)
def test_update_event_allows_valid_status_transitions(
    db_session,
    initial_status,
    new_status,
):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = create_event(
            tenant_db,
            data=event_data(client.id, status=initial_status),
        )

        updated = update_event(
            tenant_db,
            event_id=event.id,
            data={"status": new_status},
        )

        assert updated.status == new_status
    finally:
        tenant_db.close()


@pytest.mark.parametrize(
    ("initial_status", "new_status"),
    [
        ("draft", "completed"),
        ("draft", "in_progress"),
        ("confirmed", "draft"),
        ("completed", "confirmed"),
        ("cancelled", "confirmed"),
    ],
)
def test_update_event_rejects_invalid_status_transitions(
    db_session,
    initial_status,
    new_status,
):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = create_event(
            tenant_db,
            data=event_data(client.id, status=initial_status),
        )

        with pytest.raises(InvalidEventDataError):
            update_event(
                tenant_db,
                event_id=event.id,
                data={"status": new_status},
            )
    finally:
        tenant_db.close()


@pytest.mark.parametrize(
    "initial_status",
    ["draft", "confirmed", "in_progress"],
)
def test_cancel_event(initial_status, db_session):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = create_event(
            tenant_db,
            data=event_data(client.id, status=initial_status),
        )

        cancelled = cancel_event(
            tenant_db,
            event_id=event.id,
        )

        assert cancelled.status == EventStatus.CANCELLED.value
    finally:
        tenant_db.close()


@pytest.mark.parametrize(
    "initial_status",
    ["completed", "cancelled"],
)
def test_cancel_event_rejects_final_statuses(
    initial_status,
    db_session,
):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = create_event(
            tenant_db,
            data=event_data(client.id, status=initial_status),
        )

        with pytest.raises(InvalidEventDataError):
            cancel_event(
                tenant_db,
                event_id=event.id,
            )
    finally:
        tenant_db.close()


def test_list_events_rejects_invalid_date_filters(db_session):
    tenant, _ = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(InvalidEventDataError):
            list_events(
                tenant_db,
                starts_at_from=datetime(2026, 12, 20, tzinfo=UTC),
                starts_at_to=datetime(2026, 12, 10, tzinfo=UTC),
            )
    finally:
        tenant_db.close()
