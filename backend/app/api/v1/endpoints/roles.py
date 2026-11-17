from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.v1.deps import (
    get_current_tenant_db,
    require_permission,
)
from app.core.permissions import PermissionCode
from app.db.tenant_session import TenantSession
from app.models.role import Role

router = APIRouter()


@router.get(
    "/",
    tags=["Roles"],
    dependencies=[Depends(require_permission(PermissionCode.ROLES_READ))],
)
def list_roles(
    db: TenantSession = Depends(get_current_tenant_db),
):
    roles = db.scalars(select(Role).order_by(Role.name)).all()

    return [
        {
            "id": str(role.id),
            "name": role.name,
            "description": role.description,
            "is_system": role.is_system,
        }
        for role in roles
    ]
