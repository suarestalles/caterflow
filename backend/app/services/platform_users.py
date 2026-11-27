
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.platform_admin import PlatformAdmin
from app.models.role import Role
from app.models.user import User
from app.repositories import platform_users as repository


class PlatformUserNotFoundError(Exception):
    pass


class PlatformUserAlreadyExistsError(Exception):
    pass


class PlatformUserValidationError(Exception):
    pass


def _response_data(
    db: Session,
    user: User,
    platform_admin_ids: set[UUID] | None = None,
) -> dict:
    if platform_admin_ids is None:
        admin = repository.get_platform_admin(db, user.id)
        is_platform_admin = (
            admin is not None and admin.revoked_at is None
        )
    else:
        is_platform_admin = user.id in platform_admin_ids

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "is_active": user.is_active,
        "is_platform_admin": is_platform_admin,
        "tenants": [
            {
                "id": membership.tenant.id,
                "name": membership.tenant.name,
            }
            for membership in user.memberships
        ],
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def _validate_tenants(
    db: Session,
    tenant_ids: list[UUID],
) -> None:
    tenants = repository.get_tenants(db, tenant_ids)

    if len(tenants) != len(tenant_ids):
        raise PlatformUserValidationError(
            "One or more selected tenants do not exist."
        )

    if any(not tenant.is_active for tenant in tenants):
        raise PlatformUserValidationError(
            "Cannot associate users with inactive tenants."
        )


def _set_platform_admin(
    db: Session,
    user_id: UUID,
    enabled: bool,
) -> None:
    admin = repository.get_platform_admin(db, user_id)

    if enabled:
        if admin is None:
            db.add(PlatformAdmin(user_id=user_id))
        else:
            admin.revoked_at = None
    elif admin is not None:
        admin.revoked_at = datetime.now(UTC)


def _count_other_owners(
    db: Session,
    tenant_id: UUID,
    excluded_membership_id: UUID,
) -> int:
    statement = (
        select(
            func.count(
                func.distinct(MembershipRole.membership_id)
            )
        )
        .join(
            Role,
            (Role.id == MembershipRole.role_id)
            & (Role.tenant_id == MembershipRole.tenant_id),
        )
        .where(
            MembershipRole.tenant_id == tenant_id,
            Role.name == "Owner",
            MembershipRole.membership_id != excluded_membership_id,
        )
    )

    return db.scalar(statement) or 0


def _validate_membership_removal(
    db: Session,
    membership: Membership,
) -> None:
    is_owner = db.scalar(
        select(MembershipRole.id)
        .join(
            Role,
            (Role.id == MembershipRole.role_id)
            & (Role.tenant_id == MembershipRole.tenant_id),
        )
        .where(
            MembershipRole.tenant_id == membership.tenant_id,
            MembershipRole.membership_id == membership.id,
            Role.name == "Owner",
        )
        .limit(1)
    )

    if is_owner is None:
        return

    if _count_other_owners(
        db,
        membership.tenant_id,
        membership.id,
    ) == 0:
        raise PlatformUserValidationError(
            "Cannot remove the last Owner of a tenant."
        )


def _sync_memberships(
    db: Session,
    user: User,
    tenant_ids: list[UUID],
) -> None:
    _validate_tenants(db, tenant_ids)

    current_memberships = repository.get_memberships(db, user.id)
    current_by_tenant = {
        membership.tenant_id: membership
        for membership in current_memberships
    }

    requested_ids = set(tenant_ids)

    for tenant_id in requested_ids:
        if tenant_id not in current_by_tenant:
            db.add(
                Membership(
                    tenant_id=tenant_id,
                    user_id=user.id,
                )
            )

    for tenant_id, membership in current_by_tenant.items():
        if tenant_id not in requested_ids:
            _validate_membership_removal(db, membership)
            db.delete(membership)


def _validate_final_access(
    is_platform_admin: bool,
    tenant_ids: list[UUID],
) -> None:
    if not is_platform_admin and not tenant_ids:
        raise PlatformUserValidationError(
            "A user must be a platform admin or belong to at least one tenant."
        )


def list_users(
    db: Session,
    *,
    offset: int,
    limit: int,
    search: str | None = None,
    is_active: bool | None = None,
):
    users, total = repository.list_users(
        db,
        offset=offset,
        limit=limit,
        search=search,
        is_active=is_active,
    )

    platform_admin_ids = repository.get_active_platform_admin_ids(db)

    return [
        _response_data(db, user, platform_admin_ids)
        for user in users
    ], total


def get_user(db: Session, user_id: UUID) -> dict:
    user = repository.get_user(db, user_id)

    if user is None:
        raise PlatformUserNotFoundError

    return _response_data(db, user)


