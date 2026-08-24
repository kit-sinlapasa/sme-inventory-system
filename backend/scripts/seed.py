"""
Seed ข้อมูลเริ่มต้นสำหรับ local dev / demo — ไม่ใช้กับ production
รัน: cd backend && python -m scripts.seed
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Windows console เริ่มต้นด้วย cp1252 ซึ่ง print ข้อความไทยไม่ได้ (พังจริงตอน dev บน Windows)
if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from passlib.context import CryptContext  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.branch import Branch  # noqa: E402
from app.models.user import User  # noqa: E402

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed():
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == "admin").first():
            print("Seed data มีอยู่แล้ว — ข้าม")
            return

        hq = Branch(name="สำนักงานใหญ่", address="กรุงเทพฯ")
        branch1 = Branch(name="สาขาสยาม", address="สยามสแควร์")
        db.add_all([hq, branch1])
        db.commit()
        db.refresh(hq)
        db.refresh(branch1)

        admin = User(
            username="admin",
            password_hash=pwd_context.hash("admin1234"),
            role="Admin",
            branch_id=None,
        )
        branch_staff = User(
            username="branch1",
            password_hash=pwd_context.hash("branch1234"),
            role="BranchStaff",
            branch_id=branch1.id,
        )
        db.add_all([admin, branch_staff])
        db.commit()

        print("Seed สำเร็จ:")
        print("  Admin      -> username: admin      password: admin1234")
        print(f"  BranchStaff -> username: branch1    password: branch1234  (สาขา: {branch1.name})")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
