
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.tenant_session import TenantSession
from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.platform_admin import PlatformAdmin
from app.models.tenant import Tenant
from app.models.user import User
from app.services.permissions import sync_permissions
from app.services.roles import provision_default_roles


@dataclass(frozen=True, slots=True)
class InitialTenantResult:
    """Entities created during the initial platform bootstrap."""

    user: User
    tenant: Tenant
    membership: Membership
    platform_admin: PlatformAdmin


def create_initial_tenant(
    db: Session,
    *,
    full_name: str,
    email: str,
    password_hash: str,
    tenant_name: str,
) -> InitialTenantResult:
    """Create the initial platform administrator and tenant.

    The caller is responsible for managing the transaction.
    """
    existing_admin = db.scalar(
        select(PlatformAdmin.id).limit(1)
    )

    if existing_admin is not None:
        raise RuntimeError(
            "Platform bootstrap has already been completed."
        )

    existing_user = db.scalar(
        select(User.id).where(User.email == email)
    )

    if existing_user is not None:
        raise ValueError(
            "A user with this email already exists."
        )

    user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        is_active=True,
    )
    db.add(user)
    db.flush()

    tenant = Tenant(name=tenant_name)
    db.add(tenant)
    db.flush()

    platform_admin = PlatformAdmin(user_id=user.id)
    db.add(platform_admin)

    membership = Membership(
        user_id=user.id,
        tenant_id=tenant.id,
    )
    db.add(membership)
    db.flush()

    # Synchronize the global permission catalog.
    sync_permissions(db)

    # Provision tenant-specific roles using the same connection.
    with TenantSession(
        bind=db.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant.id,
    ) as tenant_db:
        roles = provision_default_roles(
            db=tenant_db,
            tenant_id=tenant.id,
        )

        tenant_db.add(
            MembershipRole(
                tenant_id=tenant.id,
                membership_id=membership.id,
                role_id=roles["Owner"].id,
            )
        )

        tenant_db.flush()

        # Commit only the nested savepoint.
        tenant_db.commit()

    db.flush()

    return InitialTenantResult(
        user=user,
        tenant=tenant,
        membership=membership,
        platform_admin=platform_admin,
    )
