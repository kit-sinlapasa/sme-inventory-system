from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.limiter import limiter
from app.models.item import Item
from app.schemas.sale import WarrantyCheckOut

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/warranty/{serial_number}", response_model=WarrantyCheckOut)
@limiter.limit("30/minute")  # STRIDE-D mitigation — กัน scraping/enumeration S/N จำนวนมาก
def check_warranty(request: Request, serial_number: str, db: Session = Depends(get_db)):
    """
    FR-006 — ไม่ต้อง login
    NFR-SEC-01 — ห้ามคืนข้อมูลผู้ซื้อเด็ดขาด (บังคับโดย WarrantyCheckOut schema)
    """
    item = (
        db.query(Item)
        .options(joinedload(Item.product), joinedload(Item.sale))
        .filter(Item.serial_number == serial_number)
        .first()
    )

    if item is None or item.sale is None:
        # ตั้งใจไม่บอกความต่างระหว่าง "ไม่มี S/N นี้" กับ "มีแต่ยังไม่ขาย"
        # เพื่อไม่เปิดเผยข้อมูล stock ภายในผ่านช่องทางสาธารณะ
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูล กรุณาตรวจสอบ S/N อีกครั้ง")

    now = datetime.now(timezone.utc)
    status = "อยู่ในประกัน" if item.sale.warranty_expires_at > now else "หมดประกันแล้ว"

    return WarrantyCheckOut(
        model=f"{item.product.brand} {item.product.model}",
        warranty_status=status,
        warranty_expires_at=item.sale.warranty_expires_at,
    )
