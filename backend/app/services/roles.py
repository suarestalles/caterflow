from uuid import UUID

from sqlalchemy import select

from app.core.permissions import (
    DEFAULT_ROLE_DESCRIPTIONS,
    DEFAULT_ROLE_PERMISSIONS,
)
from app.db.tenant_session import TenantSession
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


def provision_default_roles(
    db: TenantSession,
    tenant_id: UUID,
) -> dict[str, Role]:
    """Create default tenant roles and grant their initial permissions."""
    if db.platform_access or db.tenant_id != tenant_id:
        raise PermissionError("A matching tenant-scoped session is required.")

    role_names = list(DEFAULT_ROLE_PERMISSIONS)

    roles = db.scalars(select(Role).where(Role.name.in_(role_names))).all()

    roles_by_name = {role.name: role for role in roles}

    for role_name, description in DEFAULT_ROLE_DESCRIPTIONS.items():
        role = roles_by_name.get(role_name)

        if role is not None:
            if not role.is_system:
                raise ValueError(f"Role name '{role_name}' is reserved for system roles.")
            continue

        role = Role(
            tenant_id=tenant_id,
            name=role_name,
            description=description,
            is_system=True,
        )
        db.add(role)
        roles_by_name[role_name] = role

    db.flush()

    required_codes = {
        code.value for permissions in DEFAULT_ROLE_PERMISSIONS.values() for code in permissions
    }

    permissions = db.scalars(select(Permission).where(Permission.code.in_(required_codes))).all()

    permissions_by_code = {permission.code: permission for permission in permissions}

    missing_codes = required_codes - permissions_by_code.keys()

    if missing_codes:
        missing = ", ".join(sorted(missing_codes))
        raise RuntimeError(f"Permission catalog is missing required codes: {missing}")

    role_ids = [role.id for role in roles_by_name.values()]

    existing_assignments = db.execute(
        select(
            RolePermission.role_id,
            RolePermission.permission_id,
        ).where(RolePermission.role_id.in_(role_ids))
    ).all()

    assigned = {(role_id, permission_id) for role_id, permission_id in existing_assignments}

    for role_name, role in roles_by_name.items():
        for permission_code in DEFAULT_ROLE_PERMISSIONS[role_name]:
            permission = permissions_by_code[permission_code.value]
            assignment = (role.id, permission.id)

            if assignment in assigned:
                continue

            db.add(
                RolePermission(
                    tenant_id=tenant_id,
                    role_id=role.id,
                    permission_id=permission.id,
                )
            )
            assigned.add(assignment)

    db.flush()

    return roles_by_name
