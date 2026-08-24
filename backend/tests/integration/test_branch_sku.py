"""FR-012 + CR-002 — reorder point ต่อ SKU ต่อสาขา"""


def test_admin_can_set_reorder_point(client, admin_token, product, branch):
    resp = client.put(
        f"/api/branch-sku/{branch.id}/{product.id}",
        json={"reorder_point": 5},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["reorder_point"] == 5


def test_branch_staff_cannot_set_reorder_point(client, branch_staff_token, product, branch):
    """NFR-SEC-02 — สาขาไม่มีสิทธิ์ตั้งค่า reorder point เอง (CR-002: Admin ตั้งกลาง)"""
    resp = client.put(
        f"/api/branch-sku/{branch.id}/{product.id}",
        json={"reorder_point": 5},
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    assert resp.status_code == 403


def test_setting_reorder_point_twice_updates_not_duplicates(client, admin_token, product, branch, db):
    from app.models.branch_sku import BranchSKU

    client.put(
        f"/api/branch-sku/{branch.id}/{product.id}",
        json={"reorder_point": 5},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    client.put(
        f"/api/branch-sku/{branch.id}/{product.id}",
        json={"reorder_point": 8},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    rows = db.query(BranchSKU).filter(BranchSKU.branch_id == branch.id, BranchSKU.sku_id == product.id).all()
    assert len(rows) == 1  # uq_branch_sku constraint ต้องกันไม่ให้ซ้ำแถว
    assert rows[0].reorder_point == 8


def test_reorder_point_visible_in_stock_response(client, admin_token, branch, product, in_stock_item):
    """เชื่อม FR-003 กับ FR-012 — ตัวเลข stock ต้องมี reorder_point ติดมาด้วยเมื่อตั้งไว้แล้ว"""
    client.put(
        f"/api/branch-sku/{branch.id}/{product.id}",
        json={"reorder_point": 3},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    resp = client.get("/api/stock", headers={"Authorization": f"Bearer {admin_token}"})
    row = resp.json()[0]
    assert row["reorder_point"] == 3
