from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    branch_id: int | None
    # ชื่อผู้ใช้ + ชื่อสาขา ส่งกลับมาเลยเพื่อให้ UI แสดงได้ว่ากำลังทำงานในนามใคร/สาขาไหน
    # (เดิมมีแค่ branch_id ซึ่งผู้ใช้ดูแล้วไม่รู้ว่าสาขาอะไร และ /api/branches เป็น admin-only
    # พนักงานสาขาจึงหาชื่อสาขาตัวเองไม่ได้)
    username: str
    branch_name: str | None
