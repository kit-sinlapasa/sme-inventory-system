from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PurchaseRequestCreate(BaseModel):
    sku_id: int
    quantity: int = Field(..., gt=0, description="ต้องมากกว่า 0 (US-06 AC)")


class PurchaseRequestReject(BaseModel):
    reason: str = Field(..., min_length=1, description="เหตุผลบังคับกรอก (US-07 AC)")


class PurchaseRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int
    sku_id: int
    quantity: int
    status: str
    requested_by: int
    requested_at: datetime
    decided_by: int | None
    decided_at: datetime | None
    reject_reason: str | None


class PurchaseOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pr_id: int
    created_by: int
    created_at: datetime
