import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.abstract import Abstract


class PlatformAdmin(Abstract):
    __tablename__ = "platform_admins"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_platform_admins_user_id",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
