from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ItemReceive(BaseModel):
    sku_id: int
    serial_number: str
    branch_id: int


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_id: int
    serial_number: str
    branch_id: int
    status: str
    received_at: datetime


class StockLevel(BaseModel):
    """แถวหนึ่งของผลลัพธ์ GET /api/stock — FR-003"""

    sku_id: int
    category: str
    brand: str
    model: str
    branch_id: int
    branch_name: str  # แสดงชื่อสาขาเต็มใน UI แทน "สาขา #1" ที่ผู้ใช้อ่านแล้วไม่รู้ว่าสาขาไหน
    on_hand: int
    reorder_point: int | None = None  # FR-012 — เห็นได้เฉพาะ role ที่มีสิทธิ์
