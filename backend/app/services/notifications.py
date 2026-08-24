import logging
import smtplib
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_low_stock_alert(*, branch_name: str, product_label: str, on_hand: int, reorder_point: int) -> None:
    """
    FR-012 (CR-006) — ส่งอีเมลแจ้งเตือน Admin เมื่อสต็อกต่ำกว่าจุดสั่งซื้อ

    ตั้งใจไม่ raise exception ถ้าส่งไม่สำเร็จ — การขายสินค้า (business-critical,
    NFR-REL-01) ต้องไม่ถูกบล็อกเพราะอีเมลส่งไม่ได้ (เช่น SMTP down)

    ถ้าไม่ได้ตั้งค่า SMTP (dev/CI) จะ log แทนการส่งจริง — ไม่มีใครในทีมนี้เคย
    ให้ credential จริงกับ AI จึงทดสอบได้แค่ logic การตัดสินใจ "ควรส่งเมื่อไหร่"
    (ดู services/stock_alerts.py) ไม่ใช่การส่งอีเมลจริงเอง
    """
    if not settings.ALERT_EMAIL or not settings.SMTP_HOST:
        logger.info(
            "[low-stock-alert:dev-mode, ไม่ได้ตั้งค่า SMTP จริง] %s ที่ %s เหลือ %d ชิ้น (จุดสั่งซื้อ %d)",
            product_label,
            branch_name,
            on_hand,
            reorder_point,
        )
        return

    subject = f"[แจ้งเตือนสต็อก] {product_label} ที่ {branch_name} ใกล้หมด"
    body = (
        f"สินค้า: {product_label}\n"
        f"สาขา: {branch_name}\n"
        f"คงเหลือ: {on_hand}\n"
        f"จุดสั่งซื้อ: {reorder_point}\n\n"
        "กรุณาตรวจสอบและพิจารณาสร้างคำขอสั่งซื้อหากจำเป็น"
    )
    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USERNAME
    msg["To"] = settings.ALERT_EMAIL

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception:
        logger.exception("ส่งอีเมลแจ้งเตือนสต็อกไม่สำเร็จ — ไม่ทำให้ธุรกรรมหลักล้มเหลวตาม")
