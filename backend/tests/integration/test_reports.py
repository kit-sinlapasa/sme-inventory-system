"""
CR-013 — test สำหรับ endpoint สรุปผลของ dashboard

จุดที่ตั้งใจทดสอบเป็นพิเศษ (เพราะเป็นจุดที่ "พังแล้วหน้าจอยังดูปกติ"):

* **scope สาขา** — BranchStaff ส่ง branch_id ของสาขาอื่นมาต้องไม่ได้ข้อมูลสาขานั้น
  ข้อบกพร่องแบบนี้ไม่มีอะไรฟ้องบนหน้าจอเลย กราฟยังเรนเดอร์สวยเหมือนเดิม

* **กรองก่อน limit** — top-products/pending-requests เคยเขียน `.limit()` ไว้ก่อน
  `.filter()` จริง ๆ ตอนพัฒนา ซึ่งถ้าไม่มี test จะเจอเฉพาะตอนผู้ใช้ระดับสาขาเปิดหน้า

* **แบ่งวันตามเวลาไทย** — ยอดขายเวลา 23:00 น. ของไทยคือ 16:00 UTC ถ้าจัดกลุ่มด้วย UTC
  รายการนั้นจะถูกนับเป็นวันเดียวกัน แต่ถ้าขายเวลา 01:00 น. ไทย (18:00 UTC วันก่อน)
  จะถูกนับผิดวันทันที — test นี้จับตรงนั้น
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.models.item import Item
from app.models.purchase_request import PurchaseRequest
from app.models.sale import Sale

BKK = timezone(timedelta(hours=7))


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def _sell(db, *, product, branch, serial, sold_at, received_days_before=10):
    """สร้างของหนึ่งชิ้นที่ขายไปแล้ว ณ เวลาที่กำหนด"""
    item = Item(
        sku_id=product.id,
        serial_number=serial,
        branch_id=branch.id,
        status="Sold",
        received_at=sold_at - timedelta(days=received_days_before),
    )
    db.add(item)
    db.flush()
    db.add(
        Sale(
            item_id=item.id,
            buyer_name="ผู้ซื้อทดสอบ",
            buyer_phone="0812345678",
            branch_id=branch.id,
            sold_at=sold_at,
            warranty_expires_at=sold_at + timedelta(days=365),
        )
    )
    db.commit()
    return item


@pytest.fixture()
def other_product(db):
    from app.models.product import Product

    p = Product(category="CPU", brand="OtherBrand", model="OB-9", warranty_months=36)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ── scope สาขา (NFR-SEC-02) ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    "path",
    [
        "/api/reports/daily-sales",
        "/api/reports/stockout-risk",
        "/api/reports/pending-requests",
        "/api/reports/stock-aging",
        "/api/reports/top-products",
    ],
)
def test_branch_staff_cannot_read_other_branch(
    client, db, branch, other_branch, product, branch_staff_token, path
):
    """ส่ง branch_id ของสาขาอื่นมาตรง ๆ ต้องไม่ได้ข้อมูลของสาขานั้นกลับไป"""
    now = datetime.now(timezone.utc)
    _sell(db, product=product, branch=other_branch, serial="SN-OTHER-1", sold_at=now - timedelta(days=1))
    db.add(Item(sku_id=product.id, serial_number="SN-OTHER-2", branch_id=other_branch.id, status="InStock"))
    db.commit()

    resp = client.get(f"{path}?branch_id={other_branch.id}", headers=auth(branch_staff_token))
    assert resp.status_code == 200
    rows = resp.json()

    # ทุก endpoint ที่มีคอลัมน์สาขา ต้องไม่มีสาขาอื่นโผล่มา
    assert all(r.get("branch_id", branch.id) == branch.id for r in rows), rows
    # endpoint ที่ไม่มีคอลัมน์สาขา (aging/top-products) ต้องนับได้ 0 เพราะสาขาตัวเองไม่มีของ
    if path in ("/api/reports/stock-aging", "/api/reports/top-products"):
        assert sum(r["qty"] for r in rows) == 0


def test_branch_performance_shows_only_own_branch(
    client, db, branch, other_branch, product, branch_staff_token, admin_token
):
    """ตารางเทียบสาขา: Admin เห็นทุกสาขา / BranchStaff เห็นแถวเดียวคือสาขาตัวเอง"""
    staff_rows = client.get("/api/reports/branch-performance", headers=auth(branch_staff_token)).json()
    assert [r["branch_id"] for r in staff_rows] == [branch.id]

    admin_rows = client.get("/api/reports/branch-performance", headers=auth(admin_token)).json()
    assert {r["branch_id"] for r in admin_rows} == {branch.id, other_branch.id}


def test_sell_through_is_none_when_branch_has_nothing(client, other_branch, admin_token):
    """
    สาขาที่ยังไม่เคยลงของเลย: 0/0 คำนวณไม่ได้ ต้องเป็น None ไม่ใช่ 0%
    "ระบายไม่ได้เลย" กับ "ยังไม่มีอะไรให้ระบาย" เป็นคนละสถานการณ์ทางธุรกิจ
    """
    rows = client.get("/api/reports/branch-performance", headers=auth(admin_token)).json()
    empty = next(r for r in rows if r["branch_id"] == other_branch.id)
    assert empty["sell_through"] is None
    assert empty["sold"] == 0 and empty["on_hand"] == 0


# ── กรองก่อน limit ────────────────────────────────────────────────────────────


def test_top_products_limit_applies_after_branch_filter(
    client, db, branch, other_branch, product, other_product, branch_staff_token
):
    """
    สาขาอื่นขายสินค้า A เยอะมาก สาขาตัวเองขายสินค้า B น้อย ๆ
    ถ้า limit ถูกใช้ก่อนกรองสาขา สินค้า A จะกินโควตาจนสาขาตัวเองได้ผลลัพธ์ว่าง
    """
    now = datetime.now(timezone.utc)
    for i in range(5):
        _sell(db, product=product, branch=other_branch, serial=f"SN-BIG-{i}", sold_at=now - timedelta(days=2))
    _sell(db, product=other_product, branch=branch, serial="SN-MINE-1", sold_at=now - timedelta(days=2))

    rows = client.get("/api/reports/top-products?limit=1", headers=auth(branch_staff_token)).json()
    assert len(rows) == 1
    assert rows[0]["sku_id"] == other_product.id
    assert rows[0]["qty"] == 1


def test_pending_requests_limit_applies_after_branch_filter(
    client, db, branch, other_branch, product, branch_staff_user, branch_staff_token
):
    """คำขอเก่าจำนวนมากของสาขาอื่นต้องไม่เบียดคำขอของสาขาตัวเองออกจากผลลัพธ์"""
    old = datetime.now(timezone.utc) - timedelta(days=60)
    for _ in range(5):
        db.add(
            PurchaseRequest(
                branch_id=other_branch.id, sku_id=product.id, quantity=1,
                status="Pending", requested_by=branch_staff_user.id, requested_at=old,
            )
        )
    db.add(
        PurchaseRequest(
            branch_id=branch.id, sku_id=product.id, quantity=7, status="Pending",
            requested_by=branch_staff_user.id, requested_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
    )
    db.commit()

    rows = client.get("/api/reports/pending-requests?limit=2", headers=auth(branch_staff_token)).json()
    assert len(rows) == 1
    assert rows[0]["branch_id"] == branch.id and rows[0]["quantity"] == 7


# ── การแบ่งวันตามเวลาไทย ─────────────────────────────────────────────────────


def test_daily_sales_groups_by_thai_calendar_day(client, db, branch, product, admin_token):
    """
    ขายสองครั้งในวันเดียวกันตามปฏิทินไทย (09:00 และ 23:00 น.)
    23:00 น. ไทย = 16:00 UTC วันเดียวกัน จึงยังไม่ข้ามวันแม้จัดกลุ่มด้วย UTC —
    เคสที่แยกความต่างได้จริงคือ 01:00 น. ไทย ซึ่งเป็น 18:00 UTC ของ "เมื่อวาน"
    """
    # เลือกวันฐานที่แน่นอน แล้วสร้าง 01:00 น. ตามเวลาไทยของวันนั้น
    base = (datetime.now(BKK) - timedelta(days=3)).replace(hour=1, minute=30, second=0, microsecond=0)
    _sell(db, product=product, branch=branch, serial="SN-EARLY", sold_at=base)
    _sell(db, product=product, branch=branch, serial="SN-NOON", sold_at=base.replace(hour=14))

    rows = client.get("/api/reports/daily-sales?days=7", headers=auth(admin_token)).json()
    days = {r["day"]: r["qty"] for r in rows}
    # ทั้งสองรายการต้องอยู่วันเดียวกัน = วันตามปฏิทินไทย ไม่ใช่แตกเป็นสองวันตาม UTC
    assert days == {base.date().isoformat(): 2}, rows


def test_weekday_sales_uses_thai_weekday(client, db, branch, product, admin_token):
    """
    ขายเวลา 01:00 น. วันจันทร์ (เวลาไทย) = 18:00 UTC วันอาทิตย์
    ต้องถูกนับเป็น "วันจันทร์" (weekday 0) ไม่ใช่วันอาทิตย์
    """
    now = datetime.now(BKK)
    # ถอยหาวันจันทร์ล่าสุดที่อยู่ในช่วง 7 วัน แล้วตั้งเวลา 01:00 น.
    monday = (now - timedelta(days=(now.weekday() + 7) % 7 or 7)).replace(
        hour=1, minute=0, second=0, microsecond=0
    )
    assert monday.weekday() == 0
    _sell(db, product=product, branch=branch, serial="SN-MON-1AM", sold_at=monday)

    rows = client.get("/api/reports/weekday-sales?days=30", headers=auth(admin_token)).json()
    by_day = {r["weekday"]: r["qty"] for r in rows}
    assert sorted(by_day) == list(range(7))  # คืนครบ 7 วันเสมอ แม้วันที่ไม่มียอดขาย
    assert by_day[0] == 1, by_day
    assert by_day[6] == 0, by_day  # ต้องไม่ตกไปอยู่วันอาทิตย์


# ── พฤติกรรมอื่นที่ผิดง่าย ────────────────────────────────────────────────────


def test_days_parameter_is_whitelisted(client, db, branch, product, admin_token):
    """ค่า days นอก whitelist ต้องถูกบังคับกลับเป็น 30 ไม่ใช่สแกนทั้งตาราง"""
    now = datetime.now(timezone.utc)
    _sell(db, product=product, branch=branch, serial="SN-OLD", sold_at=now - timedelta(days=200))
    _sell(db, product=product, branch=branch, serial="SN-NEW", sold_at=now - timedelta(days=3))

    assert client.get("/api/reports/summary?days=99999", headers=auth(admin_token)).json()["sold_in_period"] == 1
    assert client.get("/api/reports/summary?days=90", headers=auth(admin_token)).json()["sold_in_period"] == 1
    # 200 วันก่อนอยู่นอกช่วงสูงสุด (90) จึงต้องไม่ถูกนับไม่ว่าจะขอ days เท่าไร


def test_summary_previous_period_does_not_overlap(client, db, branch, product, admin_token):
    """ช่วงก่อนหน้าต้องเป็น [60,30) วัน ไม่ใช่ [60,0] — ไม่งั้นยอดปัจจุบันถูกนับซ้ำในช่วงเทียบ"""
    now = datetime.now(timezone.utc)
    _sell(db, product=product, branch=branch, serial="SN-NOW", sold_at=now - timedelta(days=5))
    _sell(db, product=product, branch=branch, serial="SN-PREV", sold_at=now - timedelta(days=45))

    body = client.get("/api/reports/summary?days=30", headers=auth(admin_token)).json()
    assert body["sold_in_period"] == 1
    assert body["sold_prev_period"] == 1


def test_stock_aging_returns_all_buckets_even_when_empty(client, db, branch, product, admin_token):
    """แกนกราฟต้องคงที่ — ถังที่ไม่มีของต้องคืน 0 ไม่ใช่หายไปทั้งถัง"""
    db.add(
        Item(
            sku_id=product.id, serial_number="SN-AGE-OLD", branch_id=branch.id, status="InStock",
            received_at=datetime.now(timezone.utc) - timedelta(days=250),
        )
    )
    db.commit()

    rows = client.get("/api/reports/stock-aging", headers=auth(admin_token)).json()
    assert [r["bucket"] for r in rows] == ["0-30", "31-90", "91-180", "180+"]
    assert [r["qty"] for r in rows] == [0, 0, 0, 1]


def test_stockout_risk_ranks_by_days_left_not_raw_quantity(
    client, db, branch, product, other_product, admin_token
):
    """
    ประเด็นหลักของตารางนี้: เหลือน้อยไม่เท่ากับเสี่ยง
    - สินค้า A เหลือ 6 ชิ้น แต่ขายเร็ว  -> ใกล้หมดจริง ต้องมาก่อน
    - สินค้า B เหลือ 2 ชิ้น แต่ไม่เคยขาย -> ประมาณวันหมดไม่ได้ ต้องไปท้ายตาราง

    ตั้งใจให้ A อยู่ห่างจากเส้น RISK_HORIZON_DAYS พอสมควร (≈8 วัน ไม่ใช่ 14-15 วัน)
    เพื่อให้ test นี้วัด "การจัดลำดับ" อย่างเดียว ไม่ใช่ไปวัดค่าคงที่ของเกณฑ์เข้าตาราง
    """
    now = datetime.now(timezone.utc)
    for i in range(6):
        db.add(Item(sku_id=product.id, serial_number=f"SN-FAST-{i}", branch_id=branch.id, status="InStock"))
    for i in range(21):  # ขาย 21 ชิ้นใน 30 วัน = 0.7 ชิ้น/วัน -> เหลือ 6 ชิ้น ≈ 8.6 วัน
        _sell(db, product=product, branch=branch, serial=f"SN-FASTSOLD-{i}", sold_at=now - timedelta(days=i % 28 + 1))
    for i in range(2):
        db.add(Item(sku_id=other_product.id, serial_number=f"SN-SLOW-{i}", branch_id=branch.id, status="InStock"))
    db.commit()

    from app.models.branch_sku import BranchSKU

    db.add(BranchSKU(branch_id=branch.id, sku_id=product.id, reorder_point=0))
    db.add(BranchSKU(branch_id=branch.id, sku_id=other_product.id, reorder_point=5))
    db.commit()

    rows = client.get("/api/reports/stockout-risk?days=30", headers=auth(admin_token)).json()
    assert [r["sku_id"] for r in rows] == [product.id, other_product.id], rows
    assert rows[0]["days_left"] is not None and rows[0]["days_left"] < 14
    assert rows[1]["days_left"] is None  # ไม่เคยขาย -> ประมาณไม่ได้ ไม่ใช่ 0


def test_dead_stock_kpi_matches_the_180_plus_aging_bucket(client, db, branch, product, admin_token):
    """
    KPI "ค้างสต็อกเกิน 180 วัน" กับแท่ง "180+" ของกราฟอายุสต็อก อยู่บนหน้าจอเดียวกัน
    จึงต้องเท่ากันเสมอ

    เคสที่เคยทำให้ไม่ตรงกัน: ของอายุ 180.5 วัน — ถ้า KPI เทียบ timestamp ตรง ๆ จะนับว่าเกิน
    แต่กราฟตัดเศษวันเหลือ 180 จึงไปอยู่ถัง "91-180" ผลคือตัวเลขต่างกัน 1 ชิ้นตลอดเวลา
    โดยไม่มีอะไรผิดพลาดให้เห็นบนหน้าจอ
    """
    now = datetime.now(timezone.utc)
    for i, hours_past_180 in enumerate([-12, 12, 24 * 30]):  # ก่อนเส้น / คร่อมเส้น / เกินไปไกล
        db.add(
            Item(
                sku_id=product.id, serial_number=f"SN-EDGE-{i}", branch_id=branch.id, status="InStock",
                received_at=now - timedelta(days=180, hours=hours_past_180),
            )
        )
    db.commit()

    kpi = client.get("/api/reports/summary", headers=auth(admin_token)).json()["dead_stock_items"]
    buckets = client.get("/api/reports/stock-aging", headers=auth(admin_token)).json()
    over_180 = next(b["qty"] for b in buckets if b["bucket"] == "180+")

    assert kpi == over_180, f"KPI={kpi} but 180+ bucket={over_180}"
    assert sum(b["qty"] for b in buckets) == 3  # ทุกชิ้นต้องถูกจัดลงถังใดถังหนึ่ง ไม่มีตกหล่น


def test_low_stock_kpi_reports_the_out_of_stock_subset(client, db, branch, product, other_product, admin_token):
    """
    KPI ใกล้หมดรวมรายการที่ของหมดเกลี้ยงแล้วด้วย (ของหมด = กรณีแย่สุดของใกล้หมด)
    แต่ตารางสต็อกด้านล่างแสดงรายการเหล่านั้นไม่ได้ เพราะ /api/stock JOIN กับ Item ที่ InStock

    endpoint จึงต้องคืนจำนวนของที่หมดแยกออกมา ให้หน้าจอเขียนกำกับได้ว่าเลขต่างกันเพราะอะไร
    ไม่งั้นผู้ใช้เห็น KPI = 2 แต่นับแถวแดงในตารางได้ 1 แล้วสรุปว่าระบบนับผิด
    """
    from app.models.branch_sku import BranchSKU

    db.add(BranchSKU(branch_id=branch.id, sku_id=product.id, reorder_point=5))  # มีของแต่ต่ำ
    db.add(BranchSKU(branch_id=branch.id, sku_id=other_product.id, reorder_point=5))  # ไม่มีของเลย
    db.add(Item(sku_id=product.id, serial_number="SN-LOW-1", branch_id=branch.id, status="InStock"))
    db.commit()

    body = client.get("/api/reports/summary", headers=auth(admin_token)).json()
    assert body["low_stock_skus"] == 2
    assert body["out_of_stock_skus"] == 1

    # ยืนยันว่าตารางสต็อกแสดงได้จริงแค่รายการเดียว — คือที่มาของส่วนต่าง
    stock = client.get("/api/stock", headers=auth(admin_token)).json()
    assert len(stock) == 1 and stock[0]["sku_id"] == product.id


def test_reports_require_authentication(client):
    assert client.get("/api/reports/summary").status_code == 401
