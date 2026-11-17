from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.db.tenant_session import TenantSession
from app.models.client import Client
from app.models.tenant import Tenant
from app.services import clients as client_service
from app.services.clients import (
    ClientNotFoundError,
    InvalidClientDataError,
)


def create_tenant_session(
    db_session: Session,
    tenant_id=None,
) -> TenantSession:
    return TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant_id,
    )


def create_tenant(db_session: Session) -> Tenant:
    tenant = Tenant(name="Client Service Test Tenant")
    db_session.add(tenant)
    db_session.flush()
    return tenant


def create_client(
    db_session: Session,
    tenant_id,
    **overrides,
) -> Client:
    data = {
        "client_type": "individual",
        "name": "Maria Silva",
        "email": "maria@example.com",
        "phone": None,
        "country": "ES",
    }
    data.update(overrides)

    client = Client(
        tenant_id=tenant_id,
        **data,
    )

    db_session.add(client)
    db_session.flush()

    return client


# ============================================================
# CREATE CLIENT
# ============================================================


def test_create_client_service(db_session):
    tenant = create_tenant(db_session)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        client = client_service.create_client(
            tenant_db,
            data={
                "client_type": "individual",
                "name": "Maria Silva",
                "email": "maria@example.com",
                "country": "ES",
            },
        )

        assert client.id is not None
        assert client.tenant_id == tenant.id
        assert client.name == "Maria Silva"
        assert client.email == "maria@example.com"
        assert client.client_type == "individual"


def test_create_company_client_service(db_session):
    tenant = create_tenant(db_session)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        client = client_service.create_client(
            tenant_db,
            data={
                "client_type": "company",
                "name": "Empresa Exemplo SL",
                "contact_person": "João Silva",
                "phone": "+34600123456",
                "country": "ES",
            },
        )

        assert client.client_type == "company"
        assert client.name == "Empresa Exemplo SL"
        assert client.contact_person == "João Silva"
        assert client.phone == "+34600123456"


def test_create_client_without_contact_fails(db_session):
    tenant = create_tenant(db_session)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(
            InvalidClientDataError,
            match="At least one contact method",
        ):
            client_service.create_client(
                tenant_db,
                data={
                    "client_type": "individual",
                    "name": "Maria Silva",
                    "email": None,
                    "phone": None,
                    "country": "ES",
                },
            )


def test_create_client_with_phone_only_succeeds(db_session):
    tenant = create_tenant(db_session)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        client = client_service.create_client(
            tenant_db,
            data={
                "client_type": "individual",
                "name": "João Silva",
                "email": None,
                "phone": "+34600123456",
                "country": "ES",
            },
        )

        assert client.email is None
        assert client.phone == "+34600123456"


# ============================================================
# GET CLIENT
# ============================================================


def test_get_client_service(db_session):
    tenant = create_tenant(db_session)
    client = create_client(db_session, tenant.id)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        result = client_service.get_client(
            tenant_db,
            client_id=client.id,
        )

        assert result.id == client.id
        assert result.name == "Maria Silva"


def test_get_nonexistent_client_fails(db_session):
    tenant = create_tenant(db_session)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(ClientNotFoundError):
            client_service.get_client(
                tenant_db,
                client_id=uuid4(),
            )


def test_get_client_from_another_tenant_fails(db_session):
    tenant_a = create_tenant(db_session)
    tenant_b = Tenant(name="Another Client Tenant")
    db_session.add(tenant_b)
    db_session.flush()

    client_b = create_client(
        db_session,
        tenant_b.id,
        name="Client B",
    )

    with create_tenant_session(db_session, tenant_a.id) as tenant_db:
        with pytest.raises(ClientNotFoundError):
            client_service.get_client(
                tenant_db,
                client_id=client_b.id,
            )


def test_get_archived_client_fails(db_session):
    tenant = create_tenant(db_session)

    client = create_client(
        db_session,
        tenant.id,
        archived_at=datetime.now(UTC),
    )

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(ClientNotFoundError):
            client_service.get_client(
                tenant_db,
                client_id=client.id,
            )


# ============================================================
# LIST CLIENTS
# ============================================================


