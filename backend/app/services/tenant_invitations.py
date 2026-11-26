from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.repositories import tenant_invitations as repository
from app.services.user_action_tokens import (
    TENANT_INVITATION,
    InvalidUserActionTokenError,
    consume_user_action_token,
    create_user_action_token,
    get_valid_user_action_token,
)

INVITATION_EXPIRES_IN = timedelta(hours=72)
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128


class TenantInvitationError(Exception):
    pass


class TenantInvitationNotFoundError(TenantInvitationError):
    pass


class TenantInvitationConflictError(TenantInvitationError):
    pass


class TenantInvitationValidationError(TenantInvitationError):
    pass


def create_tenant_invitation(
    db: Session,
    tenant_id: UUID,
    invited_by_user_id: UUID,
    email: str,
    role_id: UUID,
) -> tuple[str, UUID]:
    now = datetime.now(UTC)
    normalized_email = email.strip().lower()

    try:
        tenant = repository.get_tenant(db, tenant_id)

        if tenant is None:
            raise TenantInvitationNotFoundError("Tenant not found.")

        if not tenant.is_active:
            raise TenantInvitationValidationError(
                "Cannot invite users to an inactive tenant."
            )

        role = repository.get_role(db, tenant_id, role_id)

        if role is None:
            raise TenantInvitationValidationError(
                "The selected role does not belong to this tenant."
            )

        user = repository.get_user_by_email(db, normalized_email)

        if user is not None:
            if not user.is_active:
                raise TenantInvitationValidationError(
                    "Cannot invite an inactive user account."
                )

            membership = repository.get_membership(
                db,
                tenant_id,
                user.id,
            )

            if membership is not None:
                raise TenantInvitationConflictError(
                    "This user already belongs to the tenant."
                )

        repository.revoke_pending_invites(
            db,
            tenant_id,
            normalized_email,
            now,
        )

        raw_token, action_token = create_user_action_token(
            db=db,
            user_id=user.id if user else None,
            purpose=TENANT_INVITATION,
            expires_in=INVITATION_EXPIRES_IN,
            email=normalized_email,
            tenant_id=tenant_id,
            role_id=role_id,
            invited_by_user_id=invited_by_user_id,
        )

        db.commit()

        return raw_token, action_token.id

    except Exception:
        db.rollback()
        raise


def _get_invitation(db: Session, raw_token: str):
    try:
        action_token = get_valid_user_action_token(
            db=db,
            raw_token=raw_token,
            purpose=TENANT_INVITATION,
        )
    except InvalidUserActionTokenError:
        raise

    if action_token.tenant_id is None or action_token.role_id is None:
        raise TenantInvitationValidationError(
            "Invalid tenant invitation."
        )

    return action_token


def _validate_invitation_target(
    db: Session,
    action_token,
):
    tenant = repository.get_tenant(
        db,
        action_token.tenant_id,
        for_update=True,
    )

    if tenant is None:
        raise TenantInvitationNotFoundError("Tenant not found.")

    if not tenant.is_active:
        raise TenantInvitationValidationError(
            "This tenant is currently inactive."
        )

    role = repository.get_role(
        db,
        action_token.tenant_id,
        action_token.role_id,
    )

    if role is None:
        raise TenantInvitationValidationError(
            "The invitation role is no longer available."
        )

    return tenant, role


def _complete_acceptance(
    db: Session,
    action_token,
    user_id: UUID,
) -> dict[str, UUID]:
    membership = repository.get_membership(
        db,
        action_token.tenant_id,
        user_id,
    )

    if membership is not None:
        raise TenantInvitationConflictError(
            "This user already belongs to the tenant."
        )

    membership = repository.create_membership(
        db=db,
        tenant_id=action_token.tenant_id,
        user_id=user_id,
        role_id=action_token.role_id,
    )

    action_token.user_id = user_id
    consume_user_action_token(action_token)

    db.flush()

    return {
        "user_id": user_id,
        "tenant_id": action_token.tenant_id,
        "membership_id": membership.id,
    }


def accept_tenant_invitation_for_new_user(
    db: Session,
    raw_token: str,
    full_name: str,
    password: str,
) -> dict[str, UUID]:
    normalized_name = full_name.strip()

    if not normalized_name or len(normalized_name) > 150:
        raise TenantInvitationValidationError(
            "Full name must contain between 1 and 150 characters."
        )

    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise TenantInvitationValidationError(
            "Password must contain between 12 and 128 characters."
        )

    try:
        action_token = _get_invitation(db, raw_token)

        if action_token.user_id is not None:
            raise TenantInvitationValidationError(
                "This invitation belongs to an existing account. "
                "Sign in to accept it."
            )

        _validate_invitation_target(db, action_token)

        existing_user = repository.get_user_by_email(
            db,
            action_token.email,
        )

        if existing_user is not None:
            raise TenantInvitationConflictError(
                "An account with this email already exists. "
                "Sign in to accept the invitation."
            )

        user = repository.create_user(
            db=db,
            full_name=normalized_name,
            email=action_token.email,
            password_hash=hash_password(password),
        )

        result = _complete_acceptance(
            db,
            action_token,
            user.id,
        )

        db.commit()
        return result

    except (TenantInvitationError, InvalidUserActionTokenError):
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise TenantInvitationConflictError(
            "The invitation could not be accepted because the account "
            "or membership already exists."
        ) from None

    except Exception:
        db.rollback()
        raise


def accept_tenant_invitation_for_existing_user(
    db: Session,
    raw_token: str,
    authenticated_user_id: UUID,
) -> dict[str, UUID]:
    try:
        action_token = _get_invitation(db, raw_token)

        if action_token.user_id is not None:
            if action_token.user_id != authenticated_user_id:
                raise TenantInvitationValidationError(
                    "This invitation belongs to another account."
                )

        user = repository.get_user_by_email(
            db,
            action_token.email,
        )

        if user is None or user.id != authenticated_user_id:
            raise TenantInvitationValidationError(
                "The authenticated account does not match the invitation."
            )

        if not user.is_active:
            raise TenantInvitationValidationError(
                "This user account is inactive."
            )

        _validate_invitation_target(db, action_token)

        result = _complete_acceptance(
            db,
            action_token,
            user.id,
        )

        db.commit()
        return result

    except (TenantInvitationError, InvalidUserActionTokenError):
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise TenantInvitationConflictError(
            "The invitation could not be accepted because the membership "
            "already exists."
        ) from None

    except Exception:
        db.rollback()
        raise