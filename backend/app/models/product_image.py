from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class ProductImage(Base):
    """
    รูปสินค้า — FR-013 (CR-007), สูงสุด 5 รูปต่อ SKU บังคับที่ router ไม่ใช่ DB constraint
    เก็บเป็น URL เท่านั้น (ไม่ใช่ไฟล์อัปโหลด) — ดูเหตุผลใน CR-007
    ตาราง**แยก**จาก Product แทนคอลัมน์ image1-image5 ตามหลัก 1NF (Deck 02/03)
    """

    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="images")
