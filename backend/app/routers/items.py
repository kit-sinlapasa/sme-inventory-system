from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.models.item import Item
from app.models.product import Product
from app.models.user import User
from app.schemas.item import ItemOut, ItemReceive
from app.services.audit import write_audit_log

router = APIRouter(prefix="/api/items", tags=["items"])


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
    return item
