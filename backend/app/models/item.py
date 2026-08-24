from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.branch import Branch
    from app.models.product import Product
    from app.models.sale import Sale


class Item(Base):
    """หนึ่งชิ้นสินค้าจริง มี S/N เฉพาะตัว — FR-002 (serialized inventory)"""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="InStock", nullable=False)  # InStock | Sold
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="items")
    branch: Mapped["Branch"] = relationship(back_populates="items")
    sale: Mapped["Sale | None"] = relationship(back_populates="item", uselist=False)
