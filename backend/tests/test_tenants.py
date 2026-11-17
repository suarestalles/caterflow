import pytest
from sqlalchemy import func, select

from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.models.membership_role import MembershipRole
from app.models.platform_admin import PlatformAdmin
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.services.tenants import create_initial_tenant


def test_create_initial_tenant_creates_platform_admin_and_tenant(
    db_session,
):
    result = create_initial_tenant(
        db_session,
        full_name="Platform Administrator",
        email="platform-bootstrap@test.com",
        password_hash="test-password-hash",
        tenant_name="First CaterFlow Tenant",
    )

    assert result.user.full_name == "Platform Administrator"
    assert result.user.email == "platform-bootstrap@test.com"
    assert result.user.is_active is True

    assert result.tenant.name == "First CaterFlow Tenant"

    assert result.platform_admin.user_id == result.user.id
    assert result.membership.user_id == result.user.id
    assert result.membership.tenant_id == result.tenant.id


def test_create_initial_tenant_provisions_default_roles(
    db_session,
):
    result = create_initial_tenant(
        db_session,
        full_name="Platform Administrator",
        email="roles-bootstrap@test.com",
        password_hash="test-password-hash",
        tenant_name="Roles Bootstrap Tenant",
    )

    roles = db_session.scalars(select(Role).where(Role.tenant_id == result.tenant.id)).all()

    roles_by_name = {role.name: role for role in roles}

    assert set(roles_by_name) == set(DEFAULT_ROLE_PERMISSIONS)

    assert all(role.is_system for role in roles)


def test_create_initial_tenant_assigns_membership_to_owner(
    db_session,
):
    result = create_initial_tenant(
        db_session,
        full_name="Platform Administrator",
        email="owner-bootstrap@test.com",
        password_hash="test-password-hash",
        tenant_name="Owner Bootstrap Tenant",
    )

    owner_role = db_session.scalar(
        select(Role).where(
            Role.tenant_id == result.tenant.id,
            Role.name == "Owner",
        )
    )

    membership_role = db_session.scalar(
        select(MembershipRole).where(
            MembershipRole.tenant_id == result.tenant.id,
            MembershipRole.membership_id == result.membership.id,
            MembershipRole.role_id == owner_role.id,
        )
    )

    assert membership_role is not None


def test_create_initial_tenant_grants_all_permissions_to_owner(
    db_session,
):
    result = create_initial_tenant(
        db_session,
        full_name="Platform Administrator",
        email="permissions-bootstrap@test.com",
        password_hash="test-password-hash",
        tenant_name="Permissions Bootstrap Tenant",
    )

    owner_role = db_session.scalar(
        select(Role).where(
            Role.tenant_id == result.tenant.id,
            Role.name == "Owner",
        )
    )

    permission_count = db_session.scalar(
        select(func.count(RolePermission.id)).where(
            RolePermission.tenant_id == result.tenant.id,
            RolePermission.role_id == owner_role.id,
        )
    )

    assert permission_count == len(DEFAULT_ROLE_PERMISSIONS["Owner"])


def test_create_initial_tenant_rejects_existing_platform_admin(
    db_session,
):
    user = User(
        full_name="Existing Administrator",
        email="existing-platform@test.com",
        password_hash="test-password-hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    db_session.add(PlatformAdmin(user_id=user.id))
    db_session.flush()

    with pytest.raises(
        RuntimeError,
        match="Platform bootstrap has already been completed.",
    ):
        create_initial_tenant(
            db_session,
            full_name="Another Administrator",
            email="another-platform@test.com",
            password_hash="test-password-hash",
            tenant_name="Another Tenant",
        )


def test_create_initial_tenant_rejects_existing_user(
    db_session,
):
    user = User(
        full_name="Existing User",
        email="existing-user@test.com",
        password_hash="test-password-hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    with pytest.raises(
        ValueError,
        match="A user with this email already exists.",
    ):
        create_initial_tenant(
            db_session,
            full_name="Another Administrator",
            email="existing-user@test.com",
            password_hash="test-password-hash",
            tenant_name="Another Tenant",
        )
