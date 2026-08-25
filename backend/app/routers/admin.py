import smtplib
import socket
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import require_admin
from app.models.sale import Sale
from app.models.user import User
from app.schemas.admin import PurgeBuyerDataOut, SmtpCheckOut
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


def _redact(text: str) -> str:
    """
    กันไม่ให้ค่าลับหลุดออกไปกับข้อความ error — smtplib ปกติไม่ใส่รหัสผ่านมาใน error
    แต่เราไม่พึ่ง "ปกติ" กับข้อมูลประเภทนี้ ตัดทิ้งเองอีกชั้นหนึ่ง
    """
    for secret in (settings.SMTP_PASSWORD, settings.SMTP_USERNAME):
        if secret:
            text = text.replace(secret, "[ตัดออก]")
    return text[:300]


@router.get("/smtp-check", response_model=SmtpCheckOut)
def smtp_check(current_user: User = Depends(require_admin)):
    """
    เครื่องมือวินิจฉัยการตั้งค่าอีเมลแจ้งเตือน (FR-012) — **Admin เท่านั้น**

    เขียนขึ้นตอนที่ตั้งค่า SMTP บน production แล้วอีเมลไม่ออก และแยกไม่ได้ว่าเป็นเพราะ
    ตั้งค่าไม่ครบ / รหัสผ่านผิด / หรือผู้ให้บริการ hosting บล็อกการต่อออกพอร์ต SMTP
    ซึ่งทั้งสามอย่างมีอาการเหมือนกันหมดคือ "ไม่มีเมล"

    **ต่อจริงแต่ไม่ส่งเมลจริง** — แค่ connect + starttls + login แล้วตัดสาย
    จะได้ไม่รบกวนผู้รับทุกครั้งที่กดตรวจ

    **ไม่คืนค่าของตัวแปรใด ๆ** คืนแค่ว่าตั้งไว้หรือยัง (ดู SmtpCheckOut)
    """
    present = {
        "ALERT_EMAIL": bool(settings.ALERT_EMAIL),
        "SMTP_HOST": bool(settings.SMTP_HOST),
        "SMTP_PORT": bool(settings.SMTP_PORT),
        "SMTP_USERNAME": bool(settings.SMTP_USERNAME),
        "SMTP_PASSWORD": bool(settings.SMTP_PASSWORD),
        "SMTP_FROM": bool(settings.SMTP_FROM),
    }

    # เงื่อนไขเดียวกับที่ notifications.py ใช้ตัดสินใจว่าจะ log แทนการส่ง
    if not settings.ALERT_EMAIL or not settings.SMTP_HOST:
        return SmtpCheckOut(
            configured=False,
            settings_present=present,
            connection="not_configured",
            detail="ยังไม่ได้ตั้ง ALERT_EMAIL หรือ SMTP_HOST — ระบบจะ log แทนการส่งจริง (dev-mode)",
        )

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
    except smtplib.SMTPAuthenticationError as exc:
        return SmtpCheckOut(
            configured=True, settings_present=present, connection="auth_failed",
            detail=_redact(f"เซิร์ฟเวอร์ปฏิเสธการยืนยันตัวตน — มักเป็นเพราะ App Password ผิด "
                           f"ถูกลบไปแล้ว หรือยังไม่ได้เปิด 2-Step Verification ({exc.smtp_code})"),
        )
    except (socket.timeout, TimeoutError, ConnectionRefusedError, OSError) as exc:
        return SmtpCheckOut(
            configured=True, settings_present=present, connection="blocked",
            detail=_redact(f"ต่อไปยัง {settings.SMTP_HOST}:{settings.SMTP_PORT} ไม่ได้ — "
                           f"มักเป็นเพราะผู้ให้บริการ hosting บล็อก outbound SMTP ({type(exc).__name__}: {exc})"),
        )
    except Exception as exc:  # noqa: BLE001 — endpoint วินิจฉัย ต้องรายงานทุกกรณีไม่ให้ 500
        return SmtpCheckOut(
            configured=True, settings_present=present, connection="error",
            detail=_redact(f"{type(exc).__name__}: {exc}"),
        )

    return SmtpCheckOut(
        configured=True, settings_present=present, connection="ok",
        detail="เชื่อมต่อและยืนยันตัวตนกับเซิร์ฟเวอร์ SMTP สำเร็จ — การตั้งค่าใช้งานได้จริง",
    )
