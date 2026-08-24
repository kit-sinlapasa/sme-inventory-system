"""
ทดสอบ NFR-REL-01 / ADR-002 (docs/03-Architecture-Design.md ส่วนที่ 3)

Quality Attribute Scenario #1:
Source: พนักงาน 2 สาขาพร้อมกัน
Stimulus: กดขาย S/N เดียวกันในเวลาไล่เลี่ยกัน
Response: ระบบอนุญาตให้สำเร็จได้เพียง 1 request เท่านั้น

นี่คือ test ที่สำคัญที่สุดของโปรเจกต์ — พิสูจน์ว่า "ความท้าทายหลัก" ที่โจทย์ระบุ
(Transaction consistency) ถูกแก้จริง ไม่ใช่แค่พูดใน ADR
"""
import concurrent.futures
import uuid

from fastapi.testclient import TestClient


def _attempt_sale(client: TestClient, token: str, item_id: int, idempotency_key: str):
    return client.post(
        "/api/sales",
        json={"item_id": item_id, "buyer_name": "Concurrency Tester", "buyer_phone": "0800000000"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
    )


def test_only_one_concurrent_sale_succeeds(client, branch_staff_token, in_stock_item):
    """N request พร้อมกันไปที่ S/N เดียว — ต้องสำเร็จแค่ 1 request"""
    N = 10
    item_id = in_stock_item.id

    with concurrent.futures.ThreadPoolExecutor(max_workers=N) as executor:
        futures = [
            executor.submit(_attempt_sale, client, branch_staff_token, item_id, str(uuid.uuid4()))
            for _ in range(N)
        ]
        responses = [f.result() for f in futures]

    success_count = sum(1 for r in responses if r.status_code == 201)
    conflict_count = sum(1 for r in responses if r.status_code == 409)

    assert success_count == 1, f"ควรสำเร็จแค่ 1 request แต่สำเร็จ {success_count} — ADR-002 ล้มเหลว!"
    assert conflict_count == N - 1


def test_idempotent_retry_returns_same_sale(client, branch_staff_token, in_stock_item):
    """จำลองผู้ใช้กดยืนยันซ้ำเพราะเน็ตช้า — ต้องได้ sale เดิม ไม่สร้างรายการใหม่ (Deck 03 สไลด์ 17)"""
    key = str(uuid.uuid4())

    r1 = _attempt_sale(client, branch_staff_token, in_stock_item.id, key)
    r2 = _attempt_sale(client, branch_staff_token, in_stock_item.id, key)  # retry — key เดิม

    assert r1.status_code == 201
    assert r2.status_code in (200, 201)
    assert r1.json()["id"] == r2.json()["id"], "Idempotency key ซ้ำต้องคืนผลลัพธ์เดิม ไม่ใช่สร้างใหม่"


def test_selling_already_sold_item_returns_409(client, branch_staff_token, in_stock_item):
    """ขายสำเร็จครั้งแรก แล้วพยายามขายซ้ำด้วย request ใหม่ (key ใหม่) — ต้องถูกปฏิเสธ"""
    first = _attempt_sale(client, branch_staff_token, in_stock_item.id, str(uuid.uuid4()))
    assert first.status_code == 201

    second = _attempt_sale(client, branch_staff_token, in_stock_item.id, str(uuid.uuid4()))
    assert second.status_code == 409


def test_branch_staff_cannot_sell_item_from_other_branch(client, branch_staff_token, db):
    """NFR-SEC-02 ทางอ้อม — item ที่ branch_id ไม่ตรงกับ token ต้องขายไม่ได้"""
    from app.models.branch import Branch
    from app.models.item import Item
    from app.models.product import Product

    other_branch = Branch(name="สาขาอื่น")
    db.add(other_branch)
    db.commit()
    db.refresh(other_branch)

    product = Product(category="CPU", brand="X", model="Y", warranty_months=6)
    db.add(product)
    db.commit()
    db.refresh(product)

    other_item = Item(sku_id=product.id, serial_number="SN-OTHER-0001", branch_id=other_branch.id, status="InStock")
    db.add(other_item)
    db.commit()
    db.refresh(other_item)

    resp = _attempt_sale(client, branch_staff_token, other_item.id, str(uuid.uuid4()))
    assert resp.status_code == 409  # conditional update ไม่เจอแถวที่ match branch_id จึง affected-row = 0
