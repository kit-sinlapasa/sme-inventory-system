"""
CR-013 — schema ของ dashboard เชิงวิเคราะห์

ทุก endpoint ในกลุ่มนี้คืน "ผลสรุป" ไม่ใช่รายการดิบ เพราะถ้าให้ frontend ดึงรายการทั้งหมด
มา group เองจะเจอปัญหาสองข้อพร้อมกัน:
  1) endpoint รายการมี limit (200/500 แถว) — กราฟจะถูกคำนวณจากข้อมูลที่ถูกตัดไปแล้ว
     โดยที่หน้าจอยังเรนเดอร์ออกมาสวยงามเหมือนถูกต้อง จับไม่ได้ด้วยตาเปล่า
  2) ปัจจุบันมีสินค้า ~1,200 ชิ้นและการขาย ~900 รายการ ส่งทั้งหมดมาให้เบราว์เซอร์
     เพื่อจะแสดงกราฟ 12 จุดเป็นการเปลืองแบนด์วิดท์โดยไม่จำเป็น
"""
from datetime import date

from pydantic import BaseModel


class KpiSummary(BaseModel):
    """ตัวเลขหัวหน้าจอ — เทียบกับช่วงก่อนหน้าที่ยาวเท่ากันเพื่อบอกทิศทาง ไม่ใช่แค่ค่าปัจจุบัน"""

    on_hand: int
    sold_in_period: int
    sold_prev_period: int
    low_stock_skus: int  # รวมรายการที่ของหมดแล้ว — ของหมดคือกรณีแย่ที่สุดของ "ใกล้หมด"
    out_of_stock_skus: int  # ส่วนย่อยของ low_stock_skus ที่คงเหลือ = 0 (ตารางสต็อกแสดงไม่ได้)
    dead_stock_items: int  # ค้างเกิน 180 วัน — นิยามอายุเดียวกับถัง '180+' ของกราฟอายุสต็อก
    pending_requests: int


class DailySalesPoint(BaseModel):
    day: date
    branch_id: int
    branch_name: str
    qty: int


class TopProduct(BaseModel):
    sku_id: int
    category: str
    brand: str
    model: str
    qty: int


class AgingBucket(BaseModel):
    bucket: str  # '0-30' | '31-90' | '91-180' | '180+'
    qty: int


class BranchPerformance(BaseModel):
    branch_id: int
    branch_name: str
    sold: int
    on_hand: int
    sell_through: float | None  # None = ไม่มีทั้งของขายและของเหลือ คำนวณไม่ได้ (ไม่ใช่ 0%)


class WeekdaySales(BaseModel):
    weekday: int  # 0 = จันทร์ ... 6 = อาทิตย์ (เวลาไทย)
    qty: int


class StockoutRisk(BaseModel):
    sku_id: int
    category: str
    brand: str
    model: str
    branch_id: int
    branch_name: str
    on_hand: int
    reorder_point: int | None
    daily_velocity: float
    days_left: float | None  # None = ไม่เคยขายในช่วงที่ดู จึงประมาณวันหมดไม่ได้


class PendingRequest(BaseModel):
    id: int
    branch_id: int
    branch_name: str
    category: str
    brand: str
    model: str
    quantity: int
    requested_at: date
    age_days: int
