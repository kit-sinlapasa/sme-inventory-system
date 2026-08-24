from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def write_audit_log(
    db: Session,
    *,
    actor: User,
    action: str,
    entity_type: str,
    entity_id: int,
    before: dict | None = None,
    after: dict | None = None,
) -> AuditLog:
    """
    บันทึก audit log ตาม FR-011 (5W2H) — เรียกจากทุก service ที่แก้ไขข้อมูลสำคัญ
    ไม่ควรลืมเรียกฟังก์ชันนี้ในทุก endpoint ที่เปลี่ยนสถานะ Item/PR/PO
    """
    log = AuditLog(
        actor_user_id=actor.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_value=before,
        after_value=after,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
