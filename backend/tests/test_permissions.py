import pytest
from fastapi import HTTPException

from app.api.v1.deps import AuthContext, require_permission
from app.core.permissions import PermissionCode
from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.user import User
from app.services.permissions import get_effective_permissions

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

def get_or_create_permission(db_session, code: PermissionCode) -> Permission:
    permission = db_session.scalar(
        select(Permission).where(Permission.code == code.value)
    )

    if permission is None:
        permission = Permission(
            code=code.value,
            description=f"Test permission: {code.value}",
        )
        db_session.add(permission)
        db_session.flush()

    return permission


def create_authorization_context(db_session, tenant, email):
    user = User(
        full_name="Authorization Test User",
        email=email,
        password_hash="test-password-hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    membership = Membership(
        user_id=user.id,
        tenant_id=tenant.id,
    )
    db_session.add(membership)
    db_session.flush()

    return AuthContext(
        user=user,
        tenant_id=tenant.id,
    ), membership


def test_get_effective_permissions_returns_union_of_all_roles(db_session):
    tenant = Tenant(name="Permission Union Tenant")
    db_session.add(tenant)
    db_session.flush()

    auth, membership = create_authorization_context(
        db_session,
        tenant,
        "permission-union@example.com",
    )

    manager_role = Role(
        tenant_id=tenant.id,
        name="Manager",
        is_system=True,
    )
    finance_role = Role(
        tenant_id=tenant.id,
        name="Finance",
        is_system=False,
    )

    read_permission = get_or_create_permission(
        db_session,
        PermissionCode.EVENTS_READ,
    )
    create_permission = get_or_create_permission(
        db_session,
        PermissionCode.EVENTS_CREATE,
    )

    db_session.add_all(
        [
            manager_role,
            finance_role,
            read_permission,
            create_permission,
        ]
    )
    db_session.flush()

    db_session.add_all(
        [
            MembershipRole(
                tenant_id=tenant.id,
                membership_id=membership.id,
                role_id=manager_role.id,
            ),
            MembershipRole(
                tenant_id=tenant.id,
                membership_id=membership.id,
                role_id=finance_role.id,
            ),
            RolePermission(
                tenant_id=tenant.id,
                role_id=manager_role.id,
                permission_id=read_permission.id,
            ),
            RolePermission(
                tenant_id=tenant.id,
                role_id=finance_role.id,
                permission_id=create_permission.id,
            ),
        ]
    )
    db_session.flush()

    permissions = get_effective_permissions(
        db_session,
        membership.id,
        auth.tenant_id,
    )

    assert permissions == {
        PermissionCode.EVENTS_READ.value,
        PermissionCode.EVENTS_CREATE.value,
    }


def test_get_effective_permissions_does_not_leak_across_tenants(db_session):
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")
    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()

    auth, membership_a = create_authorization_context(
        db_session,
        tenant_a,
        "tenant-a@example.com",
    )

    _, membership_b = create_authorization_context(
        db_session,
        tenant_b,
        "tenant-b@example.com",
    )

    role_b = Role(
        tenant_id=tenant_b.id,
        name="Manager",
        is_system=True,
    )

    permission = get_or_create_permission(
        db_session,
        PermissionCode.EVENTS_CREATE,
    )

    db_session.add_all([role_b, permission])
    db_session.flush()

    db_session.add_all(
        [
            MembershipRole(
                tenant_id=tenant_b.id,
                membership_id=membership_b.id,
                role_id=role_b.id,
            ),
            RolePermission(
                tenant_id=tenant_b.id,
                role_id=role_b.id,
                permission_id=permission.id,
            ),
        ]
    )
    db_session.flush()

    permissions = get_effective_permissions(
        db_session,
        membership_a.id,
        auth.tenant_id,
    )

    assert permissions == set()


def test_require_permission_allows_authorized_user(db_session):
    tenant = Tenant(name="Authorized Tenant")
    db_session.add(tenant)
    db_session.flush()

    auth, membership = create_authorization_context(
        db_session,
        tenant,
        "authorized@example.com",
    )

    role = Role(
        tenant_id=tenant.id,
        name="Event Manager",
        is_system=False,
    )
    permission = get_or_create_permission(
        db_session,
        PermissionCode.EVENTS_CREATE,
    )

    db_session.add_all([role, permission])
    db_session.flush()

    db_session.add_all(
        [
            MembershipRole(
                tenant_id=tenant.id,
                membership_id=membership.id,
                role_id=role.id,
            ),
            RolePermission(
                tenant_id=tenant.id,
                role_id=role.id,
                permission_id=permission.id,
            ),
        ]
    )
    db_session.flush()

    dependency = require_permission(PermissionCode.EVENTS_CREATE)

    result = dependency(
        auth=auth,
        db=db_session,
    )

    assert result is None


def test_require_permission_rejects_unauthorized_user(db_session):
    tenant = Tenant(name="Unauthorized Tenant")
    db_session.add(tenant)
    db_session.flush()

    auth, _ = create_authorization_context(
        db_session,
        tenant,
        "unauthorized@example.com",
    )

    dependency = require_permission(PermissionCode.EVENTS_CREATE)

    with pytest.raises(HTTPException) as exc:
        dependency(
            auth=auth,
            db=db_session,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Insufficient permissions."
