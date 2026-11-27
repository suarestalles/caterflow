
from sqlalchemy import select

from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.platform_admin import PlatformAdmin
from app.models.role import Role
from app.models.user import User
from app.services.platform_users import (
    PlatformUserValidationError,
    create_user,
    deactivate_user,
    update_user,
)


def assign_owner_role(db_session, tenant, user):
    membership = db_session.scalar(
        select(Membership).where(
            Membership.tenant_id == tenant.id,
            Membership.user_id == user.id,
        )
    )

    if membership is None:
        membership = Membership(
            tenant_id=tenant.id,
            user_id=user.id,
        )
        db_session.add(membership)
        db_session.flush()

    owner_role = db_session.scalar(
        select(Role).where(
            Role.tenant_id == tenant.id,
            Role.name == "Owner",
        )
    )

    db_session.add(
        MembershipRole(
            tenant_id=tenant.id,
            membership_id=membership.id,
            role_id=owner_role.id,
        )
    )

    db_session.flush()
    return membership


def test_create_user_with_multiple_tenants(
    db_session,
    tenant_factory,
):
    tenant_a = tenant_factory(name="Company A")
    tenant_b = tenant_factory(name="Company B")

    result = create_user(
        db_session,
        full_name="Multi Tenant User",
        email="multi@example.com",
        password="StrongPassword123!",
        is_platform_admin=False,
        tenant_ids=[tenant_a.id, tenant_b.id],
    )

    assert result["full_name"] == "Multi Tenant User"
    assert result["is_platform_admin"] is False
    assert {tenant["id"] for tenant in result["tenants"]} == {
        tenant_a.id,
        tenant_b.id,
    }


def test_create_platform_admin_without_tenant(
    db_session,
):
    result = create_user(
        db_session,
        full_name="Platform Only",
        email="platform-only@example.com",
        password="StrongPassword123!",
        is_platform_admin=True,
        tenant_ids=[],
    )

    user = db_session.get(User, result["id"])

    platform_admin = db_session.scalar(
        select(PlatformAdmin).where(
            PlatformAdmin.user_id == user.id
        )
    )

    assert result["is_platform_admin"] is True
    assert result["tenants"] == []
    assert platform_admin is not None
    assert platform_admin.revoked_at is None


def test_update_user_replaces_tenant_memberships(
    db_session,
    tenant_factory,
):
    tenant_a = tenant_factory(name="Company A")
    tenant_b = tenant_factory(name="Company B")

    result = create_user(
        db_session,
        full_name="Tenant User",
        email="tenant-user@example.com",
        password="StrongPassword123!",
        is_platform_admin=False,
        tenant_ids=[tenant_a.id],
    )

    updated = update_user(
        db_session,
        user_id=result["id"],
        current_admin_id=None,
        tenant_ids=[tenant_b.id],
    )

    assert {tenant["id"] for tenant in updated["tenants"]} == {
        tenant_b.id,
    }


def test_update_user_rejects_removing_all_access(
    db_session,
    tenant_factory,
):
    tenant = tenant_factory()

    result = create_user(
        db_session,
        full_name="Tenant User",
        email="access-user@example.com",
        password="StrongPassword123!",
        is_platform_admin=False,
        tenant_ids=[tenant.id],
    )

    try:
        update_user(
            db_session,
            user_id=result["id"],
            current_admin_id=None,
            is_platform_admin=False,
            tenant_ids=[],
        )
        assert False, "Expected PlatformUserValidationError"
    except PlatformUserValidationError:
        pass


def test_deactivate_user_rejects_last_owner(
    db_session,
    user_factory,
    tenant_factory,
    membership_factory,
):
    owner = user_factory(email="last-owner@example.com")
    current_admin = user_factory(email="admin@example.com")

    tenant = tenant_factory()
    membership_factory(tenant, owner)
    assign_owner_role(db_session, tenant, owner)

    try:
        deactivate_user(
            db_session,
            owner.id,
            current_admin.id,
        )
        assert False, "Expected PlatformUserValidationError"
    except PlatformUserValidationError:
        pass

    db_session.refresh(owner)
    assert owner.is_active is True


def test_deactivate_user_allows_owner_when_another_owner_exists(
    db_session,
    user_factory,
    tenant_factory,
    membership_factory,
):
    owner_a = user_factory(email="owner-a@example.com")
    owner_b = user_factory(email="owner-b@example.com")
    current_admin = user_factory(email="admin@example.com")

    tenant = tenant_factory()

    membership_factory(tenant, owner_a)
    membership_factory(tenant, owner_b)

    assign_owner_role(db_session, tenant, owner_a)
    assign_owner_role(db_session, tenant, owner_b)

    result = deactivate_user(
        db_session,
        owner_a.id,
        current_admin.id,
    )

    assert result["is_active"] is False

    db_session.refresh(owner_b)
    assert owner_b.is_active is True
