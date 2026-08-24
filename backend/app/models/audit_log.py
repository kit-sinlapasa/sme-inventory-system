from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditLog(Base):
    """บันทึกทุกการเปลี่ยนแปลงสำคัญ — ใคร/ทำอะไร/เมื่อไหร่/ค่าก่อน-หลัง (FR-011, 5W2H)"""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # เช่น "CREATE_SALE", "APPROVE_PR"
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    before_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )  # NFR-MAINT-01 — index เพื่อ query ย้อนหลังได้เร็ว
