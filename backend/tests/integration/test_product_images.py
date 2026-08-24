"""FR-013 (CR-007) — รูปสินค้าสูงสุด 5 รูป เก็บเป็น URL"""


def test_admin_can_add_image(client, admin_token, product):
    resp = client.post(
        f"/api/products/{product.id}/images",
        json={"image_url": "https://placehold.co/400x300?text=RAM"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["sort_order"] == 0


def test_branch_staff_cannot_add_image(client, branch_staff_token, product):
    resp = client.post(
        f"/api/products/{product.id}/images",
        json={"image_url": "https://placehold.co/400x300?text=RAM"},
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    assert resp.status_code == 403


def test_invalid_url_rejected(client, admin_token, product):
    resp = client.post(
        f"/api/products/{product.id}/images",
        json={"image_url": "not-a-url"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 422


def test_max_5_images_enforced(client, admin_token, product):
    for i in range(5):
        resp = client.post(
            f"/api/products/{product.id}/images",
            json={"image_url": f"https://placehold.co/400x300?text=img{i}"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201

    sixth = client.post(
        f"/api/products/{product.id}/images",
        json={"image_url": "https://placehold.co/400x300?text=img6"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert sixth.status_code == 409


def test_images_appear_in_product_response(client, admin_token, product):
    client.post(
        f"/api/products/{product.id}/images",
        json={"image_url": "https://placehold.co/400x300?text=RAM"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = client.get(f"/api/products/{product.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert len(resp.json()["images"]) == 1


def test_admin_can_delete_image(client, admin_token, product):
    created = client.post(
        f"/api/products/{product.id}/images",
        json={"image_url": "https://placehold.co/400x300?text=RAM"},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    resp = client.delete(
        f"/api/products/{product.id}/images/{created['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 204

    check = client.get(f"/api/products/{product.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert len(check.json()["images"]) == 0


def test_product_images_deleted_via_cascade(client, admin_token, product, db):
    """ถ้า product ถูกลบจริง (ไม่ใช่ suspend) รูปต้องไม่เป็น orphan row — ทดสอบ cascade ที่ ORM ระดับ"""
    from app.models.product import Product
    from app.models.product_image import ProductImage

    client.post(
        f"/api/products/{product.id}/images",
        json={"image_url": "https://placehold.co/400x300?text=RAM"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    db.delete(db.get(Product, product.id))
    db.commit()
    remaining = db.query(ProductImage).filter(ProductImage.product_id == product.id).count()
    assert remaining == 0
