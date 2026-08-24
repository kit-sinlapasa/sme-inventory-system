"""FR-001 — Product CRUD + soft-delete (suspend)"""


def test_admin_can_create_product(client, admin_token):
    resp = client.post(
        "/api/products",
        json={"category": "CPU", "brand": "Intel", "model": "i5-13400", "warranty_months": 36},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["category"] == "CPU"
    assert body["is_active"] is True


def test_branch_staff_cannot_create_product(client, branch_staff_token):
    """NFR-SEC-02 — Branch ไม่มีสิทธิ์แก้ไขสินค้าในสต็อกหลัก"""
    resp = client.post(
        "/api/products",
        json={"category": "CPU", "brand": "Intel", "model": "i5", "warranty_months": 12},
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    assert resp.status_code == 403


def test_branch_staff_can_list_products_readonly(client, branch_staff_token, product):
    resp = client.get("/api/products", headers={"Authorization": f"Bearer {branch_staff_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_warranty_months_must_be_positive(client, admin_token):
    """FR-001 ต้อง 'เขียนให้ทดสอบได้' — validate ที่ schema level"""
    resp = client.post(
        "/api/products",
        json={"category": "RAM", "brand": "X", "model": "Y", "warranty_months": 0},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 422


def test_suspend_product_is_soft_delete_and_idempotent(client, admin_token, product):
    resp1 = client.delete(f"/api/products/{product.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp1.status_code == 204

    # ระงับซ้ำต้องไม่ error (idempotent)
    resp2 = client.delete(f"/api/products/{product.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp2.status_code == 204

    # ค่าเริ่มต้นของ list ต้องไม่เห็นสินค้าที่ถูกระงับแล้ว
    listing = client.get("/api/products", headers={"Authorization": f"Bearer {admin_token}"})
    assert product.id not in [p["id"] for p in listing.json()]

    # แต่ include_inactive=true ต้องยังเห็น (ประวัติต้องคงอยู่ ไม่ hard delete)
    listing_all = client.get(
        "/api/products?include_inactive=true", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert product.id in [p["id"] for p in listing_all.json()]
