"""
Acceptance test — ทดสอบตาม **Acceptance Criteria ของ User Story** โดยตรง

ต่างจาก integration test ตรงที่จุดตั้งต้น: integration test เขียนจากมุมของ endpoint
("endpoint นี้ทำงานถูกไหม") ส่วนไฟล์นี้เขียนจากมุมของผู้ใช้ ("US-xx ทำได้จริงไหม")
ชื่อ test จึงอ้าง US และ Given-When-Then ตรงตามที่เขียนไว้ใน
docs/01-Requirements-Package.md ข้อ 5 — ถ้า AC เปลี่ยน test นี้ต้องเปลี่ยนตาม

**เกณฑ์ที่โจทย์กำหนด: "Test case trace กลับไปยัง Requirements"** — ไฟล์นี้คือเส้นทางนั้น
"""
from datetime import datetime, timedelta, timezone

from app.models.item import Item
from app.models.sale import Sale


def auth(t):
    return {"Authorization": f"Bearer {t}"}


# ── US-01 — เช็คประกัน (End Customer) · FR-005, FR-006 ────────────────────────


def test_us01_customer_checks_warranty_without_logging_in(client, db, branch, product):
    """
    Given ผู้ใช้เปิดหน้าเว็บสาธารณะ (ไม่ login)
    When  กรอก S/N ที่ถูกต้องและมีในระบบ
    Then  ระบบแสดงรุ่นสินค้า วันหมดประกัน และสถานะ
    """
    now = datetime.now(timezone.utc)
    item = Item(sku_id=product.id, serial_number="SN-US01-001", branch_id=branch.id, status="Sold")
    db.add(item)
    db.flush()
    db.add(
        Sale(item_id=item.id, buyer_name="สมชาย ใจดี", buyer_phone="0812345678",
             branch_id=branch.id, warranty_expires_at=now + timedelta(days=365))
    )
    db.commit()

    resp = client.get("/api/public/warranty/SN-US01-001")  # ไม่ส่ง Authorization โดยตั้งใจ
    assert resp.status_code == 200
    body = resp.json()
    assert body["model"] == f"{product.brand} {product.model}"
    assert body["warranty_status"] == "อยู่ในประกัน"
    assert "warranty_expires_at" in body


def test_us01_unknown_serial_gives_a_clear_answer(client):
    """
    Given ผู้ใช้กรอก S/N ที่ไม่มีในระบบ · When กดค้นหา
    Then  ระบบตอบว่าไม่พบ (ไม่ crash และไม่ตอบกำกวม)
    """
    resp = client.get("/api/public/warranty/SN-DOES-NOT-EXIST-999")
    assert resp.status_code == 404
    assert "ไม่พบ" in resp.json()["detail"]


def test_us01_public_result_never_exposes_buyer_identity(client, db, branch, product):
    """
    Given S/N ถูกต้อง · When ระบบแสดงผล
    Then  ต้องไม่แสดงชื่อ เบอร์โทร หรือที่อยู่ของผู้ซื้อ  (NFR-SEC-01)

    เป็น AC ที่ห้ามพลาดที่สุดในไฟล์นี้ — หน้านี้เปิดสาธารณะ ใครก็ยิงได้
    """
    now = datetime.now(timezone.utc)
    item = Item(sku_id=product.id, serial_number="SN-US01-PRIV", branch_id=branch.id, status="Sold")
    db.add(item)
    db.flush()
    db.add(
        Sale(item_id=item.id, buyer_name="ความลับ ห้ามหลุด", buyer_phone="0899999999",
             branch_id=branch.id, warranty_expires_at=now + timedelta(days=365))
    )
    db.commit()

    body = client.get("/api/public/warranty/SN-US01-PRIV").json()
    raw = str(body)
    assert "ความลับ" not in raw and "0899999999" not in raw
    assert set(body) == {"model", "warranty_status", "warranty_expires_at"}


# ── US-04 — บันทึกการขาย (Branch Staff) · FR-004, FR-005, NFR-REL-01 ─────────


def test_us04_staff_records_sale_and_warranty_is_calculated(
    client, db, branch, product, in_stock_item, branch_staff_token
):
    """
    Given พนักงานสาขาล็อกอินแล้วและสินค้ายังอยู่ในสต็อก
    When  บันทึกการขายด้วย S/N
    Then  ระบบบันทึกสำเร็จ และคำนวณวันหมดประกันให้อัตโนมัติตามระยะประกันของสินค้า
    """
    resp = client.post(
        "/api/sales",
        json={"item_id": in_stock_item.id, "buyer_name": "สุดา รักเรียน", "buyer_phone": "0898765432"},
        headers={**auth(branch_staff_token), "Idempotency-Key": "us04-happy-path"},
    )
    assert resp.status_code == 201
    expires = datetime.fromisoformat(resp.json()["warranty_expires_at"].replace("Z", "+00:00"))
    expected = datetime.now(timezone.utc) + timedelta(days=30 * product.warranty_months)
    assert abs((expires - expected).days) <= 2, "วันหมดประกันต้องคิดจากระยะประกันของสินค้า"


