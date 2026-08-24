from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.product_image import ProductImage


class Product(Base):
    """SKU — FR-001"""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # RAM | Mainboard | CPU ...
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    spec: Mapped[str | None] = mapped_column(String(255), nullable=True)
    warranty_months: Mapped[int] = mapped_column(Integer, nullable=False)

    # FR-001 "ระงับ" — soft delete เท่านั้น ห้าม hard delete เพราะ Item อ้างอิงผ่าน FK
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    items: Mapped[list["Item"]] = relationship(back_populates="product")
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.sort_order"
    )
