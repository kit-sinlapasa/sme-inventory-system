"""
สัปดาห์ 8 — พบระหว่างเตรียม demo ว่า production ไม่มี CORS middleware เลย ทำให้ browser จริง
บล็อก response ทุก request จาก frontend origin (ไม่เคยเจอตอน local dev เพราะ vite proxy บังไว้)
เทสต์นี้ยืนยันว่า response มี header ที่ browser ต้องใช้ตัดสินใจว่าจะให้ JS อ่าน response ได้หรือไม่
"""


def test_allowed_origin_gets_cors_header(client):
    resp = client.get(
        "/api/public/warranty/SN-DOES-NOT-EXIST",
        headers={"Origin": "https://sme-inventory-frontend.onrender.com"},
    )
    assert resp.headers.get("access-control-allow-origin") == "https://sme-inventory-frontend.onrender.com"


def test_local_dev_origin_gets_cors_header(client):
    resp = client.get(
        "/api/public/warranty/SN-DOES-NOT-EXIST",
        headers={"Origin": "http://localhost:5173"},
    )
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_preflight_for_login_is_allowed(client):
    """Browser ยิง OPTIONS ก่อน POST /api/auth/login เสมอเพราะมี Content-Type: application/json"""
    resp = client.options(
        "/api/auth/login",
        headers={
            "Origin": "https://sme-inventory-frontend.onrender.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "https://sme-inventory-frontend.onrender.com"


def test_untrusted_origin_does_not_get_cors_header(client):
    resp = client.get(
        "/api/public/warranty/SN-DOES-NOT-EXIST",
        headers={"Origin": "https://some-random-attacker-site.example"},
    )
    assert "access-control-allow-origin" not in resp.headers
