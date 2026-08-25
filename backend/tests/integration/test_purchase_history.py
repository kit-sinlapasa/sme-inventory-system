"""
FR-015 (CR-014) — ค้นประวัติการซื้อจากเบอร์โทรผู้ซื้อ

จุดที่ตั้งใจทดสอบหนัก คือ **ขอบเขตความเป็นส่วนตัว** ไม่ใช่แค่ว่าค้นเจอ:
endpoint นี้เป็นทางเดียวในระบบที่เข้าถึงข้อมูลผู้ซื้อได้จากฝั่งพนักงาน
ถ้าออกแบบพลาดจะกลายเป็นช่องให้ไล่อ่านข้อมูลลูกค้าทั้งฐาน
"""
from datetime import datetime, timedelta, timezone

from app.models.item import Item
from app.models.sale import Sale


def auth(t):
    return {"Authorization": f"Bearer {t}"}


def _sell(db, *, product, branch, serial, phone, name="สมชาย ใจดี", years=1, purged=False):
    now = datetime.now(timezone.utc)
    item = Item(sku_id=product.id, serial_number=serial, branch_id=branch.id, status="Sold")
    db.add(item)
    db.flush()
    db.add(
        Sale(
            item_id=item.id, buyer_name=name, buyer_phone=phone, branch_id=branch.id,
            sold_at=now - timedelta(days=10),
            warranty_expires_at=now + timedelta(days=365 * years),
            buyer_data_purged=purged,
        )
    )
    db.commit()
    return item


def test_finds_all_purchases_for_a_phone(client, db, branch, product, admin_token):
    """ลูกค้าคนเดียวซื้อหลายชิ้น ต้องได้ครบทุกชิ้น เรียงจากล่าสุด"""
    _sell(db, product=product, branch=branch, serial="SN-H-1", phone="0812345678")
    _sell(db, product=product, branch=branch, serial="SN-H-2", phone="0812345678")
    _sell(db, product=product, branch=branch, serial="SN-OTHER", phone="0899999999")

    rows = client.get("/api/sales/by-buyer?phone=0812345678", headers=auth(admin_token)).json()
    assert {r["serial_number"] for r in rows} == {"SN-H-1", "SN-H-2"}
    assert all("buyer_phone" not in r for r in rows), "ไม่ควรส่งเบอร์กลับไป ผู้เรียกพิมพ์มาเองอยู่แล้ว"
    assert rows[0]["warranty_status"] == "อยู่ในประกัน"


def test_warranty_status_reflects_expiry(client, db, branch, product, admin_token):
    now = datetime.now(timezone.utc)
    item = Item(sku_id=product.id, serial_number="SN-EXPIRED", branch_id=branch.id, status="Sold")
    db.add(item)
    db.flush()
    db.add(
        Sale(item_id=item.id, buyer_name="ก", buyer_phone="0811111111", branch_id=branch.id,
             sold_at=now - timedelta(days=800), warranty_expires_at=now - timedelta(days=1))
    )
    db.commit()

    rows = client.get("/api/sales/by-buyer?phone=0811111111", headers=auth(admin_token)).json()
    assert rows[0]["warranty_status"] == "หมดประกันแล้ว"


# ── ขอบเขตความเป็นส่วนตัว ────────────────────────────────────────────────────


def test_partial_phone_number_is_rejected(client, admin_token):
    """
    ต้องปฏิเสธเบอร์สั้น ๆ — ถ้ายอมให้ค้นด้วย "08" แล้วคืนทุกคนที่ขึ้นต้นด้วย 08
    endpoint นี้จะกลายเป็นเครื่องมือไล่อ่านข้อมูลลูกค้าทั้งฐาน
    """
    r = client.get("/api/sales/by-buyer?phone=08", headers=auth(admin_token))
    assert r.status_code == 422


def test_no_partial_matching_even_with_full_length(client, db, branch, product, admin_token):
    """เบอร์ที่ยาวพอแต่ไม่ตรงทั้งเบอร์ ต้องไม่เจอ — ยืนยันว่าใช้ == ไม่ใช่ LIKE"""
    _sell(db, product=product, branch=branch, serial="SN-EXACT", phone="0812345678")
    rows = client.get("/api/sales/by-buyer?phone=081234567", headers=auth(admin_token)).json()
    assert rows == []


def test_purged_records_are_not_returned(client, db, branch, product, admin_token):
    """
    NFR-PRIV-01 — รายการที่ถูก purge ตาม retention policy แล้วต้องไม่โผล่กลับมา
    การคืนแถวที่ชื่อเป็น "ข้อมูลถูกลบ" ไม่ช่วยพนักงาน และทำให้เข้าใจผิดว่ายังมีข้อมูลอยู่
    """
    _sell(db, product=product, branch=branch, serial="SN-PURGED", phone="0822222222",
          name="ลูกค้า (ข้อมูลถูกลบตามนโยบายความเป็นส่วนตัว)", purged=True)
    rows = client.get("/api/sales/by-buyer?phone=0822222222", headers=auth(admin_token)).json()
    assert rows == []


def test_branch_staff_only_sees_own_branch(
    client, db, branch, other_branch, product, branch_staff_token, admin_token
):
    """NFR-SEC-02 — ลูกค้าคนเดียวซื้อจาก 2 สาขา พนักงานต้องเห็นเฉพาะของสาขาตัวเอง"""
    _sell(db, product=product, branch=branch, serial="SN-MINE", phone="0833333333")
    _sell(db, product=product, branch=other_branch, serial="SN-THEIRS", phone="0833333333")

    staff = client.get("/api/sales/by-buyer?phone=0833333333", headers=auth(branch_staff_token)).json()
    assert {r["serial_number"] for r in staff} == {"SN-MINE"}

    admin = client.get("/api/sales/by-buyer?phone=0833333333", headers=auth(admin_token)).json()
    assert {r["serial_number"] for r in admin} == {"SN-MINE", "SN-THEIRS"}


def test_requires_authentication(client):
    """ต่างจากหน้าเช็คประกันสาธารณะ — endpoint นี้คืนข้อมูลผู้ซื้อ จึงต้องล็อกอินเสมอ"""
    assert client.get("/api/sales/by-buyer?phone=0812345678").status_code == 401


def test_phone_with_formatting_is_normalised(client, db, branch, product, admin_token):
    """พนักงานอาจพิมพ์ 081-234-5678 — ต้องหาเจอเหมือนกัน"""
    _sell(db, product=product, branch=branch, serial="SN-FMT", phone="0812345678")
    rows = client.get("/api/sales/by-buyer?phone=081-234-5678", headers=auth(admin_token)).json()
    assert len(rows) == 1
