from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import require_admin
from app.models.sale import Sale
from app.models.user import User
from app.schemas.admin import PurgeBuyerDataOut
from app.services.audit import write_audit_log

router = APIRouter(prefix="/api/admin", tags=["admin"])

ANONYMIZED_NAME = "ลูกค้า (ข้อมูลถูกลบตามนโยบายความเป็นส่วนตัว)"
ANONYMIZED_PHONE = "0000000000"


@router.post("/purge-old-buyer-data", response_model=PurgeBuyerDataOut)
def purge_old_buyer_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # NFR-PRIV-01 — Admin เท่านั้น
):
    """
    NFR-PRIV-01 (CR-001) — ลบ/anonymize ข้อมูลผู้ซื้อ (ชื่อ/เบอร์โทร) ของ Sale ที่หมดประกัน
    มาแล้วเกิน DATA_RETENTION_YEARS ปี — เก็บ Sale/warranty record ไว้เหมือนเดิม (ยังตรวจ
    ประกันย้อนหลังได้ผ่าน FR-006) แค่ anonymize เฉพาะข้อมูลระบุตัวตนผู้ซื้อ

    ตัดสินใจตาม CR-005: ทำเป็นฟังก์ชัน **manual** ที่ Admin กดเรียกเอง ไม่ใช่ background job
    อัตโนมัติ (ลดขอบเขตให้เหมาะกับเวลาที่มี แต่ยังมี evidence จริงว่าทำงานได้)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=365 * settings.DATA_RETENTION_YEARS)

    eligible = (
        db.query(Sale)
        .filter(Sale.warranty_expires_at < cutoff, Sale.buyer_data_purged.is_(False))
        .all()
    )

    purged_ids = []
    for sale in eligible:
        sale.buyer_name = ANONYMIZED_NAME
        sale.buyer_phone = ANONYMIZED_PHONE
        sale.buyer_data_purged = True
        purged_ids.append(sale.id)
    db.commit()

    write_audit_log(
        db,
        actor=current_user,
        action="PURGE_OLD_BUYER_DATA",
        entity_type="Sale",
        entity_id=0,  # เป็น bulk operation ไม่ผูกกับ entity เดียว — รายการ id เต็มอยู่ใน after_value
        before=None,
        after={"purged_sale_ids": purged_ids, "cutoff": cutoff.isoformat(), "count": len(purged_ids)},
    )

    return PurgeBuyerDataOut(purged_count=len(purged_ids), cutoff=cutoff)
