from getpass import getpass

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.services.tenants import create_initial_tenant


def bootstrap() -> None:
    """Collect input and execute the initial platform bootstrap."""

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
        result = create_initial_tenant(
            db,
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            tenant_name=tenant_name,
        )

    print("\nBootstrap completed successfully.")
    print(f"Administrator: {result.user.email}")
    print(f"Tenant: {result.tenant.name}")
    print("Platform administrator created.")
    print("Default tenant roles and permissions created.")
    print("Initial membership assigned to Owner.")


if __name__ == "__main__":
    bootstrap()
