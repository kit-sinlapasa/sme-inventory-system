from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin, require_any_role, require_branch_staff
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_request import PurchaseRequest
from app.models.user import User
from app.schemas.purchase_request import (
    PurchaseOrderOut,
    PurchaseRequestCreate,
    PurchaseRequestOut,
    PurchaseRequestReject,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/api/purchase-requests", tags=["purchase-requests"])


@router.post("", response_model=PurchaseRequestOut, status_code=status.HTTP_201_CREATED)
def create_purchase_request(
    payload: PurchaseRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_branch_staff),  # FR-009 — สาขาเท่านั้น
):
    """
    FR-009 — สร้างคำขอสั่งซื้อ

    หมายเหตุ scope: ยังไม่มีระบบ push/email notification จริงไปหา Admin
    ("แจ้งเตือน HQ" ใน FR-009 ตอนนี้ทำผ่านการ query GET ?status=Pending เท่านั้น
    ดู README.md สำหรับสิ่งที่ยังไม่ implement)
    """
    product = db.get(Product, payload.sku_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=400, detail="ไม่พบ SKU นี้ หรือถูกระงับแล้ว")

    pr = PurchaseRequest(
        branch_id=current_user.branch_id,
        sku_id=payload.sku_id,
        quantity=payload.quantity,
        status="Pending",
        requested_by=current_user.id,
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)

    write_audit_log(
        db,
        actor=current_user,
        action="CREATE_PR",
        entity_type="PurchaseRequest",
        entity_id=pr.id,
        before=None,
        after={"sku_id": pr.sku_id, "quantity": pr.quantity, "status": "Pending"},
    )
    return pr


@router.get("", response_model=list[PurchaseRequestOut])
def list_purchase_requests(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """Admin เห็นทุกสาขา, Branch เห็นเฉพาะของตัวเอง (NFR-SEC-02 — บังคับที่ server)"""
    query = db.query(PurchaseRequest)
    if current_user.role == "BranchStaff":
        query = query.filter(PurchaseRequest.branch_id == current_user.branch_id)
    if status_filter:
        query = query.filter(PurchaseRequest.status == status_filter)
    return query.order_by(PurchaseRequest.requested_at.desc()).all()


@router.post("/{pr_id}/approve", response_model=PurchaseOrderOut)
def approve_purchase_request(
    pr_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # FR-010 — Admin เท่านั้น
):
    """
    FR-010 — อนุมัติ PR แล้วสร้าง PO อัตโนมัติ

    ใช้ conditional update pattern เดียวกับ ADR-002 (routers/sales.py):
    เปลี่ยนสถานะได้ก็ต่อเมื่อยัง 'Pending' อยู่ ณ ขณะนั้นเท่านั้น — กันกรณี
    อนุมัติซ้ำ (double-submit) หรือ Admin สองคนตัดสินใจ PR เดียวกันพร้อมกัน
    """
    result = db.execute(
        update(PurchaseRequest)
        .where(PurchaseRequest.id == pr_id, PurchaseRequest.status == "Pending")
        .values(status="Approved", decided_by=current_user.id, decided_at=func.now())
    )
    if result.rowcount == 0:
        db.rollback()
        pr = db.get(PurchaseRequest, pr_id)
        if pr is None:
            raise HTTPException(status_code=404, detail="ไม่พบคำขอนี้")
        raise HTTPException(status_code=409, detail=f"คำขอนี้ถูกตัดสินใจไปแล้ว (สถานะ: {pr.status})")

    po = PurchaseOrder(pr_id=pr_id, created_by=current_user.id)
    db.add(po)
    db.commit()
    db.refresh(po)

    write_audit_log(
        db,
        actor=current_user,
        action="APPROVE_PR",
        entity_type="PurchaseRequest",
        entity_id=pr_id,
        before={"status": "Pending"},
        after={"status": "Approved", "po_id": po.id},
    )
    return po


@router.post("/{pr_id}/reject", response_model=PurchaseRequestOut)
def reject_purchase_request(
    pr_id: int,
    payload: PurchaseRequestReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # FR-010 — Admin เท่านั้น
):
    """FR-010 — ปฏิเสธ PR พร้อมเหตุผล (บังคับกรอก ตาม US-07 AC)"""
    result = db.execute(
        update(PurchaseRequest)
        .where(PurchaseRequest.id == pr_id, PurchaseRequest.status == "Pending")
        .values(
            status="Rejected",
            decided_by=current_user.id,
            decided_at=func.now(),
            reject_reason=payload.reason,
        )
    )
    if result.rowcount == 0:
        db.rollback()
        pr = db.get(PurchaseRequest, pr_id)
        if pr is None:
            raise HTTPException(status_code=404, detail="ไม่พบคำขอนี้")
        raise HTTPException(status_code=409, detail=f"คำขอนี้ถูกตัดสินใจไปแล้ว (สถานะ: {pr.status})")

    db.commit()
    pr = db.get(PurchaseRequest, pr_id)

    write_audit_log(
        db,
        actor=current_user,
        action="REJECT_PR",
        entity_type="PurchaseRequest",
        entity_id=pr_id,
        before={"status": "Pending"},
        after={"status": "Rejected", "reason": payload.reason},
    )
    return pr
