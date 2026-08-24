from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.limiter import limiter
from app.routers import auth, sales, public

app = FastAPI(
    title="SME Inventory & Order Management API",
    description=(
        "ระบบจัดการสต็อกและตรวจสอบการรับประกันอะไหล่คอมพิวเตอร์ "
        "— ดูสเปกเต็มที่ docs/03-Architecture-Design.md"
    ),
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(sales.router)
app.include_router(public.router)

# TODO สัปดาห์ 2-3: เพิ่ม router สำหรับ products, items, stock, branch_sku,
# purchase_requests, audit_log, alerts — ดู endpoint list เต็มใน
# docs/03-Architecture-Design.md ส่วนที่ 5 (REST API Specification)
# ทำตามรูปแบบเดียวกับ routers/sales.py และ routers/public.py


@app.get("/health")
def health_check():
    return {"status": "ok"}
