"""
สัปดาห์ 7 (Hardening) — ทดสอบจริงว่า mitigation แต่ละข้อใน STRIDE Threat Model
(docs/03-Architecture-Design.md ส่วนที่ 7) ทำงานได้จริง ไม่ใช่แค่คอมเมนต์ในโค้ดที่อ้างว่าทำ
"""
import uuid

from fastapi.testclient import TestClient
from jose import jwt

from app.config import settings
from app.database import get_db
from app.limiter import limiter
from app.main import app


# --- STRIDE-S: Spoofing — JWT เซ็นด้วย server secret, แก้ signature แล้วต้องถูกปฏิเสธ ---
def test_tampered_jwt_signature_rejected(client, branch_staff_token):
    header, payload, signature = branch_staff_token.split(".")
    tampered_signature = signature[:-4] + ("AAAA" if signature[-4:] != "AAAA" else "BBBB")
    tampered_token = f"{header}.{payload}.{tampered_signature}"

    resp = client.get("/api/stock", headers={"Authorization": f"Bearer {tampered_token}"})
    assert resp.status_code == 401


def test_jwt_signed_with_wrong_secret_rejected(client, branch_staff_user):
    forged = jwt.encode(
        {"sub": str(branch_staff_user.id), "role": "Admin", "branch_id": None},
        "not-the-real-server-secret",
        algorithm=settings.JWT_ALGORITHM,
    )
    resp = client.get("/api/stock", headers={"Authorization": f"Bearer {forged}"})
    assert resp.status_code == 401, "โทเคนที่เซ็นด้วย secret ปลอมต้องถูกปฏิเสธ แม้ role อ้างว่าเป็น Admin ก็ตาม"


# --- STRIDE-T: Tampering — แก้ branch_id ใน request body ต้องไม่มีผล (server ใช้ branch_id จาก JWT เสมอ) ---
def test_spoofed_branch_id_in_sale_payload_is_ignored(client, branch_staff_token, other_branch, in_stock_item):
    resp = client.post(
        "/api/sales",
        json={
            "item_id": in_stock_item.id,
            "buyer_name": "ทดสอบ",
            "buyer_phone": "0800000000",
            "branch_id": other_branch.id,  # พยายามยัด branch_id ปลอมเข้าไปใน body
        },
        headers={"Authorization": f"Bearer {branch_staff_token}", "Idempotency-Key": str(uuid.uuid4())},
    )
    assert resp.status_code == 201
    assert resp.json()["branch_id"] != other_branch.id, (
        "branch_id ต้องมาจาก JWT ของผู้ใช้เท่านั้น ห้ามรับค่าจาก client body แม้จะพยายามส่งมาก็ตาม"
    )


# --- STRIDE-D: Denial of Service — rate limit 30/minute บน public warranty endpoint ---
def test_public_warranty_rate_limit_returns_429_after_30_requests():
    """
    ใช้ TestClient แยกจาก fixture `client` เพราะ slowapi เก็บ state แบบ in-memory
    ต่อ process (key ตาม IP ซึ่ง TestClient ทุกตัวเห็นเป็น "testclient" เดียวกันหมด) —
    ต้อง reset limiter ก่อนเทสต์นี้เสมอ ไม่งั้นโควตาที่ test อื่นในไฟล์เดียวกัน/ไฟล์อื่น
    ใช้ไปก่อนหน้าจะติดมาด้วย ทำให้ 429 มาเร็วกว่า request ที่ 31 จริง (เจอบั๊กนี้จริงตอนรัน
    ทั้ง suite พร้อมกัน — รันแยกไฟล์เดียวผ่าน แต่รันรวมกับไฟล์อื่นที่ยิง endpoint เดียวกันมาก่อนแล้วพัง)
    """
    limiter.reset()
    with TestClient(app) as c:
        statuses = [c.get("/api/public/warranty/SN-DOES-NOT-EXIST").status_code for _ in range(31)]

    assert statuses.count(429) >= 1, "ยิงเกิน 30 request/นาที ต้องโดน rate limit อย่างน้อย 1 ครั้ง"
    # 30 ตัวแรกควรผ่าน rate limiter (แม้จะเป็น 404 เพราะไม่มี S/N นี้จริง ไม่ใช่ 429)
    assert statuses[:30].count(429) == 0, "ยังไม่ควรโดน rate limit ก่อนถึง request ที่ 31"


# --- STRIDE-I: Information Disclosure — unhandled exception ต้องไม่รั่ว stack trace ให้ client เห็น ---
def test_unhandled_exception_does_not_leak_internal_details():
    SECRET_INTERNAL_DETAIL = "DB_CONNECTION_INTERNAL_DETAIL_xyz_should_never_reach_client"

    def broken_get_db():
        raise RuntimeError(SECRET_INTERNAL_DETAIL)
        yield  # pragma: no cover — ทำให้เป็น generator แต่ไม่ถูกรันถึง

    app.dependency_overrides[get_db] = broken_get_db
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.get("/api/public/warranty/SN-ANYTHING")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 500
    body = resp.text
    assert SECRET_INTERNAL_DETAIL not in body, "ข้อความ exception จริงต้องไม่รั่วไปถึง response ที่ client เห็น"
    assert "Traceback" not in body
    assert ".py" not in body, "ต้องไม่มี path ไฟล์ฝั่ง server รั่วออกไปใน response"
