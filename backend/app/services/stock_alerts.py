from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.branch_sku import BranchSKU
from app.models.item import Item
from app.models.product import Product
from app.services.notifications import send_low_stock_alert


def evaluate_low_stock_alert(db: Session, *, branch_id: int, sku_id: int, may_alert: bool = True) -> None:
    """
    FR-012 (CR-006) — เรียกหลัง event ที่เปลี่ยนยอดคงเหลือ (ขาย หรือ รับเข้า)
    เพื่อตัดสินใจว่าควรส่งแจ้งเตือนหรือควร reset debounce flag

    Debounce logic:
    - ยอดคงเหลือ <= reorder_point และยังไม่เคยแจ้งเตือนรอบนี้ (sent_at is None)
      → ส่งแจ้งเตือน 1 ครั้ง แล้วตั้ง sent_at (เฉพาะเมื่อ may_alert=True)
    - ยอดคงเหลือ <= reorder_point แต่เคยแจ้งเตือนไปแล้ว (sent_at is not None)
      → ไม่ส่งซ้ำ (กัน spam ทุกครั้งที่มีการขายขณะสต็อกยังต่ำ)
    - ยอดคงเหลือกลับมาเกิน reorder_point → เคลียร์ sent_at กลับเป็น None
      เพื่อให้รอบถัดไปที่ต่ำกว่าอีกครั้งแจ้งเตือนใหม่ได้

    may_alert=False (ใช้จากฝั่งรับเข้าสต็อก) — รับเข้าเป็นเหตุการณ์ "เพิ่มของ" ไม่ควรเป็นตัว
    จุดชนวนแจ้งเตือนใหม่แม้ว่ายอดหลังรับเข้าจะยังต่ำกว่า threshold อยู่ก็ตาม (เช่น รับเข้าทีละชิ้น
    ระหว่างที่ยอดยังไม่ผ่าน threshold) มีหน้าที่แค่ "เคลียร์" debounce flag เมื่อยอดข้ามกลับมาเกิน
    threshold เท่านั้น ส่วนการขาย (may_alert=True ค่า default) เป็นจุดเดียวที่จะยิงแจ้งเตือนใหม่ได้
    """
    branch_sku = (
        db.query(BranchSKU).filter(BranchSKU.branch_id == branch_id, BranchSKU.sku_id == sku_id).first()
    )
    if branch_sku is None:
        return  # ไม่ได้ตั้งค่า reorder point ไว้ ไม่มีอะไรให้ตรวจ

    on_hand = (
        db.query(Item)
        .filter(Item.branch_id == branch_id, Item.sku_id == sku_id, Item.status == "InStock")
        .count()
    )

    if on_hand <= branch_sku.reorder_point:
        if may_alert and branch_sku.low_stock_alert_sent_at is None:
            product = db.get(Product, sku_id)
            branch = db.get(Branch, branch_id)
            send_low_stock_alert(
                branch_name=branch.name if branch else f"สาขา #{branch_id}",
                product_label=f"{product.brand} {product.model}" if product else f"SKU #{sku_id}",
                on_hand=on_hand,
                reorder_point=branch_sku.reorder_point,
            )
            branch_sku.low_stock_alert_sent_at = datetime.now(timezone.utc)
            db.commit()
    else:
        if branch_sku.low_stock_alert_sent_at is not None:
            branch_sku.low_stock_alert_sent_at = None
            db.commit()
