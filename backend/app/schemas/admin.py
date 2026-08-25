from datetime import datetime

from pydantic import BaseModel


class PurgeBuyerDataOut(BaseModel):
    purged_count: int
    cutoff: datetime


class SmtpCheckOut(BaseModel):
    """
    ผลตรวจการเชื่อมต่อ SMTP — จงใจไม่คืน "ค่า" ของตัวแปรใด ๆ คืนแค่ว่า "ตั้งไว้หรือยัง"
    เพื่อไม่ให้ endpoint นี้กลายเป็นช่องอ่าน credential ออกจากระบบ
    """

    configured: bool
    settings_present: dict[str, bool]
    connection: str  # ok | auth_failed | blocked | error | not_configured
    detail: str
