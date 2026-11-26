
import pytest

from app.models.user_action_token import UserActionToken
from app.services.tenant_invitations import (
    TenantInvitationConflictError,
    TenantInvitationValidationError,
    create_tenant_invitation,
    accept_tenant_invitation_for_existing_user,
    accept_tenant_invitation_for_new_user,
)
from app.services.user_action_tokens import (
    TENANT_INVITATION,
    get_valid_user_action_token,
)
from app.repositories.tenant_invitations import get_membership
from sqlalchemy import select

from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.user import User


def test_create_invitation_for_new_user(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant = tenant_factory()
    admin = user_factory()

    role = tenant.roles[0]

    raw_token, token_id = create_tenant_invitation(
        db=db_session,
        tenant_id=tenant.id,
        invited_by_user_id=admin.id,
        email="newuser@example.com",
        role_id=role.id,
    )

    token = db_session.get(UserActionToken, token_id)

    assert raw_token
    assert token is not None
    assert token.email == "newuser@example.com"
    assert token.user_id is None
    assert token.tenant_id == tenant.id
    assert token.role_id == role.id
    assert token.invited_by_user_id == admin.id
    assert token.purpose == TENANT_INVITATION
    assert token.token_hash != raw_token


def test_create_invitation_for_existing_user(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant = tenant_factory()
    admin = user_factory()
    invited_user = user_factory()

    raw_token, token_id = create_tenant_invitation(
        db=db_session,
        tenant_id=tenant.id,
        invited_by_user_id=admin.id,
        email=invited_user.email,
        role_id=tenant.roles[0].id,
    )

    token = db_session.get(UserActionToken, token_id)

    assert raw_token
    assert token.user_id == invited_user.id
    assert token.email == invited_user.email


def test_reject_invitation_for_existing_membership(
    db_session,
    tenant_factory,
    user_factory,
    membership_factory,
):
    tenant = tenant_factory()
    admin = user_factory()
    invited_user = user_factory()

    membership_factory(
        tenant=tenant,
        user=invited_user,
    )

    with pytest.raises(TenantInvitationConflictError):
        create_tenant_invitation(
            db=db_session,
            tenant_id=tenant.id,
            invited_by_user_id=admin.id,
            email=invited_user.email,
            role_id=tenant.roles[0].id,
        )


def test_reject_invitation_for_inactive_user(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant = tenant_factory()
    admin = user_factory()
    invited_user = user_factory(is_active=False)

    with pytest.raises(TenantInvitationValidationError):
        create_tenant_invitation(
            db=db_session,
            tenant_id=tenant.id,
            invited_by_user_id=admin.id,
            email=invited_user.email,
            role_id=tenant.roles[0].id,
        )


def test_reject_invitation_for_inactive_tenant(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant = tenant_factory(is_active=False)
    admin = user_factory()

    with pytest.raises(TenantInvitationValidationError):
        create_tenant_invitation(
            db=db_session,
            tenant_id=tenant.id,
            invited_by_user_id=admin.id,
            email="newuser@example.com",
            role_id=tenant.roles[0].id,
        )


def test_reject_role_from_another_tenant(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant = tenant_factory()
    another_tenant = tenant_factory()
    admin = user_factory()

    with pytest.raises(TenantInvitationValidationError):
        create_tenant_invitation(
            db=db_session,
            tenant_id=tenant.id,
            invited_by_user_id=admin.id,
            email="newuser@example.com",
            role_id=another_tenant.roles[0].id,
        )


def test_new_invitation_revokes_previous_pending_invitation(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant = tenant_factory()
    admin = user_factory()
    email = "newuser@example.com"

    first_raw_token, first_id = create_tenant_invitation(
        db=db_session,
        tenant_id=tenant.id,
        invited_by_user_id=admin.id,
        email=email,
        role_id=tenant.roles[0].id,
    )

    second_raw_token, second_id = create_tenant_invitation(
        db=db_session,
        tenant_id=tenant.id,
        invited_by_user_id=admin.id,
        email=email,
        role_id=tenant.roles[0].id,
    )

    first = db_session.get(UserActionToken, first_id)
    second = db_session.get(UserActionToken, second_id)

    assert first.used_at is not None
    assert second.used_at is None
    assert first_raw_token != second_raw_token

    with pytest.raises(Exception):
        get_valid_user_action_token(
            db_session,
            first_raw_token,
            TENANT_INVITATION,
        )

    assert get_valid_user_action_token(
        db_session,
        second_raw_token,
        TENANT_INVITATION,
    )


def test_same_email_can_be_invited_to_different_tenants(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant_one = tenant_factory()
    tenant_two = tenant_factory()
    admin = user_factory()
    email = "newuser@example.com"

    first_token, first_id = create_tenant_invitation(
        db=db_session,
        tenant_id=tenant_one.id,
        invited_by_user_id=admin.id,
        email=email,
        role_id=tenant_one.roles[0].id,
    )

    second_token, second_id = create_tenant_invitation(
        db=db_session,
        tenant_id=tenant_two.id,
        invited_by_user_id=admin.id,
        email=email,
        role_id=tenant_two.roles[0].id,
    )

    first = db_session.get(UserActionToken, first_id)
    second = db_session.get(UserActionToken, second_id)

    assert first.used_at is None
    assert second.used_at is None
    assert first.tenant_id != second.tenant_id
    assert first_token != second_token


def test_invitation_token_is_not_stored_in_plain_text(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant = tenant_factory()
    admin = user_factory()

    raw_token, token_id = create_tenant_invitation(
        db=db_session,
        tenant_id=tenant.id,
        invited_by_user_id=admin.id,
        email="newuser@example.com",
        role_id=tenant.roles[0].id,
    )

    token = db_session.get(UserActionToken, token_id)

    assert token.token_hash != raw_token
    assert len(token.token_hash) == 64


def test_invitation_failure_rolls_back(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant = tenant_factory()
    admin = user_factory()

    with pytest.raises(TenantInvitationValidationError):
        create_tenant_invitation(
            db=db_session,
            tenant_id=tenant.id,
            invited_by_user_id=admin.id,
            email="newuser@example.com",
            role_id=tenant_factory().roles[0].id,
        )

    pending = db_session.query(UserActionToken).filter(
        UserActionToken.tenant_id == tenant.id,
        UserActionToken.email == "newuser@example.com",
    ).all()

    assert pending == []

def test_accept_invitation_creates_new_user_and_membership(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant = tenant_factory()
    admin = user_factory()
    role = tenant.roles[0]

    raw_token, _ = create_tenant_invitation(
        db=db_session,
        tenant_id=tenant.id,
        invited_by_user_id=admin.id,
        email="newuser@example.com",
        role_id=role.id,
    )

    result = accept_tenant_invitation_for_new_user(
        db=db_session,
        raw_token=raw_token,
        full_name="New User",
        password="secure-password-123",
    )

    user = db_session.scalar(
        select(User).where(User.email == "newuser@example.com")
    )

    membership = db_session.scalar(
        select(Membership).where(
            Membership.id == result["membership_id"]
        )
    )

    membership_role = db_session.scalar(
        select(MembershipRole).where(
            MembershipRole.membership_id == membership.id
        )
    )

    assert user is not None
    assert user.full_name == "New User"
    assert user.is_active is True
    assert user.password_hash != "secure-password-123"
    assert result["user_id"] == user.id
    assert result["tenant_id"] == tenant.id
    assert membership.user_id == user.id
    assert membership_role.role_id == role.id


def test_accept_invitation_for_existing_user(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant = tenant_factory()
    admin = user_factory()
    invited_user = user_factory()
    role = tenant.roles[0]

    raw_token, _ = create_tenant_invitation(
        db=db_session,
        tenant_id=tenant.id,
        invited_by_user_id=admin.id,
        email=invited_user.email,
        role_id=role.id,
    )

    result = accept_tenant_invitation_for_existing_user(
        db=db_session,
        raw_token=raw_token,
        authenticated_user_id=invited_user.id,
    )

    assert result["user_id"] == invited_user.id
    assert result["tenant_id"] == tenant.id

    membership = db_session.scalar(
        select(Membership).where(
            Membership.tenant_id == tenant.id,
            Membership.user_id == invited_user.id,
        )
    )

    assert membership is not None


def test_existing_user_cannot_accept_another_users_invitation(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant = tenant_factory()
    admin = user_factory()
    invited_user = user_factory()
    another_user = user_factory()
    role = tenant.roles[0]

    raw_token, _ = create_tenant_invitation(
        db=db_session,
        tenant_id=tenant.id,
        invited_by_user_id=admin.id,
        email=invited_user.email,
        role_id=role.id,
    )

    with pytest.raises(TenantInvitationValidationError):
        accept_tenant_invitation_for_existing_user(
            db=db_session,
            raw_token=raw_token,
            authenticated_user_id=another_user.id,
        )

    assert get_membership(
        db_session,
        tenant.id,
        invited_user.id,
    ) is None


def test_new_user_cannot_accept_invitation_after_account_was_created(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant = tenant_factory()
    admin = user_factory()
    role = tenant.roles[0]

    raw_token, _ = create_tenant_invitation(
        db=db_session,
        tenant_id=tenant.id,
        invited_by_user_id=admin.id,
        email="newuser@example.com",
        role_id=role.id,
    )

    user_factory(email="newuser@example.com")

    with pytest.raises(TenantInvitationConflictError):
        accept_tenant_invitation_for_new_user(
            db=db_session,
            raw_token=raw_token,
            full_name="New User",
            password="secure-password-123",
        )


def test_cannot_accept_invitation_for_inactive_tenant(
    db_session,
    tenant_factory,
    user_factory,
):
    tenant = tenant_factory()
    admin = user_factory()
    role = tenant.roles[0]

    raw_token, _ = create_tenant_invitation(
        db=db_session,
        tenant_id=tenant.id,
        invited_by_user_id=admin.id,
        email="newuser@example.com",
        role_id=role.id,
    )

    tenant.is_active = False
    db_session.flush()

    with pytest.raises(TenantInvitationValidationError):
        accept_tenant_invitation_for_new_user(
            db=db_session,
            raw_token=raw_token,
            full_name="New User",
            password="secure-password-123",
        )