from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin, require_any_role
from app.models.branch_sku import BranchSKU
from app.models.user import User
from app.schemas.branch_sku import BranchSKUOut, ReorderPointUpdate
from app.services.audit import write_audit_log

router = APIRouter(prefix="/api/branch-sku", tags=["branch-sku"])


@router.get("/{branch_id}/{sku_id}", response_model=BranchSKUOut)
def get_reorder_point(
    branch_id: int,
    sku_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """FR-012 — Branch เห็นค่าที่ตั้งไว้ได้ (read-only), Admin แก้ไขได้ (ดู PUT ด้านล่าง)"""
    if current_user.role == "BranchStaff" and current_user.branch_id != branch_id:
        raise HTTPException(status_code=403, detail="ดูได้เฉพาะสาขาของตัวเอง")

    entry = db.query(BranchSKU).filter(BranchSKU.branch_id == branch_id, BranchSKU.sku_id == sku_id).first()
    if entry is None:
        raise HTTPException(status_code=404, detail="ยังไม่มีการตั้งค่า reorder point สำหรับคู่นี้")
    return entry


@router.put("/{branch_id}/{sku_id}", response_model=BranchSKUOut)
def set_reorder_point(
    branch_id: int,
    sku_id: int,
    payload: ReorderPointUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # CR-002 — Admin ตั้งค่ากลาง สาขาแก้เองไม่ได้
):
    """FR-012 — ตั้ง/แก้ reorder point ต่อ SKU ต่อสาขา (CR-002)"""
    entry = db.query(BranchSKU).filter(BranchSKU.branch_id == branch_id, BranchSKU.sku_id == sku_id).first()

    if entry is None:
        entry = BranchSKU(branch_id=branch_id, sku_id=sku_id, reorder_point=payload.reorder_point)
        db.add(entry)
        before = None
    else:
        before = {"reorder_point": entry.reorder_point}
        entry.reorder_point = payload.reorder_point

    db.commit()
    db.refresh(entry)

    write_audit_log(
        db,
        actor=current_user,
        action="SET_REORDER_POINT",
        entity_type="BranchSKU",
        entity_id=entry.id,
        before=before,
        after={"reorder_point": entry.reorder_point},
    )
    return entry
