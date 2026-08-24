[![CI](https://github.com/kit-sinlapasa/sme-inventory-system/actions/workflows/ci.yml/badge.svg)](https://github.com/kit-sinlapasa/sme-inventory-system/actions/workflows/ci.yml)

# SME Inventory & Order Management (ชื่อชั่วคราว)

Repo: https://github.com/kit-sinlapasa/sme-inventory-system

ระบบจัดการสต็อกและตรวจสอบการรับประกันอะไหล่คอมพิวเตอร์แบบรายชิ้น (serialized inventory)
โครงงานปลายภาค NC221 วิศวกรรมซอฟต์แวร์ — ม.หอการค้าไทย

## 🚀 Live Deployment

| ส่วน | URL | สถานะ |
|---|---|---|
| Frontend | https://sme-inventory-frontend.onrender.com | ✅ Live |
| Backend API | https://sme-inventory-api.onrender.com | ✅ Live |
| API Docs (auto-generated) | https://sme-inventory-api.onrender.com/docs | ✅ Live |

> ⚠️ Free tier ของ Render spin down หลังไม่มีคนใช้ 15 นาที — request แรกหลังจากนั้นอาจช้า ~30-60 วินาที (ปกติ ไม่ใช่บั๊ก)

📄 เอกสารประกอบทั้งหมด (Requirement Package, Architecture & Design, AI Usage Log) อยู่ที่ `../project/`
**ก่อน commit ครั้งแรก ให้ย้าย 3 ไฟล์นั้นมาไว้ใน `docs/` ของ repo นี้** เพื่อให้เป็นส่วนหนึ่งของ git history จริง (เป็นหลักฐาน RTM/traceability ที่ Deck 05 ต้องการ)

## Tech Stack (ADR-003)
- **Backend:** Python 3.11+ · FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL
- **Frontend:** React + Vite + Tailwind CSS
- **Testing:** Pytest (backend) · Vitest (frontend)
- **CI/CD:** GitHub Actions

## Quick Start (Local Dev)

```bash
# 1. ตั้ง Postgres local
docker compose up -d db

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env   # แก้ DATABASE_URL/JWT_SECRET ตามจริง
alembic upgrade head       # สร้างตารางจาก ER Model
python -m scripts.seed     # สร้าง user/branch ทดสอบ (ดูรหัสผ่านด้านล่าง)
uvicorn app.main:app --reload --port 8000

# 3. Frontend (terminal ใหม่)
cd frontend
npm install
npm run dev
```

- Backend API docs (auto-generated จาก FastAPI): http://localhost:8000/docs
- Frontend: http://localhost:5173

## สถานะการพัฒนา (อัปเดตตามแผน 8 สัปดาห์ ดู `docs/01-Requirements-Package.md`)

| ส่วน | สถานะ |
|---|---|
| Requirement Package | ✅ Baseline v1.3 |
| Architecture & Design | ✅ v1.0 (ADR-001~003) |
| Repo Skeleton | ✅ (เอกสารนี้) |
| Auth (FR-007) | ✅ ใช้งานได้ |
| Product CRUD + suspend (FR-001) | ✅ ใช้งานได้ + test |
| รับสินค้าเข้าสต็อกรายชิ้น (FR-002) | ✅ ใช้งานได้ + test |
| ดูสต็อกเรียลไทม์ แยกตามสาขา (FR-003) | ✅ ใช้งานได้ + test |
| บันทึกการขาย + concurrency (FR-004/005, NFR-REL-01) | ✅ ใช้งานได้ + **รันจริงแล้ว: concurrency test 10 thread แข่งกัน ผ่าน** |
| เช็คประกันสาธารณะ (FR-006) | ✅ ใช้งานได้ (backend+frontend) |
| Reorder point ต่อสาขา (FR-012) | ✅ ใช้งานได้ + test — ตั้งค่า/แสดงผล + แจ้งเตือนผ่านอีเมลจริง (debounce กันสแปม, CR-006) |
| PR→PO flow (FR-009/010) | ✅ ใช้งานได้ + test — approve/reject กัน double-submit ด้วย pattern เดียวกับ ADR-002 |
| Audit log (FR-011) | ✅ ใช้งานได้ + test — `GET /api/audit-log` ค้นย้อนหลังได้ (Admin เท่านั้น) |
| รูปสินค้าสูงสุด 5 รูปต่อ SKU (FR-013) | ✅ ใช้งานได้ + test — URL-based, จัดการผ่านหน้า Products (CR-007) |
| KPI Dashboard สรุปภาพรวม (FR-014) | ✅ ใช้งานได้ — เสริมหน้า Dashboard เดิมทั้ง Admin/Branch ไม่มี endpoint ใหม่ (CR-008) — **ธีมสว่างสไตล์ dashboard.render.com จริง + กราฟแท่งแนวนอนสีผ่าน CVD-safety check (CR-010)** เฉพาะหน้านี้ |
| Branch UI (สต็อก/บันทึกขาย/คำขอสั่งซื้อ) | ✅ ใช้งานได้ — click-through ผ่าน browser จริงครบ |
| Admin UI (สต็อกรวม/สินค้า/รับสต็อก/คำขอ/audit log) | ✅ ใช้งานได้ — click-through ผ่าน browser จริงครบ |
| Seed data สาธิต (CR-009) | ✅ 60 สินค้า (6 หมวดหมู่ x 10) พร้อม Item/S/N รับเข้าจริง 2 สาขา, ขายบางส่วน, PR ครบ 3 สถานะ |
| Purge ข้อมูลผู้ซื้อเก่า (NFR-PRIV-01) | ✅ ใช้งานได้ + test — `POST /api/admin/purge-old-buyer-data` manual purge ตาม retention policy |
| Load test สาธารณะ (NFR-PERF-01) | ✅ 200 concurrent request จริง — P95 1472-1533ms (เป้าหมาย ≤2000ms) ผ่าน 2 รอบ ดู `docs/03-Architecture-Design.md` หัวข้อ 9.5 |
| STRIDE mitigation verification | ✅ ทุกข้อมี automated test กำกับแล้ว (`test_stride_mitigations.py`) — ดู `docs/03-Architecture-Design.md` หัวข้อ 7 |
| Dependency security (`pip-audit` + `npm audit`) | ✅ Backend 23→1 vulnerability (เหลือ 1 จุดที่ unreachable, ดูเหตุผลหัวข้อ 9.1) · Frontend 2→0 vulnerability (production deps) |
| Usability test (NFR-USE-01) | 🟡 ยังไม่ทำ — ต้องการผู้ใช้จริงทดลอง AI ทำแทนไม่ได้ ทีมต้องทำเองก่อนส่งงาน |
| Deploy จริง (Render) | ✅ **Live** — deploy สำเร็จหลังแก้บั๊กจริง 2 จุด (Python version, `alembic` bare command) ดู URL ด้านบน — redeploy ล่าสุดมี FR-012/013/014 ครบแล้ว (verify ผ่าน production จริง) แต่**ยังไม่ redeploy รอบ hardening ล่าสุด** (dependency upgrade + purge endpoint) ต้อง `git push` ให้ Render sync ก่อน |

> ✅ **ยืนยันแล้ว (2026-08-24):** โครงนี้รันได้จริง ไม่ใช่แค่โค้ดที่ยังไม่เคยรัน — ทดสอบผ่าน `docker compose up db` + `alembic upgrade head` + `pytest` **ครบ 57 เคสจริง** (concurrency, RBAC, soft-delete, stock isolation ระหว่างสาขา, PR→PO lifecycle, audit trail, low-stock alert debounce, product image limit, STRIDE mitigation, buyer-data purge ฯลฯ) และผ่าน CI จริงบน GitHub Actions ด้วย (ดู badge ด้านบน) **UI ทั้ง Branch และ Admin ถูกคลิกทดสอบจริงผ่าน browser** ครบ flow: login → เพิ่มสินค้า → รับสต็อก → ขาย (S/N lookup) → เช็คประกันสาธารณะ → สร้าง/ปฏิเสธคำขอสั่งซื้อ → ดู audit log → จัดการรูปสินค้า → ดู KPI dashboard พบและแก้บัคจริงหลายจุดระหว่างทาง (ดู `docs/02-AI-Usage-Log.md`) **แต่ทีมควรรันเองอีกครั้งเพื่อ independent verification ก่อนอ้างเป็นหลักฐานส่งอาจารย์**

## Test Login (local dev, สร้างจาก `python -m scripts.seed`)
| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin1234` |
| Branch Staff (สาขาสยาม) | `branch1` | `branch1234` |

## โครงสร้างโปรเจกต์
ดูเหตุผลของโครงสร้างนี้ใน ADR-003 (`docs/03-Architecture-Design.md`)

```
backend/app/
├── models/     SQLAlchemy models (ตรงกับ ER Model)
├── schemas/    Pydantic request/response
├── routers/    FastAPI endpoints แยกตาม resource
├── services/   business logic (เช่น audit log writer)
├── deps.py     auth/role dependency — จุดเดียวที่บังคับ NFR-SEC-02
└── main.py

frontend/src/
├── pages/public/   ไม่ต้อง login (FR-006)
├── pages/branch/   route guard role=BranchStaff
└── pages/admin/    route guard role=Admin
```

## Branching & Commit
ใช้ GitHub Flow (branch สั้นจาก `main` → PR → review → merge) ตาม Deck 04 — ดูเหตุผลใน `docs/01-Requirements-Package.md`

## AI Usage
ทุกจุดที่ใช้ AI ช่วยพัฒนาโปรเจกต์นี้ถูกบันทึกใน `docs/02-AI-Usage-Log.md` ตามข้อกำหนดของ Deck 05 — **ต้องอัปเดตทุกครั้งที่ใช้ AI ช่วยเขียนโค้ด ไม่ใช่แค่ตอนเขียน requirements**
