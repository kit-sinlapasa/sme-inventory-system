from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "branch_id": user.branch_id,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    ถอด JWT แล้วคืน User จริงจาก DB เสมอ (ไม่ใช่แค่เชื่อค่าใน token)
    เพื่อให้ role/branch_id ที่ใช้ตัดสินใจสิทธิ์เป็นค่าล่าสุดจาก DB เสมอ
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


def require_role(*allowed_roles: str):
    """
    NFR-SEC-02 — บังคับ role check ที่ SERVER ทุก endpoint ที่แก้ไขข้อมูล
    ไม่ใช่แค่ซ่อนปุ่มใน UI ฝั่ง client (STRIDE-T mitigation)
    ใช้เป็น dependency: Depends(require_admin) หรือ Depends(require_branch_staff)
    """

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' ไม่มีสิทธิ์เข้าถึง endpoint นี้",
            )
        return user

    return dependency


require_admin = require_role("Admin")
require_branch_staff = require_role("BranchStaff")
require_any_role = require_role("Admin", "BranchStaff")
