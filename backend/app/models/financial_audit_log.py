
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.tenant_scoped import TenantScoped


class FinancialAuditLog(Abstract, TenantScoped):
    __tablename__ = "financial_audit_logs"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_financial_audit_logs_tenant_id_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "event_id"],
            ["events.tenant_id", "events.id"],
            name="fk_financial_audit_logs_tenant_event",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "entity_type IN ('expense', 'event_staff_assignment')",
            name="financial_audit_log_entity_type_valid",
        ),
        CheckConstraint(
            "length(trim(field_name)) > 0",
            name="financial_audit_log_field_name_not_empty",
        ),
        CheckConstraint(
            "length(trim(reason)) > 0",
            name="financial_audit_log_reason_not_empty",
        ),
        Index(
            "ix_financial_audit_logs_tenant_entity",
            "tenant_id",
            "entity_type",
            "entity_id",
        ),
        Index(
            "ix_financial_audit_logs_tenant_event",
            "tenant_id",
            "event_id",
        ),
        Index(
            "ix_financial_audit_logs_tenant_created_at",
            "tenant_id",
            "created_at",
        ),
    )

    event_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    entity_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )

    field_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    old_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    new_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    recorded_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_financial_audit_logs_recorded_by_user",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    tenant = relationship(
        "Tenant",
        back_populates="financial_audit_logs",
    )

    recorded_by = relationship("User")