def create_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    password: str,
    is_platform_admin: bool,
    tenant_ids: list[UUID],
) -> dict:
    normalized_email = email.strip().lower()
    normalized_name = full_name.strip()

    _validate_final_access(is_platform_admin, tenant_ids)
    _validate_tenants(db, tenant_ids)

    if repository.get_user_by_email(db, normalized_email):
        raise PlatformUserAlreadyExistsError

    try:
        user = repository.create_user(
            db,
            full_name=normalized_name,
            email=normalized_email,
            password_hash=hash_password(password),
        )

        _set_platform_admin(db, user.id, is_platform_admin)

        for tenant_id in set(tenant_ids):
            db.add(
                Membership(
                    tenant_id=tenant_id,
                    user_id=user.id,
                )
            )

        db.commit()

        user = repository.get_user(db, user.id)
        return _response_data(db, user)

    except IntegrityError:
        db.rollback()
        raise PlatformUserAlreadyExistsError from None
    except Exception:
        db.rollback()
        raise


def update_user(
    db: Session,
    *,
    user_id: UUID,
    current_admin_id: UUID,
    full_name: str | None = None,
    email: str | None = None,
    is_platform_admin: bool | None = None,
    tenant_ids: list[UUID] | None = None,
) -> dict:
    user = repository.get_user(db, user_id)

    if user is None:
        raise PlatformUserNotFoundError

    current_admin = repository.get_platform_admin(db, user.id)
    currently_platform_admin = (
        current_admin is not None
        and current_admin.revoked_at is None
    )

    final_platform_admin = (
        is_platform_admin
        if is_platform_admin is not None
        else currently_platform_admin
    )

    current_tenant_ids = [
        membership.tenant_id
        for membership in user.memberships
    ]

    final_tenant_ids = (
        tenant_ids
        if tenant_ids is not None
        else current_tenant_ids
    )

    _validate_final_access(
        final_platform_admin,
        final_tenant_ids,
    )

    if tenant_ids is not None:
        _validate_tenants(db, tenant_ids)

    if email is not None:
        normalized_email = email.strip().lower()
        existing_user = repository.get_user_by_email(
            db,
            normalized_email,
        )

        if existing_user is not None and existing_user.id != user.id:
            raise PlatformUserAlreadyExistsError

    if (
        currently_platform_admin
        and not final_platform_admin
    ):
        if user.id == current_admin_id:
            raise PlatformUserValidationError(
                "You cannot revoke your own platform admin access."
            )

        active_admin_ids = repository.get_active_platform_admin_ids(db)

        if len(active_admin_ids) <= 1:
            raise PlatformUserValidationError(
                "Cannot revoke the last active Platform Admin."
            )

    try:
        if full_name is not None:
            user.full_name = full_name.strip()

        if email is not None:
            user.email = email.strip().lower()

        if is_platform_admin is not None:
            _set_platform_admin(
                db,
                user.id,
                is_platform_admin,
            )

        if tenant_ids is not None:
            _sync_memberships(db, user, tenant_ids)

        db.commit()

        user = repository.get_user(db, user.id)
        return _response_data(db, user)

    except IntegrityError:
        db.rollback()
        raise PlatformUserAlreadyExistsError from None
    except Exception:
        db.rollback()
        raise


def activate_user(
    db: Session,
    user_id: UUID,
) -> dict:
    user = repository.get_user(db, user_id)

    if user is None:
        raise PlatformUserNotFoundError

    if user.is_active:
        return _response_data(db, user)

    try:
        repository.set_user_active(db, user, True)
        db.commit()

        user = repository.get_user(db, user.id)
        return _response_data(db, user)

    except Exception:
        db.rollback()
        raise



def deactivate_user(
    db: Session,
    user_id: UUID,
    current_admin_id: UUID,
) -> dict:
    if user_id == current_admin_id:
        raise PlatformUserValidationError(
            "You cannot deactivate your own account."
        )

    user = repository.get_user(db, user_id)

    if user is None:
        raise PlatformUserNotFoundError

    if not user.is_active:
        return _response_data(db, user)

    # Prevent deactivating the last active Platform Admin.
    platform_admin = repository.get_platform_admin(db, user.id)

    if (
        platform_admin is not None
        and platform_admin.revoked_at is None
    ):
        active_admin_ids = repository.get_active_platform_admin_ids(db)

        if len(active_admin_ids) <= 1:
            raise PlatformUserValidationError(
                "Cannot deactivate the last active Platform Admin."
            )

    # Prevent leaving a tenant without an Owner.
    for membership in user.memberships:
        _validate_membership_removal(db, membership)

    repository.set_user_active(db, user, False)

    try:
        db.commit()
        return _response_data(db, repository.get_user(db, user.id))
    except Exception:
        db.rollback()
        raise
