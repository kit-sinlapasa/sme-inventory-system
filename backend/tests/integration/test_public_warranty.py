"""
Integration test สำหรับ FR-006 + NFR-SEC-01
ตรงกับ US-01 Acceptance Criteria (docs/01-Requirements-Package.md)
"""
from datetime import datetime, timedelta, timezone

from app.models.sale import Sale


def test_warranty_check_no_auth_required(client, in_stock_item, db, branch_staff_token):
    """Given: item ที่ยังไม่ขาย — When: เช็คด้วย S/N — Then: ไม่พบข้อมูล (ยังไม่มี Sale)"""
    resp = client.get(f"/api/public/warranty/{in_stock_item.serial_number}")
    assert resp.status_code == 404


def test_warranty_check_valid_serial_returns_status_without_buyer_info(client, in_stock_item, db):
    """
    Given: item ถูกขายแล้ว — When: กรอก S/N ถูกต้อง — Then: เห็นสถานะประกัน
    แต่ต้อง**ไม่มี** field buyer_name/buyer_phone ใน response เด็ดขาด (NFR-SEC-01)
    """
    sale = Sale(
        item_id=in_stock_item.id,
        buyer_name="ลูกค้าทดสอบ",
        buyer_phone="0899999999",
        branch_id=in_stock_item.branch_id,
        warranty_expires_at=datetime.now(timezone.utc) + timedelta(days=300),
        idempotency_key="test-key-warranty-1",
    )
    db.add(sale)
    db.commit()

    resp = client.get(f"/api/public/warranty/{in_stock_item.serial_number}")
    assert resp.status_code == 200

    body = resp.json()
    assert body["warranty_status"] == "อยู่ในประกัน"
    assert "buyer_name" not in body
    assert "buyer_phone" not in body
    assert "ลูกค้าทดสอบ" not in resp.text  # กันหลุดผ่านทาง serialization อื่น ๆ ด้วย


def test_warranty_check_unknown_serial_returns_404(client):
    """Given: S/N ที่ไม่มีในระบบ — When: ค้นหา — Then: ไม่พบข้อมูล"""
    resp = client.get("/api/public/warranty/SN-DOES-NOT-EXIST")
    assert resp.status_code == 404
