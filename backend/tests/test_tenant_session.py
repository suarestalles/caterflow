import pytest
from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.exc import IntegrityError

from app.db.tenant_session import TenantSession
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant


def create_tenant_session(db_session, tenant_id=None, platform_access=False):
    return TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant_id,
        platform_access=platform_access,
    )


def test_tenant_session_filters_other_tenants(db_session):
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")

    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()

    role_a = Role(
        tenant_id=tenant_a.id,
        name="Owner",
        is_system=True,
    )
    role_b = Role(
        tenant_id=tenant_b.id,
        name="Owner",
        is_system=True,
    )

    db_session.add_all([role_a, role_b])
    db_session.flush()

    tenant_session = create_tenant_session(
        db_session,
        tenant_id=tenant_a.id,
    )

    try:
        roles = tenant_session.scalars(select(Role)).all()

        assert [role.id for role in roles] == [role_a.id]
        assert all(role.tenant_id == tenant_a.id for role in roles)
    finally:
        tenant_session.close()


def test_tenant_session_assigns_tenant_id_automatically(db_session):
    tenant = Tenant(name="Tenant Automatic")
    db_session.add(tenant)
    db_session.flush()

    tenant_session = create_tenant_session(
        db_session,
        tenant_id=tenant.id,
    )

    try:
        role = Role(
            name="Manager",
            is_system=False,
        )

        tenant_session.add(role)
        tenant_session.flush()

        assert role.tenant_id == tenant.id
    finally:
        tenant_session.close()


def test_tenant_session_requires_tenant_context(db_session):
    tenant_session = create_tenant_session(db_session)

    try:
        with pytest.raises(
            PermissionError,
            match="Tenant context is required",
        ):
            tenant_session.scalars(select(Role)).all()
    finally:
        tenant_session.close()


def test_tenant_session_rejects_cross_tenant_insert(db_session):
    tenant_a = Tenant(name="Tenant Insert A")
    tenant_b = Tenant(name="Tenant Insert B")

    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()

    tenant_session = create_tenant_session(
        db_session,
        tenant_id=tenant_a.id,
    )

    try:
        role = Role(
            tenant_id=tenant_b.id,
            name="Unauthorized",
            is_system=False,
        )

        tenant_session.add(role)

        with pytest.raises(
            PermissionError,
            match="Cannot create a record for another tenant",
        ):
            tenant_session.flush()
    finally:
        tenant_session.close()


def test_tenant_session_blocks_bulk_update_of_other_tenant(db_session):
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")

    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()

    role_b = Role(
        tenant_id=tenant_b.id,
        name="Role B",
        is_system=False,
    )
    db_session.add(role_b)
    db_session.flush()

    with create_tenant_session(
        db_session,
        tenant_id=tenant_a.id,
    ) as tenant_db:
        result = tenant_db.execute(
            update(Role).where(Role.id == role_b.id).values(name="Modified by Tenant A")
        )

        assert result.rowcount == 0

    db_session.expire_all()

    persisted_role = db_session.get(Role, role_b.id)
    assert persisted_role.name == "Role B"


def test_tenant_session_blocks_bulk_delete_of_other_tenant(db_session):
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")

    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()

    role_b = Role(
        tenant_id=tenant_b.id,
        name="Role B",
        is_system=False,
    )
    db_session.add(role_b)
    db_session.flush()

    with create_tenant_session(
        db_session,
        tenant_id=tenant_a.id,
    ) as tenant_db:
        result = tenant_db.execute(delete(Role).where(Role.id == role_b.id))

        assert result.rowcount == 0

    db_session.expire_all()

    persisted_role = db_session.get(Role, role_b.id)
    assert persisted_role is not None
    assert persisted_role.name == "Role B"


def test_tenant_session_blocks_cross_tenant_object_update(db_session):
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")

    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()

    role_b = Role(
        tenant_id=tenant_b.id,
        name="Role B",
        is_system=False,
    )
    db_session.add(role_b)
    db_session.flush()

    role_id = role_b.id

    # Remove o objeto da sessão original.
    db_session.expunge(role_b)

    with create_tenant_session(
        db_session,
        tenant_id=tenant_a.id,
    ) as tenant_db:
        tenant_db.add(role_b)
        role_b.name = "Modified by Tenant A"

        with pytest.raises(
            PermissionError,
            match="Cannot modify or delete another tenant's records.",
        ):
            tenant_db.flush()

    db_session.expire_all()

    persisted_role = db_session.get(Role, role_id)
    assert persisted_role.name == "Role B"


def test_tenant_session_blocks_cross_tenant_object_delete(db_session):
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")

    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()

    role_b = Role(
        tenant_id=tenant_b.id,
        name="Role B",
        is_system=False,
    )
    db_session.add(role_b)
    db_session.flush()

    role_id = role_b.id

    # Remove o objeto da sessão original.
    db_session.expunge(role_b)

    with create_tenant_session(
        db_session,
        tenant_id=tenant_a.id,
    ) as tenant_db:
        tenant_db.add(role_b)
        tenant_db.delete(role_b)

        with pytest.raises(
            PermissionError,
            match="Cannot modify or delete another tenant's records.",
        ):
            tenant_db.flush()

    db_session.expire_all()

    persisted_role = db_session.get(Role, role_id)
    assert persisted_role is not None
    assert persisted_role.name == "Role B"


def test_tenant_session_rejects_cross_tenant_role_permission(db_session):
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")

    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()

    role_b = Role(
        tenant_id=tenant_b.id,
        name="Role B",
        is_system=False,
    )

    permission = Permission(
        code="test.cross_tenant_permission",
        description="Cross-tenant test permission",
    )

    db_session.add_all([role_b, permission])
    db_session.flush()

    with create_tenant_session(
        db_session,
        tenant_id=tenant_a.id,
    ) as tenant_db:
        role_permission = RolePermission(
            tenant_id=tenant_a.id,
            role_id=role_b.id,
            permission_id=permission.id,
        )

        tenant_db.add(role_permission)

        with pytest.raises(IntegrityError):
            tenant_db.flush()


def test_tenant_session_rejects_core_statement(db_session):
    tenant = Tenant(name="Tenant A")
    db_session.add(tenant)
    db_session.flush()

    with create_tenant_session(
        db_session,
        tenant_id=tenant.id,
    ) as tenant_db:
        with pytest.raises(
            PermissionError,
            match="Tenant sessions only allow ORM statements.",
        ):
            tenant_db.execute(update(Role.__table__).values(name="Unauthorized"))


def test_tenant_session_rejects_text_statement(db_session):
    tenant = Tenant(name="Tenant A")
    db_session.add(tenant)
    db_session.flush()

    with create_tenant_session(
        db_session,
        tenant_id=tenant.id,
    ) as tenant_db:
        with pytest.raises(
            PermissionError,
            match="Tenant sessions only allow ORM statements.",
        ):
            tenant_db.execute(text("SELECT 1"))


def test_tenant_session_rejects_bulk_insert(db_session):
    tenant = Tenant(name="Tenant A")
    db_session.add(tenant)
    db_session.flush()

    with create_tenant_session(
        db_session,
        tenant_id=tenant.id,
    ) as tenant_db:
        with pytest.raises(
            PermissionError,
            match="Bulk INSERT is not allowed in tenant sessions.",
        ):
            tenant_db.execute(
                insert(Role).values(
                    tenant_id=tenant.id,
                    name="Bulk Role",
                    is_system=False,
                )
            )
