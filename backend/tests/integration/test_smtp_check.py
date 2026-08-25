"""
เครื่องมือวินิจฉัยการตั้งค่า SMTP (FR-012) — GET /api/admin/smtp-check

เขียนขึ้นเพราะตอนตั้งค่าอีเมลแจ้งเตือนบน production แล้วเมลไม่ออก อาการของทั้งสามสาเหตุ
(ตั้งค่าไม่ครบ / รหัสผ่านผิด / hosting บล็อกพอร์ต) เหมือนกันหมดคือ "ไม่มีเมล" แยกไม่ออก

สิ่งที่เทสต์ชุดนี้ต้องคุมให้ได้ นอกจากว่ามันตอบถูก คือ **มันต้องไม่กลายเป็นช่องอ่าน
credential ออกจากระบบ** — ซึ่งอันตรายกว่าปัญหาที่มันถูกสร้างมาแก้เสียอีก
"""
import smtplib
import socket

import pytest

from app.config import settings


@pytest.fixture()
def smtp_configured(monkeypatch):
    """ตั้งค่าครบ เพื่อให้โค้ดเดินเลยจุด not_configured ไปถึงขั้นต่อจริง"""
    monkeypatch.setattr(settings, "ALERT_EMAIL", "boss@example.com")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "sender@example.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "s3cr3t-app-password")
    monkeypatch.setattr(settings, "SMTP_FROM", "sender@example.com")


def _get(client, token):
    return client.get("/api/admin/smtp-check", headers={"Authorization": f"Bearer {token}"})


# --- สิทธิ์เข้าถึง (NFR-SEC-02) ---

def test_branch_staff_cannot_read_smtp_status(client, branch_staff_token):
    """
    endpoint นี้เปิดเผยว่า credential ตัวไหน "ถูกตั้งไว้แล้วบ้าง" ซึ่งเป็นข้อมูลที่พนักงานสาขา
    ไม่ควรเห็น — ต้องเป็น Admin เท่านั้น
    """
    assert _get(client, branch_staff_token).status_code == 403


def test_requires_authentication(client):
    assert client.get("/api/admin/smtp-check").status_code == 401


# --- แยกสาเหตุออกจากกันได้จริง ---

def test_reports_not_configured_when_alert_email_missing(client, admin_token, monkeypatch):
    """
    ALERT_EMAIL ว่าง = notifications.py จะ log แทนการส่ง — ต้องรายงานตรงกัน
    ไม่ใช่ไปพยายามต่อ SMTP แล้วรายงานผลคนละเรื่อง
    """
    monkeypatch.setattr(settings, "ALERT_EMAIL", "")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")

    body = _get(client, admin_token).json()
    assert body["connection"] == "not_configured"
    assert body["configured"] is False
    assert body["settings_present"]["ALERT_EMAIL"] is False
    assert body["settings_present"]["SMTP_HOST"] is True


def test_reports_auth_failed_separately_from_blocked(client, admin_token, smtp_configured, monkeypatch):
    """รหัสผ่านผิด ต้องได้ auth_failed ไม่ใช่ error รวม ๆ"""
    class _Server:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self): pass
        def login(self, u, p):
            raise smtplib.SMTPAuthenticationError(535, b"5.7.8 Username and Password not accepted")

    monkeypatch.setattr(smtplib, "SMTP", lambda *a, **k: _Server())

    body = _get(client, admin_token).json()
    assert body["connection"] == "auth_failed"


def test_reports_blocked_when_connection_times_out(client, admin_token, smtp_configured, monkeypatch):
    """
    ต่อไม่ติดเลย = hosting น่าจะบล็อก outbound SMTP ซึ่งเป็นคนละปัญหากับรหัสผิด
    และแก้คนละทาง — ถ้าแยกไม่ออกก็ไล่ผิดทางได้ง่าย
    """
    def _boom(*a, **k):
        raise socket.timeout("timed out")

    monkeypatch.setattr(smtplib, "SMTP", _boom)

    body = _get(client, admin_token).json()
    assert body["connection"] == "blocked"


def test_reports_ok_when_login_succeeds(client, admin_token, smtp_configured, monkeypatch):
    class _Server:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self): pass
        def login(self, u, p): pass

    monkeypatch.setattr(smtplib, "SMTP", lambda *a, **k: _Server())

    body = _get(client, admin_token).json()
    assert body["connection"] == "ok"
    assert body["configured"] is True


def test_does_not_send_a_real_email(client, admin_token, smtp_configured, monkeypatch):
    """
    ตรวจสุขภาพต้องไม่รบกวนผู้รับ — ถ้ามันส่งเมลจริงทุกครั้งที่กด คนที่อยู่ใน ALERT_EMAIL
    จะโดนสแปมจากการกดตรวจ
    """
    sent = []

    class _Server:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self): pass
        def login(self, u, p): pass
        def send_message(self, msg): sent.append(msg)
        def sendmail(self, *a, **k): sent.append(a)

    monkeypatch.setattr(smtplib, "SMTP", lambda *a, **k: _Server())

    _get(client, admin_token)
    assert sent == []


# --- ห้ามรั่ว credential (เหตุผลหลักที่เทสต์ชุดนี้มีอยู่) ---

def test_never_returns_the_actual_secret_values(client, admin_token, smtp_configured, monkeypatch):
    """
    settings_present ต้องเป็น boolean ล้วน — ถ้าเผลอเปลี่ยนเป็นคืนค่าจริงเมื่อไหร่
    endpoint นี้จะกลายเป็นช่องอ่านรหัสผ่านออกจากระบบผ่าน HTTP
    """
    class _Server:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self): pass
        def login(self, u, p): pass

    monkeypatch.setattr(smtplib, "SMTP", lambda *a, **k: _Server())

    raw = _get(client, admin_token).text
    assert "s3cr3t-app-password" not in raw
    assert "sender@example.com" not in raw
    assert "boss@example.com" not in raw
    assert all(isinstance(v, bool) for v in _get(client, admin_token).json()["settings_present"].values())


def test_redacts_secrets_that_leak_into_the_error_message(client, admin_token, smtp_configured, monkeypatch):
    """
    ไลบรารีภายนอกอาจใส่ค่าที่ส่งเข้าไปกลับมาใน error โดยที่เราคุมไม่ได้
    จึงตัดออกเองอีกชั้นแทนที่จะเชื่อว่ามันไม่ทำ — จำลองกรณีเลวร้ายที่สุด
    """
    def _leaky(*a, **k):
        raise RuntimeError("SMTP handshake failed for sender@example.com pw=s3cr3t-app-password")

    monkeypatch.setattr(smtplib, "SMTP", _leaky)

    raw = _get(client, admin_token).text
    assert "s3cr3t-app-password" not in raw
    assert "sender@example.com" not in raw
    assert "[ตัดออก]" in _get(client, admin_token).json()["detail"]
