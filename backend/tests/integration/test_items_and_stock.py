"""FR-002 (รับเข้าสต็อก) + FR-003 (ดูสต็อกเรียลไทม์) + NFR-SEC-02 (แยกตามสาขา)"""


def test_admin_can_receive_item(client, admin_token, product, branch):
    resp = client.post(
        "/api/items",
        json={"sku_id": product.id, "serial_number": "SN-NEW-0001", "branch_id": branch.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "InStock"


def test_duplicate_serial_number_rejected(client, admin_token, product, branch, in_stock_item):
    """FR-002 — S/N ต้องไม่ซ้ำกันทั้งระบบ"""
    resp = client.post(
        "/api/items",
        json={"sku_id": product.id, "serial_number": in_stock_item.serial_number, "branch_id": branch.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 409


def test_stock_count_reflects_received_items(client, admin_token, product, branch, in_stock_item):
    """FR-003 — ยอดคงเหลือต้องนับจาก Item ที่ status=InStock จริง ไม่ใช่ตัวเลข cache"""
    resp = client.get("/api/stock", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["sku_id"] == product.id
    assert rows[0]["branch_id"] == branch.id
    assert rows[0]["on_hand"] == 1


def test_branch_staff_only_sees_own_branch_stock(
    client, branch_staff_token, product, branch, other_branch, db
):
    """NFR-SEC-02 ทางอ้อม — Branch ต้องไม่เห็นสต็อกของสาขาอื่น แม้จะพยายามส่ง branch_id ของสาขาอื่นมาเอง"""
    from app.models.item import Item

    own_item = Item(sku_id=product.id, serial_number="SN-OWN-0001", branch_id=branch.id, status="InStock")
    other_item = Item(
        sku_id=product.id, serial_number="SN-OTHERBRANCH-0001", branch_id=other_branch.id, status="InStock"
    )
    db.add_all([own_item, other_item])
    db.commit()

    # พยายามขอดูสต็อกสาขาอื่นตรง ๆ — server ต้องเมิน parameter นี้และคืนของสาขาตัวเองเท่านั้น
    resp = client.get(
        f"/api/stock?branch_id={other_branch.id}",
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert all(r["branch_id"] == branch.id for r in rows)
    assert len(rows) == 1
    assert rows[0]["on_hand"] == 1  # เห็นแค่ของสาขาตัวเอง ไม่ใช่ 2


def test_lookup_item_by_serial_own_branch(client, branch_staff_token, in_stock_item):
    """US-04 — พนักงานกรอก S/N แล้วต้อง resolve เป็น item_id ก่อนขาย"""
    resp = client.get(
        f"/api/items/by-serial/{in_stock_item.serial_number}",
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == in_stock_item.id


def test_lookup_item_by_serial_other_branch_returns_404_not_403(
    client, branch_staff_token, product, other_branch, db
):
    """NFR-SEC-02 — item ของสาขาอื่นต้องเป็น 404 (เหมือนไม่มี) ไม่ใช่ 403 (เผยว่ามีอยู่)"""
    from app.models.item import Item

    other_item = Item(
        sku_id=product.id, serial_number="SN-LOOKUP-OTHER", branch_id=other_branch.id, status="InStock"
    )
    db.add(other_item)
    db.commit()

    resp = client.get(
        "/api/items/by-serial/SN-LOOKUP-OTHER",
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    assert resp.status_code == 404


def test_lookup_unknown_serial_returns_404(client, branch_staff_token):
    resp = client.get(
        "/api/items/by-serial/SN-DOES-NOT-EXIST",
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    assert resp.status_code == 404


def test_admin_can_lookup_any_branch_item(client, admin_token, product, other_branch, db):
    from app.models.item import Item

    other_item = Item(
        sku_id=product.id, serial_number="SN-ADMIN-LOOKUP", branch_id=other_branch.id, status="InStock"
    )
    db.add(other_item)
    db.commit()

    resp = client.get(
        "/api/items/by-serial/SN-ADMIN-LOOKUP", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
