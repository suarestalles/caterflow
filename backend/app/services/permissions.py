import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.permissions import PERMISSION_CATALOG
from app.models.membership_role import MembershipRole
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission

OWNER_ROLE_NAME = "Owner"


def sync_permission_catalog(db: Session) -> None:
    """Create or update the global permission catalog."""

    values = [
        {
            "code": permission.code.value,
            "description": permission.description,
        }
        for permission in PERMISSION_CATALOG
    ]

    statement = insert(Permission).values(values)

    statement = statement.on_conflict_do_update(
        index_elements=[Permission.code],
        set_={
            "description": statement.excluded.description,
        },
    )

    db.execute(statement)


def sync_owner_role_permissions(db: Session) -> None:
    """Assign all catalog permissions to existing system Owner roles."""

    owner_roles = db.scalars(
        select(Role).where(
            Role.name == OWNER_ROLE_NAME,
            Role.is_system.is_(True),
        )
    ).all()

    if not owner_roles:
        return

    permission_codes = [permission.code.value for permission in PERMISSION_CATALOG]

    permission_ids = db.scalars(
        select(Permission.id).where(Permission.code.in_(permission_codes))
    ).all()

    if not permission_ids:
        return

    values = [
        {
            "tenant_id": role.tenant_id,
            "role_id": role.id,
            "permission_id": permission_id,
        }
        for role in owner_roles
        for permission_id in permission_ids
    ]

    statement = insert(RolePermission).values(values)

    statement = statement.on_conflict_do_nothing(
        index_elements=[
            RolePermission.role_id,
            RolePermission.permission_id,
        ],
    )

    db.execute(statement)


def sync_permissions(db: Session) -> None:
    """Synchronize permissions and grant them to existing Owners."""

    sync_permission_catalog(db)
    sync_owner_role_permissions(db)


def get_effective_permissions(
    db: Session,
    membership_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> set[str]:
    """Return all permission codes granted to a tenant membership."""

    statement = (
        select(Permission.code)
        .join(
            RolePermission,
            RolePermission.permission_id == Permission.id,
        )
        .join(
            MembershipRole,
            MembershipRole.role_id == RolePermission.role_id,
        )
        .where(
            MembershipRole.membership_id == membership_id,
            MembershipRole.tenant_id == tenant_id,
            RolePermission.tenant_id == tenant_id,
        )
    )

    return set(db.scalars(statement).all())
