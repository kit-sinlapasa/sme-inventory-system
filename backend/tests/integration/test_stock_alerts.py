"""FR-012 + CR-006 — debounce logic ของการแจ้งเตือนสต็อกใกล้หมด

หมายเหตุ: test เหล่านี้ตรวจ *logic การตัดสินใจว่าควรแจ้งเตือนเมื่อไหร่*
(ผ่าน monkeypatch นับจำนวนครั้งที่ send_low_stock_alert ถูกเรียก) ไม่ได้ตรวจ
การส่งอีเมลจริง เพราะไม่มี SMTP credential จริงให้ทดสอบ (ดู services/notifications.py)
"""
import uuid

from app.services import stock_alerts


def _sell(client, token, item_id):
    return client.post(
        "/api/sales",
        json={"item_id": item_id, "buyer_name": "Test", "buyer_phone": "0800000000"},
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": str(uuid.uuid4())},
    )


def test_alert_fires_once_when_crossing_below_threshold(
    client, admin_token, branch_staff_token, branch, product, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        stock_alerts, "send_low_stock_alert", lambda **kwargs: calls.append(kwargs)
    )

    # ตั้ง reorder point = 1 แล้วรับเข้า 2 ชิ้น (ยังไม่ต่ำกว่า threshold)
    client.put(
        f"/api/branch-sku/{branch.id}/{product.id}",
        json={"reorder_point": 1},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    item1 = client.post(
        "/api/items",
        json={"sku_id": product.id, "serial_number": "SN-ALERT-0001", "branch_id": branch.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    item2 = client.post(
        "/api/items",
        json={"sku_id": product.id, "serial_number": "SN-ALERT-0002", "branch_id": branch.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    # ขายชิ้นแรก: เหลือ 1 = เท่ากับ reorder point → ควรแจ้งเตือน
    resp1 = _sell(client, branch_staff_token, item1["id"])
    assert resp1.status_code == 201
    assert len(calls) == 1

    # ขายชิ้นที่สอง: เหลือ 0 แต่ "เคยแจ้งเตือนไปแล้ว" (ยังไม่เติมสต็อกกลับ) → ไม่ส่งซ้ำ
    resp2 = _sell(client, branch_staff_token, item2["id"])
    assert resp2.status_code == 201
    assert len(calls) == 1, "ไม่ควรส่งอีเมลซ้ำขณะสต็อกยังต่ำกว่า threshold ต่อเนื่อง (debounce)"


def test_alert_resets_after_restock_above_threshold(
    client, admin_token, branch_staff_token, branch, product, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        stock_alerts, "send_low_stock_alert", lambda **kwargs: calls.append(kwargs)
    )

    client.put(
        f"/api/branch-sku/{branch.id}/{product.id}",
        json={"reorder_point": 1},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    item1 = client.post(
        "/api/items",
        json={"sku_id": product.id, "serial_number": "SN-RESET-0001", "branch_id": branch.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    # ขายจนเหลือ 0 → ต่ำกว่า threshold → แจ้งเตือนครั้งที่ 1
    _sell(client, branch_staff_token, item1["id"])
    assert len(calls) == 1

    # เติมสต็อกกลับมา 2 ชิ้น (เกิน reorder point = 1) → ต้อง reset debounce flag
    client.post(
        "/api/items",
        json={"sku_id": product.id, "serial_number": "SN-RESET-0002", "branch_id": branch.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    item3 = client.post(
        "/api/items",
        json={"sku_id": product.id, "serial_number": "SN-RESET-0003", "branch_id": branch.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    # ขายจนต่ำกว่า threshold อีกครั้ง → ต้องแจ้งเตือนใหม่ (ครั้งที่ 2)
    _sell(client, branch_staff_token, item3["id"])
    assert len(calls) == 2, "หลัง restock เกิน threshold แล้วต่ำกว่าอีกครั้ง ต้องแจ้งเตือนใหม่ได้"


def test_no_reorder_point_configured_never_alerts(client, admin_token, branch_staff_token, in_stock_item, monkeypatch):
    """ไม่มีการตั้งค่า reorder point ไว้เลย — ไม่ควรมีการเรียก alert"""
    calls = []
    monkeypatch.setattr(
        stock_alerts, "send_low_stock_alert", lambda **kwargs: calls.append(kwargs)
    )
    _sell(client, branch_staff_token, in_stock_item.id)
    assert len(calls) == 0
