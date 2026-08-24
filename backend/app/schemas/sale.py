from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SaleCreate(BaseModel):
    item_id: int
    buyer_name: str
    buyer_phone: str


class SaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    buyer_name: str
    buyer_phone: str
    branch_id: int
    sold_at: datetime
    warranty_expires_at: datetime


class WarrantyCheckOut(BaseModel):
    """
    NFR-SEC-01 — schema นี้คือกำแพงป้องกันจริง ไม่ใช่แค่คอมเมนต์
    Pydantic จะ strip field ที่ไม่ได้ประกาศไว้ที่นี่ทิ้งอัตโนมัติ
    ห้ามเพิ่ม buyer_name / buyer_phone ใน schema นี้เด็ดขาด
    """

    model: str
    warranty_status: str
    warranty_expires_at: datetime
