from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_any_role
from app.models.branch import Branch
from app.models.branch_sku import BranchSKU
from app.models.item import Item
from app.models.product import Product
from app.models.user import User
from app.schemas.item import StockLevel

router = APIRouter(prefix="/api/stock", tags=["stock"])


@router.get("", response_model=list[StockLevel])
def get_stock(
    branch_id: int | None = Query(None, description="Admin เท่านั้นที่กรองได้อิสระ"),
    sku_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """
    FR-003 — ยอดคงเหลือแบบเรียลไทม์ (COUNT สด ไม่ cache) แยกตาม SKU และสาขา
    NFR-SEC-02 — Branch เห็นได้เฉพาะสต็อกของสาขาตัวเองเท่านั้น ไม่ว่าจะส่ง branch_id
    parameter มาเป็นอะไรก็ตาม (บังคับที่ server ไม่เชื่อ client)
    """
    effective_branch_id = current_user.branch_id if current_user.role == "BranchStaff" else branch_id

    # reorder_point (FR-012, CR-002 — ต่อ SKU ต่อสาขา) ดึงมาพร้อมกันใน query เดียว
    #
    # เดิมวนลูปผลลัพธ์แล้วยิง query หา BranchSKU ทีละแถว = N+1 วัดจริงได้ 172 query
    # สำหรับ 170 แถว · ปัญหานี้โตตามจำนวนข้อมูล ไม่ใช่ค่าคงที่ พอสต็อกเยอะขึ้นจะช้าลง
    # เรื่อย ๆ โดยที่โค้ดหน้าตาเหมือนเดิมทุกบรรทัด
    #
    # ใช้ outerjoin เพราะสินค้าที่มีของในสาขาแต่ยังไม่เคยตั้งจุดสั่งซื้อต้องยังขึ้นในผลลัพธ์
    # (reorder_point = None) ถ้าใช้ join ธรรมดาแถวเหล่านั้นจะหายไปเงียบ ๆ
    #
    # ใส่ reorder_point ใน group_by ได้อย่างปลอดภัยเพราะ BranchSKU มี
    # UniqueConstraint("branch_id", "sku_id") — หนึ่งคู่มีได้แถวเดียว จึงแตกกลุ่มเพิ่มไม่ได้
    query = (
        db.query(
            Product.id.label("sku_id"),
            Product.category,
            Product.brand,
            Product.model,
            Item.branch_id,
            Branch.name.label("branch_name"),
            func.count(Item.id).label("on_hand"),
            BranchSKU.reorder_point,
        )
        .join(Item, Item.sku_id == Product.id)
        .join(Branch, Branch.id == Item.branch_id)
        .outerjoin(
            BranchSKU,
            (BranchSKU.sku_id == Product.id) & (BranchSKU.branch_id == Item.branch_id),
        )
        .filter(Item.status == "InStock")
        .group_by(
            Product.id,
            Product.category,
            Product.brand,
            Product.model,
            Item.branch_id,
            Branch.name,
            BranchSKU.reorder_point,
        )
    )

    if effective_branch_id is not None:
        query = query.filter(Item.branch_id == effective_branch_id)
    if sku_id is not None:
        query = query.filter(Product.id == sku_id)

    return [
        StockLevel(
            sku_id=row.sku_id,
            category=row.category,
            brand=row.brand,
            model=row.model,
            branch_id=row.branch_id,
            branch_name=row.branch_name,
            on_hand=row.on_hand,
            reorder_point=row.reorder_point,
        )
        for row in query.all()
    ]
