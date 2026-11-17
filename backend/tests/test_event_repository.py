
from datetime import UTC, datetime, timedelta

from app.db.tenant_session import TenantSession
from app.models.client import Client
from app.models.event import EventStatus
from app.models.tenant import Tenant
from app.repositories import events as event_repository


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
        event = event_repository.create_event(
            tenant_db,
            data=event_data(client.id),
        )

        assert event.id is not None
        assert event.tenant_id == tenant.id
        assert event.client_id == client.id
        assert event.name == "Corporate Event"
        assert event.status == EventStatus.DRAFT.value
    finally:
        tenant_db.close()


def test_get_event_by_id(db_session):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = event_repository.create_event(
            tenant_db,
            data=event_data(client.id),
        )

        result = event_repository.get_event_by_id(
            tenant_db,
            event_id=event.id,
        )

        assert result is not None
        assert result.id == event.id
    finally:
        tenant_db.close()


def test_get_event_by_id_returns_none_for_another_tenant(db_session):
    tenant, client = create_tenant_and_client(db_session)
    other_tenant, _ = create_tenant_and_client(
        db_session,
        name="Other Client",
    )

    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = event_repository.create_event(
            tenant_db,
            data=event_data(client.id),
        )

        other_tenant_db = create_tenant_session(
            db_session,
            other_tenant.id,
        )

        try:
            result = event_repository.get_event_by_id(
                other_tenant_db,
                event_id=event.id,
            )
            assert result is None
        finally:
            other_tenant_db.close()
    finally:
        tenant_db.close()



def test_list_events_returns_only_current_tenant_events(db_session):
    tenant, client = create_tenant_and_client(db_session)

    other_tenant, other_client = create_tenant_and_client(
        db_session,
        name="Other Client",
    )

    first_tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        first_event = event_repository.create_event(
            first_tenant_db,
            data=event_data(client.id),
        )
        first_event_id = first_event.id

        first_tenant_db.commit()
    finally:
        first_tenant_db.close()

    second_tenant_db = create_tenant_session(
        db_session,
        other_tenant.id,
    )

    try:
        event_repository.create_event(
            second_tenant_db,
            data=event_data(
                other_client.id,
                name="Other Tenant Event",
            ),
        )

        second_tenant_db.commit()
    finally:
        second_tenant_db.close()

    first_tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        items, total = event_repository.list_events(first_tenant_db)

        assert total == 1
        assert len(items) == 1
        assert items[0].id == first_event_id
        assert items[0].tenant_id == tenant.id

    finally:
        first_tenant_db.close()



def test_list_events_applies_pagination(db_session):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        for index in range(3):
            event_repository.create_event(
                tenant_db,
                data=event_data(
                    client.id,
                    name=f"Event {index}",
                ),
            )

        items, total = event_repository.list_events(
            tenant_db,
            offset=1,
            limit=1,
        )

        assert total == 3
        assert len(items) == 1
    finally:
        tenant_db.close()


def test_list_events_filters_by_name(db_session):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event_repository.create_event(
            tenant_db,
            data=event_data(client.id, name="Wedding Reception"),
        )
        event_repository.create_event(
            tenant_db,
            data=event_data(client.id, name="Corporate Meeting"),
        )

        items, total = event_repository.list_events(
            tenant_db,
            search="Wedding",
        )

        assert total == 1
        assert items[0].name == "Wedding Reception"
    finally:
        tenant_db.close()

def test_list_events_filters_by_client_and_status(db_session):
    tenant, client = create_tenant_and_client(db_session)

    other_client = Client(
        tenant_id=tenant.id,
        name="Second Client",
        email="second.client@example.com",
    )
    db_session.add(other_client)
    db_session.flush()

    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event_repository.create_event(
            tenant_db,
            data=event_data(
                client.id,
                status=EventStatus.CONFIRMED.value,
            ),
        )
        event_repository.create_event(
            tenant_db,
            data=event_data(
                other_client.id,
                status=EventStatus.DRAFT.value,
                name="Second Event",
            ),
        )

        items, total = event_repository.list_events(
            tenant_db,
            client_id=client.id,
        )

        assert total == 1
        assert len(items) == 1
        assert items[0].client_id == client.id

        items, total = event_repository.list_events(
            tenant_db,
            status=EventStatus.DRAFT.value,
        )

        assert total == 1
        assert len(items) == 1
        assert items[0].name == "Second Event"

    finally:
        tenant_db.close()



def test_list_events_filters_by_start_date(db_session):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event_repository.create_event(
            tenant_db,
            data=event_data(
                client.id,
                starts_at=datetime(2026, 12, 10, 18, tzinfo=UTC),
                ends_at=datetime(2026, 12, 10, 23, tzinfo=UTC),
            ),
        )
        event_repository.create_event(
            tenant_db,
            data=event_data(
                client.id,
                starts_at=datetime(2026, 12, 20, 18, tzinfo=UTC),
                ends_at=datetime(2026, 12, 20, 23, tzinfo=UTC),
            ),
        )

        items, total = event_repository.list_events(
            tenant_db,
            starts_at_from=datetime(2026, 12, 15, tzinfo=UTC),
        )

        assert total == 1
        assert items[0].starts_at.day == 20
    finally:
        tenant_db.close()


def test_update_event(db_session):
    tenant, client = create_tenant_and_client(db_session)
    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        event = event_repository.create_event(
            tenant_db,
            data=event_data(client.id),
        )

        updated = event_repository.update_event(
            tenant_db,
            event=event,
            data={"name": "Updated Event"},
        )

        assert updated.name == "Updated Event"
    finally:
        tenant_db.close()
