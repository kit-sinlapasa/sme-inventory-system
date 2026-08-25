"""
Unit test — ทดสอบฟังก์ชันบริสุทธิ์แบบแยกเดี่ยว ไม่แตะฐานข้อมูลและไม่ผ่าน HTTP

แยกจาก tests/integration/ โดยตั้งใจ: ชุด integration ยิงผ่าน API จริงบน Postgres จริง
ซึ่งจับบั๊กที่เกิดจากการต่อกันของหลายชั้นได้ดี แต่บอกไม่ได้ว่าตรรกะย่อยตัวไหนผิด
ไฟล์นี้จึงเจาะเฉพาะจุดตัดสินใจที่พังแล้วเสียหายมาก แต่ทดสอบแยกได้ง่าย
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.config import Settings
from app.routers.reports import _cutoff, _scope_branch


class _FakeUser:
    """ไม่ใช้ User จริงเพราะ _scope_branch อ่านแค่ 2 ฟิลด์ — ผูกกับ ORM โดยไม่จำเป็นทำให้ test เปราะ"""

    def __init__(self, role, branch_id):
        self.role = role
        self.branch_id = branch_id


# ── NFR-SEC-02: ตรรกะตัดสินขอบเขตสาขา ────────────────────────────────────────
# ฟังก์ชันนี้คือจุดเดียวที่ตัดสินว่า request จะเห็นข้อมูลสาขาไหน ทุก report endpoint
# เรียกผ่านมันหมด ถ้าพลาดที่นี่ที่เดียว ข้อมูลข้ามสาขารั่วทุก endpoint พร้อมกัน


@pytest.mark.parametrize(
    "role,own_branch,requested,expected,why",
    [
        ("BranchStaff", 3, None, 3, "ไม่ระบุอะไรมา ต้องได้สาขาตัวเอง"),
        ("BranchStaff", 3, 3, 3, "ระบุสาขาตัวเอง ต้องได้สาขาตัวเอง"),
        ("BranchStaff", 3, 1, 3, "ระบุสาขาอื่น ต้องถูกบังคับกลับเป็นสาขาตัวเอง"),
        ("BranchStaff", 3, 999, 3, "ระบุสาขาที่ไม่มีอยู่ ก็ยังต้องได้สาขาตัวเอง"),
        ("Admin", None, None, None, "Admin ไม่ระบุ = เห็นทุกสาขา"),
        ("Admin", None, 2, 2, "Admin ระบุสาขาได้อิสระ"),
    ],
)
def test_branch_scope_decision(role, own_branch, requested, expected, why):
    assert _scope_branch(_FakeUser(role, own_branch), requested) == expected, why


def test_branch_staff_can_never_widen_scope():
    """ไล่ทุกค่าที่ client ส่งมาได้ ต้องไม่มีค่าไหนหลุดออกจากสาขาตัวเองเลย"""
    staff = _FakeUser("BranchStaff", 7)
    for attempt in [None, 0, -1, 1, 7, 8, 999, 2**31]:
        assert _scope_branch(staff, attempt) == 7, f"หลุด scope เมื่อส่ง branch_id={attempt}"


# ── ช่วงเวลาที่ใช้คำนวณรายงาน ────────────────────────────────────────────────


def test_cutoff_is_timezone_aware_and_in_the_past():
    """
    ต้องเป็น timezone-aware เพราะคอลัมน์เวลาใน DB เป็น timestamptz
    ถ้าคืน naive datetime การเปรียบเทียบจะ raise หรือเทียบผิดโซนแบบเงียบ ๆ
    """
    c = _cutoff(30)
    assert c.tzinfo is not None, "ต้องมี timezone ติดมาด้วย"
    delta = datetime.now(timezone.utc) - c
    assert timedelta(days=29, hours=23) < delta < timedelta(days=30, hours=1)


def test_cutoff_longer_window_reaches_further_back():
    assert _cutoff(90) < _cutoff(30) < _cutoff(7)


# ── ADR/deploy: แปลง scheme ของ connection string ────────────────────────────
# Render ให้ URL ขึ้นต้น postgres:// แต่ SQLAlchemy 2.0 รับเฉพาะ postgresql://
# บั๊กนี้เคยทำให้ deploy ล้มจริงมาแล้ว จึงตรึงพฤติกรรมไว้ด้วย test


@pytest.mark.parametrize(
    "given,expected",
    [
        ("postgres://u:p@h/db", "postgresql://u:p@h/db"),
        ("postgresql://u:p@h/db", "postgresql://u:p@h/db"),
        # แปลงเฉพาะตัวขึ้นต้นเท่านั้น ห้ามไปแตะคำว่า postgres ที่อยู่กลาง URL
        ("postgres://u:p@h/postgres", "postgresql://u:p@h/postgres"),
    ],
)
def test_database_url_scheme_normalised(given, expected):
    assert Settings(DATABASE_URL=given).DATABASE_URL == expected


# ── CORS: บั๊กที่เคยทำให้ demo บน production พังทั้งหน้า ───────────────────────


def test_cors_origins_split_and_trimmed():
    s = Settings(CORS_ORIGINS=" https://a.com , https://b.com ,, ")
    assert s.cors_origins_list == ["https://a.com", "https://b.com"], "ต้องตัดช่องว่างและค่าว่างทิ้ง"


def test_cors_single_origin():
    assert Settings(CORS_ORIGINS="https://only.com").cors_origins_list == ["https://only.com"]
