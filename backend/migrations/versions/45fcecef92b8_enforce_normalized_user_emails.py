"""enforce normalized user emails

Revision ID: 45fcecef92b8
Revises: 14fd06ef03e9
Create Date: 2026-11-12 13:59:13.602141

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "45fcecef92b8"
down_revision: str | Sequence[str] | None = "14fd06ef03e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        op.f("ck_users_email_lowercase"),
        "users",
        "email = lower(email)",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f("ck_users_email_lowercase"),
        "users",
        type_="check",
    )
