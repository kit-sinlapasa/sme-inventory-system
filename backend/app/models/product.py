from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    """SKU — FR-001"""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # RAM | Mainboard | CPU ...
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    spec: Mapped[str | None] = mapped_column(String(255), nullable=True)
    warranty_months: Mapped[int] = mapped_column(Integer, nullable=False)

    items: Mapped[list["Item"]] = relationship(back_populates="product")
