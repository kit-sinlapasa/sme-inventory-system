from slowapi import Limiter
from slowapi.util import get_remote_address

# STRIDE-D mitigation (docs/03-Architecture-Design.md ส่วนที่ 7)
# แยกไฟล์นี้ออกมาเพื่อเลี่ยง circular import ระหว่าง main.py กับ routers/*.py
limiter = Limiter(key_func=get_remote_address)
