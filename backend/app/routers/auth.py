from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import create_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """FR-007 — Backoffice login พร้อมกำหนดสิทธิ์ตาม role (Admin/BranchStaff)"""
    user = db.query(User).filter(User.username == payload.username).first()

    if not user or not pwd_context.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user)
    return TokenResponse(
        access_token=token,
        role=user.role,
        branch_id=user.branch_id,
        username=user.username,
        branch_name=user.branch.name if user.branch else None,  # Admin ไม่สังกัดสาขา = None
    )
