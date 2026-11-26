
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.tenant import Tenant


def list_tenants(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[Tenant], int]:
    statement = select(Tenant)

    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(Tenant.name.ilike(term))

    if is_active is not None:
        statement = statement.where(Tenant.is_active.is_(is_active))

    total = db.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0

    tenants = list(
        db.scalars(
            statement
            .order_by(Tenant.name.asc(), Tenant.id.asc())
            .offset(offset)
            .limit(limit)
        ).all()
    )

    return tenants, total


def get_tenant(db: Session, tenant_id: UUID) -> Tenant | None:
    return db.get(Tenant, tenant_id)


def create_tenant(db: Session, *, name: str) -> Tenant:
    tenant = Tenant(name=name, is_active=True)
    db.add(tenant)
    db.flush()
    return tenant
