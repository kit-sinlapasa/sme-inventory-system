from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_any_role
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

    query = (
        db.query(
            Product.id.label("sku_id"),
            Product.category,
            Product.brand,
            Product.model,
            Item.branch_id,
            func.count(Item.id).label("on_hand"),
        )
        .join(Item, Item.sku_id == Product.id)
        .filter(Item.status == "InStock")
        .group_by(Product.id, Product.category, Product.brand, Product.model, Item.branch_id)
    )

    if effective_branch_id is not None:
        query = query.filter(Item.branch_id == effective_branch_id)
    if sku_id is not None:
        query = query.filter(Product.id == sku_id)

    rows = query.all()

    # เติม reorder_point ต่อแถว (FR-012, CR-002 — ต่อ SKU ต่อสาขา)
    result = []
    for row in rows:
        branch_sku = (
            db.query(BranchSKU)
            .filter(BranchSKU.branch_id == row.branch_id, BranchSKU.sku_id == row.sku_id)
            .first()
        )
        result.append(
            StockLevel(
                sku_id=row.sku_id,
                category=row.category,
                brand=row.brand,
                model=row.model,
                branch_id=row.branch_id,
                on_hand=row.on_hand,
                reorder_point=branch_sku.reorder_point if branch_sku else None,
            )
        )
    return result
