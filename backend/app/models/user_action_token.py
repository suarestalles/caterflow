
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.abstract import Abstract


class UserActionToken(Abstract):
    __tablename__ = "user_action_tokens"

    __table_args__ = (
        UniqueConstraint(
            "token_hash",
            name="uq_user_action_tokens_token_hash",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "role_id"],
            ["roles.tenant_id", "roles.id"],
            name="fk_user_action_tokens_tenant_role",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            """
            (
                purpose = 'tenant_invitation'
                AND tenant_id IS NOT NULL
                AND role_id IS NOT NULL
            )
            OR
            (
                purpose != 'tenant_invitation'
                AND tenant_id IS NULL
                AND role_id IS NULL
            )
            """,
            name="valid_tenant_role",
        ),
        CheckConstraint(
            """
            purpose != 'password_reset'
            OR user_id IS NOT NULL
            """,
            name="password_reset_requires_user",
        ),
        CheckConstraint(
            """
            purpose IN (
                'platform_invitation',
                'tenant_invitation',
                'password_reset'
            )
            """,
            name="valid_purpose",
        ),
        CheckConstraint(
            "email = lower(email)",
            name="email_lowercase",
        ),
        Index("ix_user_action_tokens_user_id", "user_id"),
        Index("ix_user_action_tokens_tenant_id", "tenant_id"),
        Index("ix_user_action_tokens_purpose", "purpose"),
        Index("ix_user_action_tokens_expires_at", "expires_at"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )

    role_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
    )

    invited_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    purpose: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
