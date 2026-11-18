from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.abstract import Abstract
from app.models.tenant_scoped import TenantScoped


class QuoteItem(Abstract, TenantScoped):
    __tablename__ = "quote_items"

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "quote_id"],
            ["quotes.tenant_id", "quotes.id"],
            name="fk_quote_items_tenant_quote",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "quantity > 0",
            name="quote_item_quantity_positive",
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="quote_item_unit_price_nonnegative",
        ),
        CheckConstraint(
            "total_price >= 0",
            name="quote_item_total_price_nonnegative",
        ),
    )

    quote_id: Mapped[UUID] = mapped_column(nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    quote = relationship(
        "Quote",
        back_populates="items",
        primaryjoin=lambda: (
            (Quote.id == foreign(QuoteItem.quote_id))
            & (Quote.tenant_id == QuoteItem.tenant_id)
        ),
    )


from app.models.quote import Quote