def test_list_clients_service(db_session):
    tenant = create_tenant(db_session)

    create_client(db_session, tenant.id, name="Maria Silva")
    create_client(
        db_session,
        tenant.id,
        name="João Santos",
        email="joao@example.com",
    )

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        clients, total = client_service.list_clients(tenant_db)

        assert total == 2
        assert len(clients) == 2


def test_list_clients_service_with_search(db_session):
    tenant = create_tenant(db_session)

    create_client(db_session, tenant.id, name="Maria Silva")
    create_client(
        db_session,
        tenant.id,
        name="João Santos",
        email="joao@example.com",
    )

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        clients, total = client_service.list_clients(
            tenant_db,
            search="Maria",
        )

        assert total == 1
        assert clients[0].name == "Maria Silva"


# ============================================================
# UPDATE CLIENT
# ============================================================


def test_update_client_service(db_session):
    tenant = create_tenant(db_session)
    client = create_client(db_session, tenant.id)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        updated_client = client_service.update_client(
            tenant_db,
            client_id=client.id,
            data={
                "name": "Maria Santos",
                "phone": "+34600123456",
            },
        )

        assert updated_client.name == "Maria Santos"
        assert updated_client.email == "maria@example.com"
        assert updated_client.phone == "+34600123456"


def test_update_client_preserves_existing_contact(db_session):
    tenant = create_tenant(db_session)

    client = create_client(
        db_session,
        tenant.id,
        email=None,
        phone="+34600123456",
    )

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        updated_client = client_service.update_client(
            tenant_db,
            client_id=client.id,
            data={
                "name": "Maria Atualizada",
            },
        )

        assert updated_client.name == "Maria Atualizada"
        assert updated_client.phone == "+34600123456"


def test_update_client_without_contact_fails(db_session):
    tenant = create_tenant(db_session)
    client = create_client(db_session, tenant.id)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(
            InvalidClientDataError,
            match="At least one contact method",
        ):
            client_service.update_client(
                tenant_db,
                client_id=client.id,
                data={
                    "email": None,
                    "phone": None,
                },
            )


@pytest.mark.parametrize(
    ("field", "expected_message"),
    [
        ("name", "Client name cannot be null."),
        ("client_type", "Client type cannot be null."),
        ("country", "Client country cannot be null."),
    ],
)
def test_update_client_rejects_null_required_fields(
    db_session,
    field,
    expected_message,
):
    tenant = create_tenant(db_session)
    client = create_client(db_session, tenant.id)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(
            InvalidClientDataError,
            match=expected_message,
        ):
            client_service.update_client(
                tenant_db,
                client_id=client.id,
                data={field: None},
            )


def test_update_nonexistent_client_fails(db_session):
    tenant = create_tenant(db_session)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(ClientNotFoundError):
            client_service.update_client(
                tenant_db,
                client_id=uuid4(),
                data={"name": "Updated Name"},
            )


def test_update_archived_client_fails(db_session):
    tenant = create_tenant(db_session)

    client = create_client(
        db_session,
        tenant.id,
        archived_at=datetime.now(UTC),
    )

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(ClientNotFoundError):
            client_service.update_client(
                tenant_db,
                client_id=client.id,
                data={"name": "Updated Name"},
            )


# ============================================================
# ARCHIVE CLIENT
# ============================================================


def test_archive_client_service(db_session):
    tenant = create_tenant(db_session)
    client = create_client(db_session, tenant.id)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        client_service.archive_client(
            tenant_db,
            client_id=client.id,
        )

        archived_client = tenant_db.get(Client, client.id)

        assert archived_client is not None
        assert archived_client.archived_at is not None


def test_archive_nonexistent_client_fails(db_session):
    tenant = create_tenant(db_session)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(ClientNotFoundError):
            client_service.archive_client(
                tenant_db,
                client_id=uuid4(),
            )


def test_archive_already_archived_client_fails(db_session):
    tenant = create_tenant(db_session)

    client = create_client(
        db_session,
        tenant.id,
        archived_at=datetime.now(UTC),
    )

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(ClientNotFoundError):
            client_service.archive_client(
                tenant_db,
                client_id=client.id,
            )
