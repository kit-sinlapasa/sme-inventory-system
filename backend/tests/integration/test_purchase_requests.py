"""FR-009 (สร้าง PR) + FR-010 (อนุมัติ/ปฏิเสธ → PO) — US-06, US-07 Acceptance Criteria"""


def test_branch_can_create_pr(client, branch_staff_token, product):
    resp = client.post(
        "/api/purchase-requests",
        json={"sku_id": product.id, "quantity": 10},
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "Pending"
    assert body["quantity"] == 10


def test_pr_with_zero_or_negative_quantity_rejected(client, branch_staff_token, product):
    """US-06 AC: PR ที่ไม่ระบุจำนวน หรือระบุเป็น 0/ค่าติดลบ ต้อง error และไม่สร้าง PR"""
    resp = client.post(
        "/api/purchase-requests",
        json={"sku_id": product.id, "quantity": 0},
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    assert resp.status_code == 422


def test_admin_cannot_create_pr(client, admin_token, product):
    """NFR-SEC-02 — สร้าง PR เป็นสิทธิ์ของสาขาเท่านั้น ตาม FR-009"""
    resp = client.post(
        "/api/purchase-requests",
        json={"sku_id": product.id, "quantity": 5},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 403


def test_branch_sees_only_own_prs(client, branch_staff_token, admin_token, product, other_branch, db):
    from passlib.context import CryptContext

    from app.models.purchase_request import PurchaseRequest
    from app.models.user import User

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    other_staff = User(
        username="other_branch_staff",
        password_hash=pwd_context.hash("testpassword123"),
        role="BranchStaff",
        branch_id=other_branch.id,
    )
    db.add(other_staff)
    db.commit()
    db.refresh(other_staff)

    other_pr = PurchaseRequest(
        branch_id=other_branch.id, sku_id=product.id, quantity=3, status="Pending", requested_by=other_staff.id
    )
    db.add(other_pr)
    db.commit()

    # สร้าง PR ของสาขาตัวเองด้วย
    client.post(
        "/api/purchase-requests",
        json={"sku_id": product.id, "quantity": 7},
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )

    resp = client.get("/api/purchase-requests", headers={"Authorization": f"Bearer {branch_staff_token}"})
    assert resp.status_code == 200
    branches_seen = {pr["branch_id"] for pr in resp.json()}
    assert other_branch.id not in branches_seen

    # Admin ต้องเห็นทั้งสองสาขา
    resp_admin = client.get("/api/purchase-requests", headers={"Authorization": f"Bearer {admin_token}"})
    assert len(resp_admin.json()) == 2


def test_admin_approve_creates_po_and_updates_status(client, admin_token, branch_staff_token, product):
    create = client.post(
        "/api/purchase-requests",
        json={"sku_id": product.id, "quantity": 4},
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    pr_id = create.json()["id"]

    resp = client.post(
        f"/api/purchase-requests/{pr_id}/approve", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["pr_id"] == pr_id

    listing = client.get("/api/purchase-requests", headers={"Authorization": f"Bearer {admin_token}"})
    approved = [pr for pr in listing.json() if pr["id"] == pr_id][0]
    assert approved["status"] == "Approved"
    assert approved["decided_by"] is not None


def test_cannot_approve_pr_twice(client, admin_token, branch_staff_token, product):
    """ป้องกัน double-submit/double-approve ด้วย conditional update pattern เดียวกับ ADR-002"""
    create = client.post(
        "/api/purchase-requests",
        json={"sku_id": product.id, "quantity": 2},
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    pr_id = create.json()["id"]

    first = client.post(f"/api/purchase-requests/{pr_id}/approve", headers={"Authorization": f"Bearer {admin_token}"})
    second = client.post(f"/api/purchase-requests/{pr_id}/approve", headers={"Authorization": f"Bearer {admin_token}"})

    assert first.status_code == 200
    assert second.status_code == 409


def test_reject_requires_reason(client, admin_token, branch_staff_token, product):
    """US-07 AC: Admin ต้องกรอกเหตุผลก่อนปฏิเสธได้"""
    create = client.post(
        "/api/purchase-requests",
        json={"sku_id": product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    pr_id = create.json()["id"]

    no_reason = client.post(
        f"/api/purchase-requests/{pr_id}/reject", json={}, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert no_reason.status_code == 422

    with_reason = client.post(
        f"/api/purchase-requests/{pr_id}/reject",
        json={"reason": "งบประมาณไม่พอในเดือนนี้"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert with_reason.status_code == 200
    assert with_reason.json()["status"] == "Rejected"
    assert with_reason.json()["reject_reason"] == "งบประมาณไม่พอในเดือนนี้"


def test_branch_staff_cannot_approve_or_reject(client, branch_staff_token, admin_token, product):
    """NFR-SEC-02 — อนุมัติ/ปฏิเสธเป็นสิทธิ์ Admin เท่านั้น"""
    create = client.post(
        "/api/purchase-requests",
        json={"sku_id": product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {branch_staff_token}"},
    )
    pr_id = create.json()["id"]

    resp = client.post(
        f"/api/purchase-requests/{pr_id}/approve", headers={"Authorization": f"Bearer {branch_staff_token}"}
    )
    assert resp.status_code == 403
