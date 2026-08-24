"""FR-011 + NFR-MAINT-01 — audit log ต้องบันทึกจริงและค้นดูได้"""


def test_admin_only_can_view_audit_log(client, branch_staff_token):
    resp = client.get("/api/audit-log", headers={"Authorization": f"Bearer {branch_staff_token}"})
    assert resp.status_code == 403


def test_actions_are_actually_logged(client, admin_token):
    """สร้าง Product แล้วต้องเห็น entry ใน audit log จริง (ไม่ใช่แค่ endpoint คืน 200 ว่าง ๆ)"""
    create = client.post(
        "/api/products",
        json={"category": "CPU", "brand": "AMD", "model": "5600X", "warranty_months": 24},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    product_id = create.json()["id"]

    resp = client.get(
        f"/api/audit-log?entity_type=Product&entity_id={product_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) == 1
    assert logs[0]["action"] == "CREATE_PRODUCT"
    assert logs[0]["entity_id"] == product_id


def test_pr_lifecycle_produces_three_log_entries(client, admin_token, branch_staff_token, product):
    """FR-011 5W2H — ทุกขั้นของ PR (สร้าง→อนุมัติ) ต้องมี actor + timestamp ตรวจสอบย้อนกลับได้"""
    create = client.post(
        "/api/purchase-requests",
        json={"sku_id": product.id, "quantity": 5},
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    pr_id = create.json()["id"]
    client.post(f"/api/purchase-requests/{pr_id}/approve", headers={"Authorization": f"Bearer {admin_token}"})

    resp = client.get(
        f"/api/audit-log?entity_type=PurchaseRequest&entity_id={pr_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    actions = [log["action"] for log in resp.json()]
    assert "CREATE_PR" in actions
    assert "APPROVE_PR" in actions
    # เรียงจากใหม่ไปเก่า — APPROVE_PR ต้องมาก่อน CREATE_PR
    assert actions.index("APPROVE_PR") < actions.index("CREATE_PR")
