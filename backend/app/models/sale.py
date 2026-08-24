from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Sale(Base):
    """
    บันทึกการขาย ผูก S/N กับผู้ซื้อ — FR-004, FR-005
    item_id เป็น unique เพื่อบังคับกฎ '1 ชิ้นขายได้ครั้งเดียว' ที่ระดับ schema
    (ป้องกันชั้นที่ 2 ร่วมกับ ADR-002 conditional update)
    """

    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), unique=True, nullable=False)
    buyer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    buyer_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False)
    sold_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    warranty_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # FR-005

    # ADR-002 — กัน retry ซ้ำจากเน็ตช้าไม่ให้สร้างรายการซ้ำ
    idempotency_key: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)

    # NFR-PRIV-01 (CR-001) — true เมื่อ buyer_name/buyer_phone ถูก anonymize แล้ว
    buyer_data_purged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    item: Mapped["Item"] = relationship(back_populates="sale")
