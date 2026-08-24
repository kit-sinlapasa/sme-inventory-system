from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_branch_staff
from app.models.item import Item
from app.models.sale import Sale
from app.models.user import User
from app.schemas.sale import SaleCreate, SaleOut
from app.services.audit import write_audit_log
from app.services.stock_alerts import evaluate_low_stock_alert

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.post("", response_model=SaleOut, status_code=status.HTTP_201_CREATED)
def create_sale(
    payload: SaleCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_branch_staff),
):
    """
    บันทึกการขาย — ตาม ADR-002 (docs/03-Architecture-Design.md ส่วนที่ 3)
    รองรับ FR-004, FR-005, NFR-REL-01

    กลไก 2 ชั้น:
    1) Idempotency key — retry ซ้ำ (เน็ตช้า, กดซ้ำ) คืนผลลัพธ์เดิม ไม่สร้างรายการใหม่
    2) Conditional UPDATE — ขายได้ก็ต่อเมื่อ status ยัง 'InStock' ณ ขณะนั้นเท่านั้น
       ถ้ามี concurrent request หลายตัวแข่งกัน มีแค่ 1 ตัวที่ affected-row count > 0
    """
    # --- (1) Idempotency check ---
    existing = db.query(Sale).filter(Sale.idempotency_key == idempotency_key).first()
    if existing:
        return existing

    # --- บังคับ branch_id จาก token เสมอ ไม่เชื่อ client (STRIDE-T mitigation) ---
    branch_id = current_user.branch_id
    if branch_id is None:
        raise HTTPException(status_code=400, detail="Branch staff ต้องสังกัดสาขาก่อนบันทึกการขาย")

    # --- (2) Conditional Update — จุดวิกฤตของ NFR-REL-01 ---
    result = db.execute(
        update(Item)
        .where(
            Item.id == payload.item_id,
            Item.status == "InStock",
            Item.branch_id == branch_id,
        )
        .values(status="Sold")
    )

    if result.rowcount == 0:
        db.rollback()
        # ไม่มีแถวถูกแก้ = สินค้าถูกขายไปแล้ว (แพ้ race) หรือไม่อยู่ที่สาขานี้
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="สินค้านี้ถูกขายไปแล้ว หรือไม่พบในสาขาของคุณ",
        )

    item = db.get(Item, payload.item_id)
    warranty_expires_at = datetime.now(timezone.utc) + timedelta(days=30 * item.product.warranty_months)

    sale = Sale(
        item_id=item.id,
        buyer_name=payload.buyer_name,
        buyer_phone=payload.buyer_phone,
        branch_id=branch_id,
        warranty_expires_at=warranty_expires_at,
        idempotency_key=idempotency_key,
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)

    write_audit_log(
        db,
        actor=current_user,
        action="CREATE_SALE",
        entity_type="Sale",
        entity_id=sale.id,
        before={"item_id": item.id, "item_status": "InStock"},
        after={"item_id": item.id, "item_status": "Sold", "sale_id": sale.id},
    )

    # CR-006 — ขาย = สต็อกลด จุดที่ต้องเช็คว่าต่ำกว่า reorder point แล้วหรือยัง
    evaluate_low_stock_alert(db, branch_id=branch_id, sku_id=item.sku_id)

    return sale
