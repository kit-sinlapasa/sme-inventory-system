from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.models.branch import Branch
from app.schemas.branch import BranchOut

router = APIRouter(prefix="/api/branches", tags=["branches"])


@router.get("", response_model=list[BranchOut])
def list_branches(db: Session = Depends(get_db), current_user=Depends(require_admin)):
    """
    Admin เท่านั้น — ใช้ประกอบ dropdown ตอนรับสต็อกเข้า (ReceiveStock UI)
    ไม่ได้อยู่ใน scope FR/NFR เดิม แต่จำเป็นสำหรับ usability จริง (NFR-USE-01)
    แทนที่จะให้ Admin พิมพ์ branch_id เป็นตัวเลขดิบ ๆ
    """
    return db.query(Branch).order_by(Branch.name).all()
