from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.permissions import (
    DEFAULT_ROLE_PERMISSIONS,
    PermissionCode,
)
from app.db.tenant_session import TenantSession
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant
from app.services.roles import provision_default_roles


def create_tenant_session(
    db_session,
    tenant_id=None,
    platform_access=False,
):
    return TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant_id,
        platform_access=platform_access,
    )


def create_permission_catalog(db_session):
    """Ensure all permissions required by default roles exist."""
    for code in PermissionCode:
        permission = db_session.scalar(select(Permission).where(Permission.code == code.value))

        if permission is None:
            db_session.add(
                Permission(
                    code=code.value,
                    description=f"Test permission: {code.value}",
                )
            )

    db_session.flush()


def test_provision_default_roles_creates_system_roles(db_session):
    tenant = Tenant(name="Roles Provision Tenant")
    db_session.add(tenant)
    db_session.flush()

    create_permission_catalog(db_session)

    with create_tenant_session(
        db_session,
        tenant_id=tenant.id,
    ) as tenant_db:
        roles = provision_default_roles(tenant_db, tenant.id)

        assert set(roles) == set(DEFAULT_ROLE_PERMISSIONS)

        for role_name, role in roles.items():
            assert role.name == role_name
            assert role.is_system is True
            assert role.tenant_id == tenant.id


def test_provision_default_roles_assigns_expected_permissions(db_session):
    tenant = Tenant(name="Roles Permissions Tenant")
    db_session.add(tenant)
    db_session.flush()

    create_permission_catalog(db_session)

    with create_tenant_session(
        db_session,
        tenant_id=tenant.id,
    ) as tenant_db:
        roles = provision_default_roles(tenant_db, tenant.id)

        for role_name, role in roles.items():
            assigned_codes = set(
                tenant_db.scalars(
                    select(Permission.code)
                    .join(
                        RolePermission,
                        RolePermission.permission_id == Permission.id,
                    )
                    .where(RolePermission.role_id == role.id)
                ).all()
            )

            expected_codes = {code.value for code in DEFAULT_ROLE_PERMISSIONS[role_name]}

            assert assigned_codes == expected_codes


def test_provision_default_roles_is_idempotent(db_session):
    tenant = Tenant(name="Roles Idempotency Tenant")
    db_session.add(tenant)
    db_session.flush()

    create_permission_catalog(db_session)

    with create_tenant_session(
        db_session,
        tenant_id=tenant.id,
    ) as tenant_db:
        first_result = provision_default_roles(tenant_db, tenant.id)
        tenant_db.flush()

        first_role_ids = {name: role.id for name, role in first_result.items()}

        first_assignment_count = len(tenant_db.scalars(select(RolePermission.id)).all())

        second_result = provision_default_roles(tenant_db, tenant.id)
        tenant_db.flush()

        second_role_ids = {name: role.id for name, role in second_result.items()}

        second_assignment_count = len(tenant_db.scalars(select(RolePermission.id)).all())

        assert first_role_ids == second_role_ids
        assert first_assignment_count == second_assignment_count


def test_provision_default_roles_preserves_custom_roles(db_session):
    tenant = Tenant(name="Roles Custom Tenant")

    db_session.add(tenant)
    db_session.flush()

    custom_role = Role(
        tenant_id=tenant.id,
        name="Kitchen Supervisor",
        description="Custom kitchen supervisor role.",
        is_system=False,
    )

    db_session.add(custom_role)
    db_session.flush()

    custom_role_id = custom_role.id

    create_permission_catalog(db_session)

    with create_tenant_session(
        db_session,
        tenant_id=tenant.id,
    ) as tenant_db:
        roles = provision_default_roles(tenant_db, tenant.id)

        persisted_custom_role = tenant_db.scalar(
            select(Role).where(Role.name == "Kitchen Supervisor")
        )

        assert persisted_custom_role is not None
        assert persisted_custom_role.id == custom_role_id
        assert persisted_custom_role.is_system is False
        assert "Kitchen Supervisor" not in roles


def test_provision_default_roles_rejects_different_tenant(db_session):
    tenant_a = Tenant(name="Roles Tenant A")
    tenant_b = Tenant(name="Roles Tenant B")

    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()

    with create_tenant_session(
        db_session,
        tenant_id=tenant_a.id,
    ) as tenant_db:
        with pytest.raises(
            PermissionError,
            match="A matching tenant-scoped session is required.",
        ):
            provision_default_roles(tenant_db, tenant_b.id)


def test_provision_default_roles_rejects_platform_session(db_session):
    tenant = Tenant(name="Roles Platform Tenant")
    db_session.add(tenant)
    db_session.flush()

    with create_tenant_session(
        db_session,
        platform_access=True,
    ) as platform_db:
        with pytest.raises(
            PermissionError,
            match="A matching tenant-scoped session is required.",
        ):
            provision_default_roles(platform_db, tenant.id)


def test_provision_default_roles_requires_complete_catalog():
    tenant_id = uuid4()

    fake_db = MagicMock()
    fake_db.platform_access = False
    fake_db.tenant_id = tenant_id
    fake_db.scalars.return_value.all.return_value = []

    with pytest.raises(
        RuntimeError,
        match="Permission catalog is missing required codes",
    ):
        provision_default_roles(fake_db, tenant_id)
