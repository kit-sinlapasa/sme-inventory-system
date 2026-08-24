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


def test_suspended_product_can_be_restored(client, admin_token, product):
    """เดิมระงับแล้วเอากลับไม่ได้เลย (ProductUpdate ไม่มี is_active) — ต้องกู้คืนได้"""
    client.delete(f"/api/products/{product.id}", headers={"Authorization": f"Bearer {admin_token}"})
    check = client.get(f"/api/products/{product.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert check.json()["is_active"] is False

    resp = client.post(
        f"/api/products/{product.id}/restore", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


def test_restore_is_idempotent(client, admin_token, product):
    """กดกู้คืนซ้ำกับสินค้าที่ใช้งานอยู่แล้วต้องไม่ error (เหมือน suspend)"""
    resp = client.post(
        f"/api/products/{product.id}/restore", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


def test_branch_staff_cannot_restore_product(client, branch_staff_token, product):
    """NFR-SEC-02 — กู้คืนสินค้าเป็นสิทธิ์ Admin เท่านั้น"""
    resp = client.post(
        f"/api/products/{product.id}/restore", headers={"Authorization": f"Bearer {branch_staff_token}"}
    )
    assert resp.status_code == 403


def test_product_list_query_count_does_not_grow_and_has_no_duplicates(
    client, admin_token, db, product, count_queries
):
    """
    /api/products ต้องโหลดรูปมาพร้อมกัน ไม่ใช่ lazy-load ทีละสินค้า

    ProductOut มีฟิลด์ images (FR-013) ถ้าไม่ joinedload มาด้วย SQLAlchemy จะยิง query
    เพิ่มทีละสินค้าตอน serialize — วัดจริงได้ 62 query สำหรับ 60 สินค้า

    อีกด้านหนึ่งที่ต้องกันคือ JOIN ทำให้สินค้าที่มีหลายรูปกลายเป็นหลายแถว test นี้จึง
    ตรวจทั้ง "จำนวน query คงที่" และ "ไม่มี id ซ้ำ" พร้อมกัน เพราะการแก้อย่างแรก
    เป็นสาเหตุของอย่างหลัง
    """
    from app.models.product import Product
    from app.models.product_image import ProductImage

    headers = {"Authorization": f"Bearer {admin_token}"}

    # สินค้าตัวแรกมีหลายรูป -> ถ้า JOIN ไม่ถูกยุบ จะโผล่ซ้ำ 3 แถว
    for i in range(3):
        db.add(ProductImage(product_id=product.id, image_url=f"https://e/{i}.png", sort_order=i))
    db.commit()

    def hit():
        r = client.get("/api/products", headers=headers)
        assert r.status_code == 200
        return r.json()

    rows_small, q_small = count_queries(hit)
    ids = [p["id"] for p in rows_small]
    assert len(ids) == len(set(ids)), f"สินค้าโผล่ซ้ำจาก JOIN กับตารางรูป: {ids}"
    assert len(rows_small[0]["images"]) == 3

    for i in range(10):
        db.add(Product(category="CPU", brand="Bulk", model=f"BK-{i}", warranty_months=12))
    db.commit()

    rows_big, q_big = count_queries(hit)
    assert len(rows_big) > len(rows_small)
    assert q_big == q_small, (
        f"จำนวน query โตตามจำนวนสินค้า ({q_small} -> {q_big}) = lazy-load รูปทีละตัวอีกแล้ว"
    )
