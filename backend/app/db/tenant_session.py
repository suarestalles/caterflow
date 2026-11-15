import uuid
from collections.abc import Generator

from sqlalchemy import event
from sqlalchemy.orm import Session, sessionmaker, with_loader_criteria

from app.db.session import engine
from app.models.tenant_scoped import TenantScoped


class TenantSession(Session):
    """SQLAlchemy session with automatic tenant isolation."""

    def __init__(
        self,
        *args,
        tenant_id: uuid.UUID | None = None,
        platform_access: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.tenant_id = tenant_id
        self.platform_access = platform_access


TenantSessionLocal = sessionmaker(
    bind=engine,
    class_=TenantSession,
    autoflush=False,
    autocommit=False,
)


@event.listens_for(TenantSession, "do_orm_execute")
def apply_tenant_filter(execute_state) -> None:
    session = execute_state.session

    if session.platform_access:
        return

    if session.tenant_id is None:
        raise PermissionError("Tenant context is required.")

    if not execute_state.is_orm_statement:
        raise PermissionError("Tenant sessions only allow ORM statements.")

    if execute_state.is_insert:
        raise PermissionError(
            "Bulk INSERT is not allowed in tenant sessions. Use the ORM unit of work instead."
        )

    if execute_state.is_relationship_load or execute_state.is_column_load:
        return

    if execute_state.is_select or execute_state.is_update or execute_state.is_delete:
        tenant_id = session.tenant_id

        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                TenantScoped,
                lambda model: model.tenant_id == tenant_id,
                include_aliases=True,
            )
        )


@event.listens_for(TenantSession, "before_flush")
def validate_tenant_changes(session, flush_context, instances) -> None:
    tenant_id = session.tenant_id
    platform_access = session.platform_access

    if tenant_id is None and not platform_access:
        raise PermissionError("Tenant context is required.")

    for instance in session.new:
        if not isinstance(instance, TenantScoped):
            continue

        if instance.tenant_id is None:
            if platform_access:
                raise PermissionError("Platform operations must explicitly provide tenant_id.")

            instance.tenant_id = tenant_id

        elif not platform_access and instance.tenant_id != tenant_id:
            raise PermissionError("Cannot create a record for another tenant.")

    for instance in session.dirty.union(session.deleted):
        if not isinstance(instance, TenantScoped):
            continue

        if instance.tenant_id is None:
            raise PermissionError("Tenant ownership cannot be empty.")

        if not platform_access and instance.tenant_id != tenant_id:
            raise PermissionError("Cannot modify or delete another tenant's records.")


def get_tenant_db(
    tenant_id: uuid.UUID,
) -> Generator[TenantSession, None, None]:
    db = TenantSessionLocal(tenant_id=tenant_id)

    try:
        yield db
    finally:
        db.close()


def get_platform_db() -> Generator[TenantSession, None, None]:
    db = TenantSessionLocal(platform_access=True)

    try:
        yield db
    finally:
        db.close()
