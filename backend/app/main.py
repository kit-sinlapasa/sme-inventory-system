from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.limiter import limiter
from app.routers import (
    audit_log,
    auth,
    branch_sku,
    branches,
    items,
    products,
    public,
    purchase_requests,
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

# TODO สัปดาห์ 4+: alerts (แจ้งเตือน reorder จริง), NFR-PRIV-01 purge endpoint
# ดู endpoint list เต็มใน docs/03-Architecture-Design.md ส่วนที่ 5


@app.get("/health")
def health_check():
    return {"status": "ok"}