def test_us04_same_item_cannot_be_sold_twice(
    client, in_stock_item, branch_staff_token
):
    """
    Given สินค้าชิ้นนี้ถูกขายไปแล้ว · When พยายามขายซ้ำ
    Then  ระบบต้องปฏิเสธ (NFR-REL-01 — หนึ่งชิ้นขายได้ครั้งเดียว)
    """
    h = auth(branch_staff_token)
    first = client.post("/api/sales", json={"item_id": in_stock_item.id, "buyer_name": "ก", "buyer_phone": "0810000000"},
                        headers={**h, "Idempotency-Key": "us04-first"})
    assert first.status_code == 201

    second = client.post("/api/sales", json={"item_id": in_stock_item.id, "buyer_name": "ข", "buyer_phone": "0820000000"},
                         headers={**h, "Idempotency-Key": "us04-second"})
    assert second.status_code == 409


def test_us04_admin_cannot_record_a_sale(client, in_stock_item, admin_token):
    """
    Given ผู้ใช้เป็น Admin (ไม่สังกัดสาขา)
    Then  ต้องบันทึกขายไม่ได้ — แยกหน้าที่ระหว่างคนอนุมัติ PR กับคนขายหน้าร้าน
    """
    resp = client.post(
        "/api/sales",
        json={"item_id": in_stock_item.id, "buyer_name": "ก", "buyer_phone": "0810000000"},
        headers={**auth(admin_token), "Idempotency-Key": "us04-admin"},
    )
    assert resp.status_code == 403


# ── US-05 — ดูสต็อกสาขาตัวเอง (Branch Staff) · FR-003, FR-008 ────────────────


def test_us05_branch_sees_only_its_own_stock(
    client, db, branch, other_branch, product, branch_staff_token
):
    """
    Given พนักงานสังกัดสาขา A · When เปิดดูสต็อก
    Then  ต้องเห็นเฉพาะของสาขา A แม้จะพยายามระบุสาขาอื่น (NFR-SEC-02)
    """
    db.add(Item(sku_id=product.id, serial_number="SN-US05-MINE", branch_id=branch.id))
    db.add(Item(sku_id=product.id, serial_number="SN-US05-THEIRS", branch_id=other_branch.id))
    db.commit()

    rows = client.get(f"/api/stock?branch_id={other_branch.id}", headers=auth(branch_staff_token)).json()
    assert {r["branch_id"] for r in rows} == {branch.id}


# ── US-06 / US-07 — คำขอสั่งซื้อและการอนุมัติ · FR-009, FR-010 ───────────────


def test_us06_us07_purchase_request_lifecycle(
    client, db, branch, product, branch_staff_token, admin_token
):
    """
    Given สาขาเห็นว่าของใกล้หมด · When สร้างคำขอสั่งซื้อ · Then สถานะเป็น Pending
    Given สำนักงานใหญ่เห็นคำขอ · When กดอนุมัติ · Then เกิด PurchaseOrder คู่กัน
    """
    created = client.post("/api/purchase-requests", json={"sku_id": product.id, "quantity": 5},
                          headers=auth(branch_staff_token))
    assert created.status_code == 201
    pr = created.json()
    assert pr["status"] == "Pending"

    approved = client.post(f"/api/purchase-requests/{pr['id']}/approve", headers=auth(admin_token))
    assert approved.status_code == 200
    # endpoint คืน PurchaseOrder ที่เพิ่งสร้าง ไม่ใช่ PR — เพราะ "ผลของการอนุมัติ" คือ PO
    po = approved.json()
    assert po["pr_id"] == pr["id"]

    from app.models.purchase_order import PurchaseOrder
    from app.models.purchase_request import PurchaseRequest

    assert db.query(PurchaseOrder).filter(PurchaseOrder.pr_id == pr["id"]).count() == 1
    db.expire_all()
    # FR-010 — PR ที่อนุมัติแล้วต้องเปลี่ยนสถานะและมี PO คู่กันเสมอ
    assert db.get(PurchaseRequest, pr["id"]).status == "Approved"


def test_us07_reject_requires_a_reason(client, db, product, branch_staff_token, admin_token):
    """Given สำนักงานใหญ่จะปฏิเสธคำขอ · When ไม่ระบุเหตุผล · Then ระบบต้องไม่ยอมรับ"""
    pr = client.post("/api/purchase-requests", json={"sku_id": product.id, "quantity": 3},
                     headers=auth(branch_staff_token)).json()
    resp = client.post(f"/api/purchase-requests/{pr['id']}/reject", json={},
                       headers=auth(admin_token))
    assert resp.status_code == 422
