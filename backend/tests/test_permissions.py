from sqlalchemy import select

from app.core.permissions import PERMISSION_CATALOG
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant
from app.services.permissions import (
    sync_permission_catalog,
    sync_permissions,
)


def test_sync_permission_catalog_inserts_all_permissions(db_session):
    sync_permission_catalog(db_session)

    permission_codes = [permission.code.value for permission in PERMISSION_CATALOG]

    permissions = db_session.scalars(
        select(Permission).where(Permission.code.in_(permission_codes))
    ).all()

    assert len(permissions) == len(PERMISSION_CATALOG)

    descriptions = {permission.code: permission.description for permission in permissions}

    for definition in PERMISSION_CATALOG:
        assert descriptions[definition.code.value] == definition.description


def test_sync_permissions_assigns_all_permissions_to_owners(db_session):
    tenant = Tenant(name="Test Catering Company")
    db_session.add(tenant)
    db_session.flush()

    owner_role = Role(
        tenant_id=tenant.id,
        name="Owner",
        is_system=True,
    )

    custom_role = Role(
        tenant_id=tenant.id,
        name="Custom Manager",
        is_system=False,
    )

    db_session.add_all([owner_role, custom_role])
    db_session.flush()

    sync_permissions(db_session)
    db_session.expire_all()

    owner_permissions = db_session.scalars(
        select(RolePermission).where(RolePermission.role_id == owner_role.id)
    ).all()

    custom_permissions = db_session.scalars(
        select(RolePermission).where(RolePermission.role_id == custom_role.id)
    ).all()

    assert len(owner_permissions) == len(PERMISSION_CATALOG)
    assert custom_permissions == []


def test_sync_permissions_is_idempotent(db_session):
    tenant = Tenant(name="Idempotency Test Company")
    db_session.add(tenant)
    db_session.flush()

    owner_role = Role(
        tenant_id=tenant.id,
        name="Owner",
        is_system=True,
    )

    db_session.add(owner_role)
    db_session.flush()

    sync_permissions(db_session)
    sync_permissions(db_session)

    db_session.expire_all()

    permission_codes = [permission.code.value for permission in PERMISSION_CATALOG]

    permissions = db_session.scalars(
        select(Permission).where(Permission.code.in_(permission_codes))
    ).all()

    owner_permissions = db_session.scalars(
        select(RolePermission).where(RolePermission.role_id == owner_role.id)
    ).all()

    assert len(permissions) == len(PERMISSION_CATALOG)
    assert len(owner_permissions) == len(PERMISSION_CATALOG)
