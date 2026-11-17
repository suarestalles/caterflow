from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.tenant_session import TenantSession
from app.models.client import Client
from app.models.tenant import Tenant
from app.repositories import clients as client_repository


def create_tenant_session(
    db_session: Session,
    tenant_id=None,
) -> TenantSession:
    return TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant_id,
    )


def create_client_data(**overrides) -> dict:
    data = {
        "client_type": "individual",
        "name": "Maria Silva",
        "email": "maria@example.com",
        "phone": None,
        "country": "ES",
    }
    data.update(overrides)
    return data


def create_tenant(db_session: Session, name: str) -> Tenant:
    tenant = Tenant(name=name)
    db_session.add(tenant)
    db_session.flush()
    return tenant


def test_create_client(db_session):
    tenant = create_tenant(db_session, "Clients Test Tenant")

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        client = client_repository.create_client(
            tenant_db,
            data=create_client_data(),
        )

        assert client.id is not None
        assert client.tenant_id == tenant.id
        assert client.name == "Maria Silva"
        assert client.email == "maria@example.com"
        assert client.client_type == "individual"


def test_get_client_by_id(db_session):
    tenant = create_tenant(db_session, "Clients Get Tenant")

    client = Client(
        tenant_id=tenant.id,
        **create_client_data(),
    )
    db_session.add(client)
    db_session.flush()

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        result = client_repository.get_client_by_id(
            tenant_db,
            client.id,
        )

        assert result is not None
        assert result.id == client.id
        assert result.name == client.name


def test_get_client_by_id_returns_none_for_other_tenant(db_session):
    tenant_a = create_tenant(db_session, "Clients Tenant A")
    tenant_b = create_tenant(db_session, "Clients Tenant B")

    client_b = Client(
        tenant_id=tenant_b.id,
        **create_client_data(name="Client B"),
    )
    db_session.add(client_b)
    db_session.flush()

    with create_tenant_session(db_session, tenant_a.id) as tenant_db:
        result = client_repository.get_client_by_id(
            tenant_db,
            client_b.id,
        )

        assert result is None


def test_list_clients_returns_only_active_clients(db_session):
    tenant = create_tenant(db_session, "Clients List Tenant")

    active_client = Client(
        tenant_id=tenant.id,
        **create_client_data(name="Active Client"),
    )
    archived_client = Client(
        tenant_id=tenant.id,
        **create_client_data(
            name="Archived Client",
            email=None,
            phone="+34600000000",
            archived_at=datetime.now(UTC),
        ),
    )

    db_session.add_all([active_client, archived_client])
    db_session.flush()

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        clients, total = client_repository.list_clients(tenant_db)

        assert total == 1
        assert len(clients) == 1
        assert clients[0].id == active_client.id


def test_list_clients_applies_pagination(db_session):
    tenant = create_tenant(db_session, "Clients Pagination Tenant")

    db_session.add_all(
        [
            Client(
                tenant_id=tenant.id,
                **create_client_data(name="Client A"),
            ),
            Client(
                tenant_id=tenant.id,
                **create_client_data(
                    name="Client B",
                    email="clientb@example.com",
                ),
            ),
            Client(
                tenant_id=tenant.id,
                **create_client_data(
                    name="Client C",
                    email="clientc@example.com",
                ),
            ),
        ]
    )
    db_session.flush()

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        clients, total = client_repository.list_clients(
            tenant_db,
            offset=1,
            limit=1,
        )

        assert total == 3
        assert len(clients) == 1
        assert clients[0].name == "Client B"


def test_list_clients_searches_by_name(db_session):
    tenant = create_tenant(db_session, "Clients Search Name Tenant")

    db_session.add_all(
        [
            Client(
                tenant_id=tenant.id,
                **create_client_data(name="Maria Silva"),
            ),
            Client(
                tenant_id=tenant.id,
                **create_client_data(
                    name="João Santos",
                    email="joao@example.com",
                ),
            ),
        ]
    )
    db_session.flush()

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        clients, total = client_repository.list_clients(
            tenant_db,
            search="maria",
        )

        assert total == 1
        assert clients[0].name == "Maria Silva"


def test_list_clients_searches_by_email(db_session):
    tenant = create_tenant(db_session, "Clients Search Email Tenant")

    db_session.add(
        Client(
            tenant_id=tenant.id,
            **create_client_data(),
        )
    )
    db_session.flush()

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        clients, total = client_repository.list_clients(
            tenant_db,
            search="maria@example.com",
        )

        assert total == 1
        assert clients[0].email == "maria@example.com"


def test_list_clients_searches_by_phone(db_session):
    tenant = create_tenant(db_session, "Clients Search Phone Tenant")

    db_session.add(
        Client(
            tenant_id=tenant.id,
            **create_client_data(
                email=None,
                phone="+34600123456",
            ),
        )
    )
    db_session.flush()

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        clients, total = client_repository.list_clients(
            tenant_db,
            search="+34600123456",
        )

        assert total == 1
        assert clients[0].phone == "+34600123456"


def test_list_clients_isolates_tenants(db_session):
    tenant_a = create_tenant(db_session, "Clients Isolation A")
    tenant_b = create_tenant(db_session, "Clients Isolation B")

    client_a = Client(
        tenant_id=tenant_a.id,
        **create_client_data(name="Client A"),
    )
    client_b = Client(
        tenant_id=tenant_b.id,
        **create_client_data(name="Client B"),
    )

    db_session.add_all([client_a, client_b])
    db_session.flush()

    with create_tenant_session(db_session, tenant_a.id) as tenant_db:
        clients, total = client_repository.list_clients(tenant_db)

        assert total == 1
        assert len(clients) == 1
        assert clients[0].id == client_a.id
        assert clients[0].tenant_id == tenant_a.id


def test_archive_client(db_session):
    tenant = create_tenant(db_session, "Clients Archive Tenant")

    client = Client(
        tenant_id=tenant.id,
        **create_client_data(),
    )
    db_session.add(client)
    db_session.flush()

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        archived_at = datetime.now(UTC)

        result = client_repository.archive_client(
            tenant_db,
            client=client_repository.get_client_by_id(
                tenant_db,
                client.id,
            ),
            archived_at=archived_at,
        )

        assert result.archived_at == archived_at

        clients, total = client_repository.list_clients(tenant_db)

        assert total == 0
        assert clients == []
