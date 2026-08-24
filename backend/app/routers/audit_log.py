from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogOut

router = APIRouter(prefix="/api/audit-log", tags=["audit-log"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_log(
    entity_type: str | None = None,
    entity_id: int | None = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # FR-011 — Admin เท่านั้น (audit trail ไม่ใช่ทุกคนดูได้)
):
    """FR-011, NFR-MAINT-01 — ใช้ index บน entity_id/occurred_at ที่มีอยู่แล้วใน DB"""
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        query = query.filter(AuditLog.entity_id == entity_id)
    return query.order_by(AuditLog.occurred_at.desc()).limit(limit).all()
