from pydantic import BaseModel, ConfigDict, Field


class ReorderPointUpdate(BaseModel):
    reorder_point: int = Field(..., ge=0)


class BranchSKUOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int
    sku_id: int
    reorder_point: int
