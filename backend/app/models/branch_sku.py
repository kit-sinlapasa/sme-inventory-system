from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BranchSKU(Base):
    """
    Associative entity แก้ปัญหา M:N ระหว่าง Branch และ Product (Deck 02 สไลด์ 14)
    เก็บ reorder_point ต่อ SKU ต่อสาขา — ตาม CR-002
    """

    __tablename__ = "branch_skus"
    __table_args__ = (UniqueConstraint("branch_id", "sku_id", name="uq_branch_sku"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False)
    sku_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # FR-012
