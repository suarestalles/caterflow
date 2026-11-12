import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract import Abstract


class RefreshToken(Abstract):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    family_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        index=True,
        default=uuid.uuid4,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    replaced_by_token_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
        nullable=True,
    )

    user = relationship(
        "User",
        back_populates="refresh_tokens",
    )

    replaced_by = relationship(
        "RefreshToken",
        remote_side="RefreshToken.id",
        foreign_keys=[replaced_by_token_id],
        uselist=False,
    )
