"""NFR-PRIV-01 (CR-001) — manual purge ของข้อมูลผู้ซื้อที่หมดประกันเกิน DATA_RETENTION_YEARS ปี"""
from datetime import datetime, timedelta, timezone

from app.models.sale import Sale


def _make_sale(db, item, *, warranty_expires_at, buyer_data_purged=False):
    sale = Sale(
        item_id=item.id,
        buyer_name="สมชาย ทดสอบ",
        buyer_phone="0812345678",
        branch_id=item.branch_id,
        warranty_expires_at=warranty_expires_at,
        idempotency_key=f"purge-test-{item.id}",
        buyer_data_purged=buyer_data_purged,
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def test_purges_sales_past_retention_window(client, admin_token, db, in_stock_item):
    long_ago = datetime.now(timezone.utc) - timedelta(days=365 * 4)  # เกิน 3 ปี (default) แน่นอน
    sale = _make_sale(db, in_stock_item, warranty_expires_at=long_ago)

    resp = client.post("/api/admin/purge-old-buyer-data", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["purged_count"] == 1

    db.refresh(sale)
    assert sale.buyer_data_purged is True
    assert sale.buyer_name != "สมชาย ทดสอบ"
    assert sale.buyer_phone != "0812345678"


def test_does_not_purge_sales_within_retention_window(client, admin_token, db, in_stock_item):
    recent = datetime.now(timezone.utc) - timedelta(days=30)  # หมดประกันไปแค่ 1 เดือน ยังไม่ถึง 3 ปี
    sale = _make_sale(db, in_stock_item, warranty_expires_at=recent)

    resp = client.post("/api/admin/purge-old-buyer-data", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["purged_count"] == 0

    db.refresh(sale)
    assert sale.buyer_data_purged is False
    assert sale.buyer_name == "สมชาย ทดสอบ"


def test_already_purged_sales_are_not_reprocessed(client, admin_token, db, in_stock_item):
    long_ago = datetime.now(timezone.utc) - timedelta(days=365 * 4)
    sale = _make_sale(db, in_stock_item, warranty_expires_at=long_ago, buyer_data_purged=True)
    sale.buyer_name = "ลูกค้า (ข้อมูลถูกลบตามนโยบายความเป็นส่วนตัว)"
    sale.buyer_phone = "0000000000"
    db.commit()

    resp = client.post("/api/admin/purge-old-buyer-data", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["purged_count"] == 0, "ไม่ควรนับ/ประมวลผลซ้ำรายการที่ purge ไปแล้ว"


def test_branch_staff_cannot_purge_buyer_data(client, branch_staff_token):
    resp = client.post(
        "/api/admin/purge-old-buyer-data", headers={"Authorization": f"Bearer {branch_staff_token}"}
    )
    assert resp.status_code == 403


def test_purge_is_logged_in_audit_trail(client, admin_token, db, in_stock_item):
    long_ago = datetime.now(timezone.utc) - timedelta(days=365 * 4)
    _make_sale(db, in_stock_item, warranty_expires_at=long_ago)

    client.post("/api/admin/purge-old-buyer-data", headers={"Authorization": f"Bearer {admin_token}"})

    resp = client.get(
        "/api/audit-log?entity_type=Sale", headers={"Authorization": f"Bearer {admin_token}"}
    )
    actions = [log["action"] for log in resp.json()]
    assert "PURGE_OLD_BUYER_DATA" in actions
