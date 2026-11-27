"""add employee default compensation

Revision ID: 5b68f2d8a26f
Revises: c4f1199ecf2f
Create Date: 2026-11-27 09:05:16.454976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b68f2d8a26f'
down_revision: Union[str, Sequence[str], None] = 'c4f1199ecf2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column(
            "default_compensation_type",
            sa.String(length=20),
            nullable=True,
        ),
    )
    op.add_column(
        "employees",
        sa.Column(
            "default_compensation_rate",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
    )

    op.create_check_constraint(
        "ck_employees_default_compensation_valid",
        "employees",
        """
        (
            default_compensation_type IS NULL
            AND default_compensation_rate IS NULL
        )
        OR
        (
            default_compensation_type IS NOT NULL
            AND default_compensation_rate IS NOT NULL
            AND default_compensation_type IN ('hourly', 'fixed')
            AND default_compensation_rate > 0
        )
        """,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_employees_default_compensation_valid",
        "employees",
        type_="check",
    )
    op.drop_column("employees", "default_compensation_rate")
    op.drop_column("employees", "default_compensation_type")