"""GET /api/branches — ใช้ประกอบ dropdown ตอนรับสต็อกเข้า (usability, NFR-USE-01)"""


def test_admin_can_list_branches(client, admin_token, branch):
    resp = client.get("/api/branches", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    names = [b["name"] for b in resp.json()]
    assert branch.name in names


def test_branch_staff_cannot_list_branches(client, branch_staff_token):
    """NFR-SEC-02 — endpoint นี้เป็น Admin เท่านั้น"""
    resp = client.get("/api/branches", headers={"Authorization": f"Bearer {branch_staff_token}"})
    assert resp.status_code == 403
