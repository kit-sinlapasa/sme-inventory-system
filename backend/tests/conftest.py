"""
Fixtures สำหรับ test — ต้องมี Postgres จริงรันอยู่ (docker compose up -d db ตอน dev,
หรือ service container ที่ .github/workflows/ci.yml ตั้งไว้แล้วตอน CI)

⚠️ ตั้ง DATABASE_URL ให้ชี้ไปที่ database แยกจาก dev เสมอ (ดู .github/workflows/ci.yml
ใช้ sme_inventory_test ไม่ใช่ sme_inventory)
"""
import pytest
from fastapi.testclient import TestClient
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base
from app.main import app
from app.models.branch import Branch
from app.models.item import Item
from app.models.product import Product
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

engine = create_engine(settings.DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """
    ล้างข้อมูลทุกตารางก่อนแต่ละ test — จำเป็นเพราะ fixture ต่าง ๆ (branch, product,
    in_stock_item ฯลฯ) เรียก db.commit() จริง ทำให้ rollback() ตอนจบ test ไม่ช่วยอะไร
    (ข้อมูลถูก commit ถาวรไปแล้ว) ถ้าไม่ล้าง จะชน unique constraint (เช่น serial_number)
    ตั้งแต่ test ที่ 2 เป็นต้นไป
    """
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    yield


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture()
def client():
    """
    หมายเหตุ: ไม่ override get_db ด้วย session เดียวกับ fixture `db` ตรง ๆ
    เพราะ concurrency test (tests/concurrency/) ต้องการให้แต่ละ thread
    เปิด connection ของตัวเอง เพื่อจำลอง concurrent request ที่สมจริง
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def branch(db):
    b = Branch(name="สาขาทดสอบ", address="123 ถนนทดสอบ")
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@pytest.fixture()
def other_branch(db):
    b = Branch(name="สาขาอื่น", address="456 ถนนอื่น")
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def _make_user(db, username, role, branch_id=None):
    user = User(
        username=username,
        password_hash=pwd_context.hash("testpassword123"),
        role=role,
        branch_id=branch_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(client, username):
    resp = client.post("/api/auth/login", json={"username": username, "password": "testpassword123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def branch_staff_user(db, branch):
    return _make_user(db, "branch_staff_test", "BranchStaff", branch_id=branch.id)


@pytest.fixture()
def branch_staff_token(client, branch_staff_user):
    return _login(client, "branch_staff_test")


@pytest.fixture()
def admin_user(db):
    return _make_user(db, "admin_test", "Admin", branch_id=None)


@pytest.fixture()
def admin_token(client, admin_user):
    return _login(client, "admin_test")


@pytest.fixture()
def product(db):
    p = Product(category="RAM", brand="TestBrand", model="TB-16GB", warranty_months=12)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture()
def in_stock_item(db, branch, product):
    item = Item(sku_id=product.id, serial_number="SN-TEST-0001", branch_id=branch.id, status="InStock")
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture()
def count_queries():
    """
    นับจำนวน SQL statement ที่ถูกยิงจริงระหว่างเรียกฟังก์ชันที่ส่งเข้ามา

    ใช้ยืนยันว่า endpoint ที่คืนหลายแถวไม่ได้ยิง query เพิ่มทีละแถว (N+1) —
    บั๊กชนิดนี้ไม่มีอะไรฟ้องเลยเพราะผลลัพธ์ถูกต้องทุกประการ แค่ช้าลงเรื่อย ๆ
    ตามจำนวนข้อมูล จึงต้องวัดที่ "จำนวน query" ไม่ใช่ที่ค่าที่คืนออกมา

        rows, n = count_queries(lambda: client.get(...).json())

    ⚠️ ต้องดักฟังที่ `app.database.engine` ไม่ใช่ `engine` ของ conftest —
    ไฟล์นี้สร้าง engine ของตัวเองไว้ใช้กับ fixture ฝั่ง test ส่วน request ที่ยิงผ่าน
    TestClient เดินผ่าน engine ของแอป คนละตัวกัน · ดักผิดตัวแล้วจะนับได้แต่ query
    ของ fixture ทำให้ test ผ่านตลอดแม้ endpoint จะเป็น N+1 จริง (เจอมาแล้วตอนเขียน
    test นี้ — รันกับโค้ดที่ยังเป็น N+1 แล้วมันไม่ FAIL จึงรู้ว่าวัดผิดที่)
    """
    from sqlalchemy import event

    from app.database import engine as app_engine

    def run(fn):
        seen = []

        def on_exec(conn, cursor, statement, params, context, executemany):
            seen.append(statement)

        event.listen(app_engine, "before_cursor_execute", on_exec)
        try:
            result = fn()
        finally:
            event.remove(app_engine, "before_cursor_execute", on_exec)
        return result, len(seen)

    return run
