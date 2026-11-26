
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.repositories import platform_tenants as repository


class PlatformTenantNotFoundError(Exception):
    pass


def list_tenants(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[Tenant], int]:
    return repository.list_tenants(
        db,
        offset=offset,
        limit=limit,
        search=search,
        is_active=is_active,
    )


def get_tenant(db: Session, tenant_id: UUID) -> Tenant:
    tenant = repository.get_tenant(db, tenant_id)

    if tenant is None:
        raise PlatformTenantNotFoundError

    return tenant


def create_tenant(db: Session, *, name: str) -> Tenant:
    try:
        tenant = repository.create_tenant(db, name=name)
        db.commit()
        db.refresh(tenant)
        return tenant
    except Exception:
        db.rollback()
        raise


def update_tenant(
    db: Session,
    *,
    tenant_id: UUID,
    data: dict,
) -> Tenant:
    tenant = get_tenant(db, tenant_id)

    try:
        for field, value in data.items():
            setattr(tenant, field, value)

        db.commit()
        db.refresh(tenant)
        return tenant
    except Exception:
        db.rollback()
        raise


def set_tenant_active(
    db: Session,
    *,
    tenant_id: UUID,
    is_active: bool,
) -> Tenant:
    tenant = get_tenant(db, tenant_id)

    try:
        tenant.is_active = is_active
        db.commit()
        db.refresh(tenant)
        return tenant
    except Exception:
        db.rollback()
        raise
