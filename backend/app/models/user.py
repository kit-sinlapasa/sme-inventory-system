from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.branch import Branch


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "Admin" | "BranchStaff"
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"), nullable=True)  # null สำหรับ Admin

    branch: Mapped["Branch"] = relationship(back_populates="users")
