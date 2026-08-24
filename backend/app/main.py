from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.limiter import limiter
from app.routers import (
    admin,
    audit_log,
    auth,
    branch_sku,
    branches,
    items,
    products,
    public,
    purchase_requests,
    reports,
    sales,
    stock,
)

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

# สัปดาห์ 8 — frontend/backend อยู่คนละ origin กันจริงบน production (Render 2 service แยกกัน)
# ไม่มี middleware นี้ = browser จริงบล็อก response ทุก request แม้แต่ POST /api/auth/login
# (พบระหว่างเตรียม screenshot ของ demo — ไม่เคยเจอตอน local dev เพราะ vite proxy บังไว้)
# allow_credentials=False เพราะ auth ใช้ Bearer token ใน header ไม่ใช่ cookie เลยไม่ต้องพึ่ง credentials mode
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sales.router)
app.include_router(public.router)
app.include_router(products.router)
app.include_router(items.router)
app.include_router(stock.router)
app.include_router(branch_sku.router)
app.include_router(purchase_requests.router)
app.include_router(audit_log.router)
app.include_router(branches.router)
app.include_router(admin.router)
app.include_router(reports.router)  # CR-013 — สรุปผลสำหรับ dashboard เชิงวิเคราะห์


@app.get("/health")
def health_check():
    return {"status": "ok"}
