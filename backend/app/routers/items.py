from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin, require_any_role
from app.models.item import Item
from app.models.product import Product
from app.models.user import User
from app.schemas.item import ItemOut, ItemReceive
from app.services.audit import write_audit_log
from app.services.stock_alerts import evaluate_low_stock_alert

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("/by-serial/{serial_number}", response_model=ItemOut)
def get_item_by_serial(
    serial_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """
    ใช้ตอนบันทึกขาย (US-04) — พนักงานกรอก/สแกน S/N บนกล่องจริง ต้อง resolve
    เป็น item_id ก่อนยิง POST /api/sales (endpoint นั้นรับแค่ item_id ไม่รับ serial ตรง ๆ)

    NFR-SEC-02 — Branch เห็นได้เฉพาะของสาขาตัวเอง item ของสาขาอื่นคืน 404
    เหมือน "ไม่พบ" (ไม่ใช่ 403) เพื่อไม่เปิดเผยว่า S/N นั้นมีอยู่ที่สาขาอื่นหรือไม่
    (ตรรกะเดียวกับ public warranty endpoint — ไม่แยกแยะ "ไม่มี" กับ "มีแต่เข้าไม่ได้")
    """
    item = db.query(Item).filter(Item.serial_number == serial_number).first()
    if item is None:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้าที่มี S/N นี้")
    if current_user.role == "BranchStaff" and item.branch_id != current_user.branch_id:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้าที่มี S/N นี้")
    return item


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def receive_item(
    payload: ItemReceive,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # NFR-SEC-02 — Admin เท่านั้นรับเข้าสต็อกได้
):
    """FR-002 — รับสินค้าเข้าสต็อกเป็นรายชิ้นพร้อม S/N"""
    product = db.get(Product, payload.sku_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=400, detail="ไม่พบ SKU นี้ หรือถูกระงับแล้ว")

    item = Item(sku_id=payload.sku_id, serial_number=payload.serial_number, branch_id=payload.branch_id)
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="S/N นี้มีอยู่แล้วในระบบ")
    db.refresh(item)

    write_audit_log(
        db,
        actor=current_user,
        action="RECEIVE_ITEM",
        entity_type="Item",
        entity_id=item.id,
        before=None,
        after={"serial_number": item.serial_number, "branch_id": item.branch_id, "status": "InStock"},
    )

    # CR-006 — รับเข้า = สต็อกเพิ่ม จุดที่ต้อง reset debounce flag ถ้าเพิ่งเติมกลับมาเกิน threshold
    # may_alert=False — ห้ามให้ event รับเข้าเป็นตัวยิงแจ้งเตือนใหม่ (ดูเหตุผลใน stock_alerts.py)
    evaluate_low_stock_alert(db, branch_id=item.branch_id, sku_id=item.sku_id, may_alert=False)

    return item
