from getpass import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    Membership,
    MembershipRole,
    PlatformAdmin,
    Role,
    Tenant,
    User,
)
from app.services.permissions import sync_permissions


def bootstrap() -> None:
    """Create the initial platform administrator and first tenant."""

    print("=== CaterFlow | Initial Bootstrap ===\n")

    full_name = input("Administrator full name: ").strip()
    email = input("Administrator email: ").strip().lower()
    tenant_name = input("First tenant name: ").strip()

    password = getpass("Administrator password: ")
    password_confirmation = getpass("Confirm password: ")

    if not full_name or not email or not tenant_name:
        raise ValueError("Name, email and tenant name are required.")

    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")

    if password != password_confirmation:
        raise ValueError("Passwords do not match.")

    password_hash = hash_password(password)

    with SessionLocal.begin() as db:
        existing_admin = db.scalar(select(PlatformAdmin.id).limit(1))

        if existing_admin is not None:
            raise RuntimeError("Platform bootstrap has already been completed.")

        existing_user = db.scalar(select(User.id).where(User.email == email))

        if existing_user is not None:
            raise ValueError("A user with this email already exists.")

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

        owner_role = Role(
            tenant_id=tenant.id,
            name="Owner",
            description="Tenant owner with full permissions.",
            is_system=True,
        )
        db.add(owner_role)
        db.flush()

        membership_role = MembershipRole(
            tenant_id=tenant.id,
            membership_id=membership.id,
            role_id=owner_role.id,
        )
        db.add(membership_role)

        sync_permissions(db)

    print("\nBootstrap completed successfully.")
    print(f"Administrator: {email}")
    print(f"Tenant: {tenant_name}")
    print("Platform administrator and Owner permissions created.")


if __name__ == "__main__":
    bootstrap()
