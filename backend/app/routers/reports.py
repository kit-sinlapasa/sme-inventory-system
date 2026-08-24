"""
CR-013 — endpoint สรุปผลสำหรับ dashboard เชิงวิเคราะห์

หลักการที่ใช้ทั้งไฟล์:

* **สรุปที่ฐานข้อมูล ไม่ใช่ที่เบราว์เซอร์** — endpoint รายการ (`/api/items`, `/api/stock`)
  มี limit เพื่อกันการดึงคลังทั้งใบ ถ้า frontend เอาไป group เองกราฟจะคำนวณจากข้อมูล
  ที่ถูกตัดทิ้งไปแล้วโดยไม่มีอะไรฟ้อง

* **NFR-SEC-02 — scope สาขาบังคับที่ server** ทุก endpoint ใช้ `_scope_branch()`
  ค่า branch_id ที่ client ส่งมาถูกละทิ้งทั้งหมดถ้าผู้ใช้เป็น BranchStaff

* **เวลาไทยเสมอ** — คอลัมน์เวลาเก็บเป็น UTC ตามมาตรฐาน แต่คำถามเชิงธุรกิจอย่าง
  "ขายดีวันไหน" / "วันนี้ขายได้เท่าไร" ต้องตอบตามวันตามปฏิทินไทย จึงต้อง
  `AT TIME ZONE 'Asia/Bangkok'` ก่อน truncate ทุกครั้ง ไม่งั้นยอดขายช่วงเย็น
  (17:00-23:59 น.) จะถูกนับเป็นวันถัดไป
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Integer, case, cast, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_any_role
from app.models.branch import Branch
from app.models.branch_sku import BranchSKU
from app.models.item import Item
from app.models.product import Product
from app.models.purchase_request import PurchaseRequest
from app.models.sale import Sale
from app.models.user import User
from app.schemas.report import (
    AgingBucket,
    BranchPerformance,
    DailySalesPoint,
    KpiSummary,
    PendingRequest,
    StockoutRisk,
    TopProduct,
    WeekdaySales,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])

BKK = "Asia/Bangkok"

# ช่วงเวลาที่หน้า dashboard เลือกได้ — จำกัดไว้เป็น whitelist ไม่ให้ client ส่งค่าอะไรก็ได้
# (days=100000 จะกลายเป็นการสแกนทั้งตารางทุกครั้งที่มีคนเปิดหน้า)
ALLOWED_DAYS = [7, 30, 90]


def _days(days: int = Query(30)) -> int:
    return days if days in ALLOWED_DAYS else 30


def _cutoff(days: int) -> datetime:
    """จุดเริ่มของช่วงที่ดู — คำนวณใน Python แล้วส่งเป็นพารามิเตอร์ ไม่ประกอบ SQL เป็นสตริง"""
    return datetime.now(timezone.utc) - timedelta(days=days)


def _scope_branch(current_user: User, branch_id: int | None) -> int | None:
    """NFR-SEC-02 — BranchStaff ถูกล็อกไว้ที่สาขาตัวเองเสมอ ไม่ว่าจะส่งพารามิเตอร์อะไรมา"""
    return current_user.branch_id if current_user.role == "BranchStaff" else branch_id


def _local_day(column):
    """แปลง timestamp เป็น 'วันที่' ตามปฏิทินไทย"""
    return func.date(func.timezone(BKK, column))


def _sales_in_window(db: Session, days: int, branch_id: int | None):
    """query ฐานของยอดขายในช่วงเวลา — ใช้ร่วมกันหลาย endpoint จะได้นิยาม 'ช่วง' ตรงกัน"""
    q = db.query(Sale).filter(Sale.sold_at >= _cutoff(days))
    if branch_id is not None:
        q = q.filter(Sale.branch_id == branch_id)
    return q


@router.get("/summary", response_model=KpiSummary)
def summary(
    days: int = Depends(_days),
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """ตัวเลข KPI หัวหน้าจอ พร้อมยอดของ 'ช่วงก่อนหน้าที่ยาวเท่ากัน' ไว้เทียบทิศทาง"""
    bid = _scope_branch(current_user, branch_id)

    on_hand_q = db.query(func.count(Item.id)).filter(Item.status == "InStock")
    # ใช้นิยามอายุเดียวกับถัง "180+" ของกราฟอายุสต็อก — ตัวเลขทั้งสองอยู่บนหน้าจอเดียวกัน
    dead_q = db.query(func.count(Item.id)).filter(
        Item.status == "InStock",
        ITEM_AGE_DAYS > DEAD_STOCK_DAYS,
    )
    if bid is not None:
        on_hand_q = on_hand_q.filter(Item.branch_id == bid)
        dead_q = dead_q.filter(Item.branch_id == bid)

    sold_now = _sales_in_window(db, days, bid).count()
    # ช่วงก่อนหน้า = [2*days ย้อนหลัง, days ย้อนหลัง) — ต้องกันขอบล่างด้วย ไม่งั้นจะนับซ้อนกัน
    prev_q = db.query(func.count(Sale.id)).filter(
        Sale.sold_at >= _cutoff(days * 2),
        Sale.sold_at < _cutoff(days),
    )
    if bid is not None:
        prev_q = prev_q.filter(Sale.branch_id == bid)

    # ใกล้หมด = ยอดคงเหลือ <= จุดสั่งซื้อ และมีการตั้งจุดสั่งซื้อไว้จริง (0 = ไม่ track)
    #
    # ตัวเลขนี้**รวมรายการที่ของหมดเกลี้ยงแล้ว (คงเหลือ 0)** ด้วย ซึ่งจงใจ เพราะของหมดคือ
    # กรณีที่แย่ที่สุดของ "ใกล้หมด" ไม่ใช่คนละเรื่อง · แต่ต้องระวังว่าตารางสต็อกด้านล่าง
    # นับรายการเหล่านี้ไม่ได้ เพราะ `/api/stock` JOIN กับ Item ที่ InStock อยู่ ถ้าไม่มีของ
    # เหลือเลยก็ไม่มีแถวให้ไฮไลต์ — จำนวนแถวแดงในตารางจึงน้อยกว่าเลข KPI เสมอ
    # หน้าจอต้องเขียนกำกับให้ชัดว่า KPI รวมของที่หมดแล้วด้วย ไม่งั้นดูเหมือนสองที่นับไม่ตรงกัน
    on_hand_sub = (
        db.query(func.count(Item.id))
        .filter(Item.sku_id == BranchSKU.sku_id, Item.branch_id == BranchSKU.branch_id, Item.status == "InStock")
        .scalar_subquery()
    )
    low_q = db.query(func.count(BranchSKU.id)).filter(BranchSKU.reorder_point > 0, on_hand_sub <= BranchSKU.reorder_point)
    out_q = db.query(func.count(BranchSKU.id)).filter(BranchSKU.reorder_point > 0, on_hand_sub == 0)
    pending_q = db.query(func.count(PurchaseRequest.id)).filter(PurchaseRequest.status == "Pending")
    if bid is not None:
        low_q = low_q.filter(BranchSKU.branch_id == bid)
        out_q = out_q.filter(BranchSKU.branch_id == bid)
        pending_q = pending_q.filter(PurchaseRequest.branch_id == bid)

    return KpiSummary(
        on_hand=on_hand_q.scalar(),
        sold_in_period=sold_now,
        sold_prev_period=prev_q.scalar(),
        low_stock_skus=low_q.scalar(),
        out_of_stock_skus=out_q.scalar(),
        dead_stock_items=dead_q.scalar(),
        pending_requests=pending_q.scalar(),
    )


@router.get("/daily-sales", response_model=list[DailySalesPoint])
def daily_sales(
    days: int = Depends(_days),
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """ยอดขายรายวันแยกตามสาขา — ข้อมูลของกราฟเส้นหลัก (หนึ่งเส้นต่อหนึ่งสาขา)"""
    bid = _scope_branch(current_user, branch_id)
    day = _local_day(Sale.sold_at).label("day")

    q = (
        db.query(day, Sale.branch_id, Branch.name.label("branch_name"), func.count(Sale.id).label("qty"))
        .join(Branch, Branch.id == Sale.branch_id)
        .filter(Sale.sold_at >= _cutoff(days))
        .group_by(day, Sale.branch_id, Branch.name)
        .order_by(day)
    )
    if bid is not None:
        q = q.filter(Sale.branch_id == bid)
    return [DailySalesPoint(day=r.day, branch_id=r.branch_id, branch_name=r.branch_name, qty=r.qty) for r in q.all()]


@router.get("/top-products", response_model=list[TopProduct])
def top_products(
    days: int = Depends(_days),
    limit: int = Query(10, le=50),
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """สินค้าขายดี — เรียงตามจำนวนชิ้นที่ขายได้ในช่วงที่เลือก"""
    bid = _scope_branch(current_user, branch_id)
    q = (
        db.query(Product.id, Product.category, Product.brand, Product.model, func.count(Sale.id).label("qty"))
        .join(Item, Item.sku_id == Product.id)
        .join(Sale, Sale.item_id == Item.id)
        .filter(Sale.sold_at >= _cutoff(days))
    )
    # ต้องกรองสาขาก่อน limit เสมอ — SQLAlchemy ไม่ยอมให้ filter หลัง limit
    # (ถ้ายอมจะยิ่งแย่: ได้ top 10 ของทุกสาขาแล้วค่อยตัดเหลือเฉพาะสาขาตัวเอง = ผิดความหมาย)
    if bid is not None:
        q = q.filter(Sale.branch_id == bid)
    q = (
        q.group_by(Product.id, Product.category, Product.brand, Product.model)
        .order_by(func.count(Sale.id).desc())
        .limit(limit)
    )
    return [
        TopProduct(sku_id=r.id, category=r.category, brand=r.brand, model=r.model, qty=r.qty) for r in q.all()
    ]


AGING_BUCKETS = ["0-30", "31-90", "91-180", "180+"]

# อายุของสินค้าเป็น "จำนวนวันเต็ม" — ต้องใช้นิยามเดียวกันทั้ง KPI และกราฟอายุสต็อก
# เพราะทั้งสองแสดงอยู่บนหน้าจอเดียวกัน ถ้านิยามต่างกันแม้แต่นิดเดียว
# (เช่น เทียบ timestamp ตรง ๆ ในที่หนึ่ง แต่ตัดเศษวันในอีกที่หนึ่ง)
# ตัวเลขจะไม่ตรงกัน 1-2 ชิ้นตลอดเวลาโดยไม่มีอะไรผิดพลาดให้เห็น
ITEM_AGE_DAYS = func.extract("day", func.now() - Item.received_at)
DEAD_STOCK_DAYS = 180

# ระยะเวลานำสั่ง — ของที่จะหมดภายในกี่วันถึงจะนับว่า "เสี่ยง"
# ตั้งไว้ 14 วันเพราะเป็นรอบสั่งของจากซัพพลายเออร์โดยประมาณของร้านอะไหล่คอม
# ถ้าธุรกิจจริงมีรอบสั่งต่างจากนี้ ให้แก้ค่านี้ค่าเดียว ไม่ต้องไล่แก้เงื่อนไขในโค้ด
RISK_HORIZON_DAYS = 14


@router.get("/stock-aging", response_model=list[AgingBucket])
def stock_aging(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """
    อายุของสินค้าที่ยังค้างในสต็อก — ตอบคำถาม "เงินจมอยู่กับของที่ไม่ขยับเท่าไร"
    ไม่ผูกกับช่วงเวลาที่เลือก เพราะเป็นภาพ ณ ปัจจุบัน ไม่ใช่ยอดสะสมในช่วง
    """
    bid = _scope_branch(current_user, branch_id)
    bucket = case(
        (ITEM_AGE_DAYS <= 30, "0-30"),
        (ITEM_AGE_DAYS <= 90, "31-90"),
        (ITEM_AGE_DAYS <= DEAD_STOCK_DAYS, "91-180"),
        else_="180+",
    ).label("bucket")

    q = db.query(bucket, func.count(Item.id).label("qty")).filter(Item.status == "InStock").group_by(bucket)
    if bid is not None:
        q = q.filter(Item.branch_id == bid)

    counts = {r.bucket: r.qty for r in q.all()}
    # คืนครบทุกถังเสมอ (ถังว่างเป็น 0) เพื่อให้แกนกราฟคงที่ ไม่กระโดดเวลาสลับสาขา
    return [AgingBucket(bucket=b, qty=counts.get(b, 0)) for b in AGING_BUCKETS]


@router.get("/branch-performance", response_model=list[BranchPerformance])
def branch_performance(
    days: int = Depends(_days),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """
    อัตราการระบายสต็อกต่อสาขา = ขายได้ / (ขายได้ + คงเหลือ)
    ตัวเลขนี้เทียบสาขาที่ขนาดต่างกันได้ ต่างจากยอดขายดิบที่สาขาใหญ่ชนะตลอดโดยไม่มีความหมาย
    """
    # ไม่รับ branch_id จาก client — endpoint นี้คือการ "เทียบสาขา" Admin จึงต้องเห็นทุกแถว
    # ส่วน BranchStaff เห็นเฉพาะแถวของตัวเอง (เทียบกับสาขาอื่นไม่ได้ ตาม NFR-SEC-02)
    bid = current_user.branch_id if current_user.role == "BranchStaff" else None

    sold_sub = (
        db.query(Sale.branch_id, func.count(Sale.id).label("sold"))
        .filter(Sale.sold_at >= _cutoff(days))
        .group_by(Sale.branch_id)
        .subquery()
    )
    on_hand_sub = (
        db.query(Item.branch_id, func.count(Item.id).label("on_hand"))
        .filter(Item.status == "InStock")
        .group_by(Item.branch_id)
        .subquery()
    )

    q = (
        db.query(
            Branch.id,
            Branch.name,
            func.coalesce(sold_sub.c.sold, 0).label("sold"),
            func.coalesce(on_hand_sub.c.on_hand, 0).label("on_hand"),
        )
        .outerjoin(sold_sub, sold_sub.c.branch_id == Branch.id)
        .outerjoin(on_hand_sub, on_hand_sub.c.branch_id == Branch.id)
        .order_by(Branch.id)
    )
    if bid is not None:
        q = q.filter(Branch.id == bid)

    result = []
    for r in q.all():
        total = r.sold + r.on_hand
        # 0/0 เกิดได้จริงกับสาขาที่ยังไม่เคยลงของ — ต้องเป็น None ไม่ใช่ 0%
        # เพราะ "ระบายไม่ได้เลย" กับ "ยังไม่มีอะไรให้ระบาย" คนละเรื่องกัน
        result.append(
            BranchPerformance(
                branch_id=r.id,
                branch_name=r.name,
                sold=r.sold,
                on_hand=r.on_hand,
                sell_through=round(r.sold / total, 4) if total else None,
            )
        )
    return result


@router.get("/weekday-sales", response_model=list[WeekdaySales])
def weekday_sales(
    days: int = Depends(_days),
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """
    ยอดขายรวมตามวันในสัปดาห์ (เวลาไทย) — ใช้วางแผนกำลังคนต่อวัน
    Postgres คืน DOW แบบ 0=อาทิตย์ จึงแปลงเป็น 0=จันทร์ ให้ตรงกับวิธีอ่านปฏิทินไทย
    """
    bid = _scope_branch(current_user, branch_id)
    pg_dow = func.extract("dow", func.timezone(BKK, Sale.sold_at))
    weekday = cast((pg_dow + 6) % 7, Integer).label("weekday")

    q = (
        db.query(weekday, func.count(Sale.id).label("qty"))
        .filter(Sale.sold_at >= _cutoff(days))
        .group_by(weekday)
    )
    if bid is not None:
        q = q.filter(Sale.branch_id == bid)

    counts = {r.weekday: r.qty for r in q.all()}
    return [WeekdaySales(weekday=d, qty=counts.get(d, 0)) for d in range(7)]


@router.get("/stockout-risk", response_model=list[StockoutRisk])
def stockout_risk(
    days: int = Depends(_days),
    limit: int = Query(15, le=50),
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """
    รายการที่เสี่ยงของขาด เรียงตาม "จะหมดในกี่วัน" ไม่ใช่แค่ยอดคงเหลือน้อย

    ยอดคงเหลือน้อยอย่างเดียวไม่ได้แปลว่าเสี่ยง — เหลือ 2 ชิ้นแต่ขายเดือนละชิ้นคือปลอดภัย
    ส่วนเหลือ 8 ชิ้นแต่ขายวันละ 2 ชิ้นคือใกล้หมดจริง หน้าจอเดิมแยกสองกรณีนี้ไม่ออก
    """
    bid = _scope_branch(current_user, branch_id)

    on_hand_sub = (
        db.query(Item.sku_id, Item.branch_id, func.count(Item.id).label("on_hand"))
        .filter(Item.status == "InStock")
        .group_by(Item.sku_id, Item.branch_id)
        .subquery()
    )
    sold_sub = (
        db.query(Item.sku_id, Sale.branch_id, func.count(Sale.id).label("sold"))
        .join(Sale, Sale.item_id == Item.id)
        .filter(Sale.sold_at >= _cutoff(days))
        .group_by(Item.sku_id, Sale.branch_id)
        .subquery()
    )

    q = (
        db.query(
            Product.id,
            Product.category,
            Product.brand,
            Product.model,
            BranchSKU.branch_id,
            Branch.name.label("branch_name"),
            BranchSKU.reorder_point,
            func.coalesce(on_hand_sub.c.on_hand, 0).label("on_hand"),
            func.coalesce(sold_sub.c.sold, 0).label("sold"),
        )
        .join(Product, Product.id == BranchSKU.sku_id)
        .join(Branch, Branch.id == BranchSKU.branch_id)
        .outerjoin(
            on_hand_sub,
            (on_hand_sub.c.sku_id == BranchSKU.sku_id) & (on_hand_sub.c.branch_id == BranchSKU.branch_id),
        )
        .outerjoin(
            sold_sub,
            (sold_sub.c.sku_id == BranchSKU.sku_id) & (sold_sub.c.branch_id == BranchSKU.branch_id),
        )
    )
    if bid is not None:
        q = q.filter(BranchSKU.branch_id == bid)

    rows = []
    for r in q.all():
        velocity = r.sold / days
        days_left = (r.on_hand / velocity) if velocity > 0 else None
        below_reorder = r.reorder_point and r.on_hand <= r.reorder_point
        # เข้าตารางเมื่อ "ต่ำกว่าจุดสั่งซื้อ" หรือ "ใกล้หมดภายในระยะเวลานำสั่ง" อย่างใดอย่างหนึ่ง
        if not below_reorder and (days_left is None or days_left > RISK_HORIZON_DAYS):
            continue
        rows.append(
            StockoutRisk(
                sku_id=r.id,
                category=r.category,
                brand=r.brand,
                model=r.model,
                branch_id=r.branch_id,
                branch_name=r.branch_name,
                on_hand=r.on_hand,
                reorder_point=r.reorder_point,
                daily_velocity=round(velocity, 3),
                days_left=round(days_left, 1) if days_left is not None else None,
            )
        )

    # ของที่ประมาณวันหมดไม่ได้ (ไม่เคยขาย) ไปท้ายตาราง — ด่วนน้อยกว่าของที่กำลังจะหมดจริง
    rows.sort(key=lambda x: (x.days_left is None, x.days_left if x.days_left is not None else 0))
    return rows[:limit]


@router.get("/pending-requests", response_model=list[PendingRequest])
def pending_requests(
    limit: int = Query(15, le=50),
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """คำขอสั่งซื้อที่ยังค้างพิจารณา เรียงจากที่ค้างนานที่สุด"""
    bid = _scope_branch(current_user, branch_id)
    age = func.extract("day", func.now() - PurchaseRequest.requested_at).label("age_days")

    q = (
        db.query(
            PurchaseRequest.id,
            PurchaseRequest.branch_id,
            Branch.name.label("branch_name"),
            Product.category,
            Product.brand,
            Product.model,
            PurchaseRequest.quantity,
            PurchaseRequest.requested_at,
            age,
        )
        .join(Branch, Branch.id == PurchaseRequest.branch_id)
        .join(Product, Product.id == PurchaseRequest.sku_id)
        .filter(PurchaseRequest.status == "Pending")
    )
    if bid is not None:  # กรองก่อน limit — เหตุผลเดียวกับ top_products
        q = q.filter(PurchaseRequest.branch_id == bid)
    q = q.order_by(PurchaseRequest.requested_at).limit(limit)

    return [
        PendingRequest(
            id=r.id,
            branch_id=r.branch_id,
            branch_name=r.branch_name,
            category=r.category,
            brand=r.brand,
            model=r.model,
            quantity=r.quantity,
            requested_at=r.requested_at.date(),
            age_days=int(r.age_days),
        )
        for r in q.all()
    ]
