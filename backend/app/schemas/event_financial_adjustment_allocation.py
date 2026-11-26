
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventFinancialAdjustmentAllocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    adjustment_id: UUID
    installment_id: UUID
    allocated_amount: Decimal
    created_at: datetime
    updated_at: datetime
