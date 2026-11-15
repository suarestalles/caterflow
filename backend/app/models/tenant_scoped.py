import uuid

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column


class TenantScoped:
    """Mixin for models that belong to a specific tenant."""

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
