
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.tenant_session import TenantSession
from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.role import Role
from app.models.tenant import Tenant
from app.repositories import platform_memberships as repository


class PlatformMembershipNotFoundError(Exception):
    pass


class PlatformMembershipConflictError(Exception):
    pass


class PlatformMembershipValidationError(Exception):
    pass


class LastOwnerError(Exception):
    pass


def _response_data(row):
    membership, user, role = row

    return {
        "id": membership.id,
        "tenant_id": membership.tenant_id,
        "user_id": user.id,
        "user_full_name": user.full_name,
        "user_email": user.email,
        "role_id": role.id,
        "role_name": role.name,
        "created_at": membership.created_at,
        "updated_at": membership.updated_at,
    }


def _validate_tenant(db: Session, tenant_id: UUID):
    tenant = db.scalar(
        select(Tenant).where(Tenant.id == tenant_id)
    )

    if tenant is None:
        raise PlatformMembershipNotFoundError("Tenant not found.")

    if not tenant.is_active:
        raise PlatformMembershipValidationError(
            "Cannot manage memberships of an inactive tenant."
        )


def list_memberships(
    db: Session,
    tenant_id: UUID,
    *,
    offset: int,
    limit: int,
):
    _validate_tenant(db, tenant_id)

    rows, total = repository.list_memberships(
        db,
        tenant_id,
        offset=offset,
        limit=limit,
    )

    return [_response_data(row) for row in rows], total


def create_membership(
    db: Session,
    *,
    tenant_id: UUID,
    user_id: UUID,
    role_id: UUID,
):
    _validate_tenant(db, tenant_id)

    user = repository.get_user(db, user_id)

    if user is None:
        raise PlatformMembershipNotFoundError("User not found.")

    if not user.is_active:
        raise PlatformMembershipValidationError(
            "Cannot add an inactive user to a tenant."
        )

    role = repository.get_role(db, tenant_id, role_id)

    if role is None:
        raise PlatformMembershipValidationError(
            "The selected role does not belong to this tenant."
        )

    if repository.get_existing_membership(db, tenant_id, user_id):
        raise PlatformMembershipConflictError(
            "This user is already a member of the tenant."
        )

    membership = Membership(
        tenant_id=tenant_id,
        user_id=user_id,
    )
    db.add(membership)

    try:
        db.flush()

        db.add(
            MembershipRole(
                tenant_id=tenant_id,
                membership_id=membership.id,
                role_id=role.id,
            )
        )

        db.commit()

        row = repository.get_membership_details(
            db,
            tenant_id,
            membership.id,
        )
        return _response_data(row)

    except IntegrityError:
        db.rollback()
        raise PlatformMembershipConflictError(
            "The membership could not be created because it already exists."
        ) from None
    except Exception:
        db.rollback()
        raise


def update_membership_role(
    db: Session,
    *,
    tenant_id: UUID,
    membership_id: UUID,
    role_id: UUID,
):
    _validate_tenant(db, tenant_id)

    membership = repository.get_membership(
        db,
        tenant_id,
        membership_id,
    )

    if membership is None:
        raise PlatformMembershipNotFoundError("Membership not found.")

    new_role = repository.get_role(db, tenant_id, role_id)

    if new_role is None:
        raise PlatformMembershipValidationError(
            "The selected role does not belong to this tenant."
        )

    current_assignment = repository.get_membership_role(
        db,
        tenant_id,
        membership_id,
    )

    if current_assignment is None:
        raise PlatformMembershipNotFoundError(
            "Membership role assignment not found."
        )

    if current_assignment.role_id == role_id:
        row = repository.get_membership_details(
            db,
            tenant_id,
            membership_id,
        )
        return _response_data(row)

    current_role_name = db.scalar(
        select(Role.name).where(Role.id == current_assignment.role_id)
    )

    if (
        current_role_name == "Owner"
        and new_role.name != "Owner"
        and repository.count_other_owners(
            db,
            tenant_id,
            membership_id,
        ) == 0
    ):
        raise LastOwnerError(
            "The tenant must have at least one Owner."
        )

    try:
        current_assignment.role_id = new_role.id
        db.commit()

        row = repository.get_membership_details(
            db,
            tenant_id,
            membership_id,
        )
        return _response_data(row)

    except Exception:
        db.rollback()
        raise


def delete_membership(
    db: Session,
    *,
    tenant_id: UUID,
    membership_id: UUID,
):
    _validate_tenant(db, tenant_id)

    membership = repository.get_membership(
        db,
        tenant_id,
        membership_id,
    )

    if membership is None:
        raise PlatformMembershipNotFoundError("Membership not found.")

    current_assignment = repository.get_membership_role(
        db,
        tenant_id,
        membership_id,
    )

    if current_assignment is not None:
        current_role_name = db.scalar(
            select(Role.name).where(Role.id == current_assignment.role_id)
        )

        if (
            current_role_name == "Owner"
            and repository.count_other_owners(
                db,
                tenant_id,
                membership_id,
            ) == 0
        ):
            raise LastOwnerError(
                "The tenant must have at least one Owner."
            )

    try:
        db.delete(membership)
        db.commit()
    except Exception:
        db.rollback()
        raise

def list_tenant_roles(db: TenantSession, tenant_id: UUID) -> list[dict]:
    tenant = repository.get_tenant(db, tenant_id)

    if tenant is None:
        raise PlatformMembershipNotFoundError("Tenant not found.")

    if not tenant.is_active:
        raise PlatformMembershipValidationError("Tenant is inactive.")

    roles = repository.list_tenant_roles(db, tenant_id)

    return [
        {
            "id": str(role.id),
            "name": role.name,
            "description": role.description,
            "is_system": role.is_system,
        }
        for role in roles
    ]