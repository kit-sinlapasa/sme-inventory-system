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


class PurchaseHistoryOut(BaseModel):
    """
    FR-015 (CR-014) — ประวัติการซื้อของลูกค้าหนึ่งราย สำหรับพนักงานใช้ตอนลูกค้ามาเคลม

    ตั้งใจ **ไม่ใส่ `buyer_phone` กลับมา** — ผู้เรียกเป็นคนพิมพ์เบอร์เข้ามาเองอยู่แล้ว
    การส่งกลับไม่ได้เพิ่มประโยชน์ แต่เพิ่มโอกาสที่เบอร์ลูกค้าจะไปโผล่ใน log/cache ของ client
    """

    model_config = ConfigDict(from_attributes=True)

    sale_id: int
    serial_number: str
    category: str
    brand: str
    model: str
    branch_name: str
    buyer_name: str
    sold_at: datetime
    warranty_expires_at: datetime
    warranty_status: str
