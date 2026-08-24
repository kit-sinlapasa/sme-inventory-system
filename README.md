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
| Reorder point ต่อสาขา (FR-012) | 🟡 ตั้งค่า+แสดงผลทำแล้ว ยังไม่มีกลไกแจ้งเตือน |
| Audit log (FR-011) | 🟡 บันทึกอัตโนมัติทุก mutation แล้ว ยังไม่มี endpoint ให้ค้นดู |
| PR→PO flow (FR-009/010), alerts, หน้า Branch/Admin UI | 🔲 TODO สัปดาห์ 3+ — ดู endpoint list เต็มใน `docs/03-Architecture-Design.md` ส่วนที่ 5 |
| Deploy จริง (Render) | ✅ **Live** — deploy สำเร็จหลังแก้บั๊กจริง 2 จุด (Python version, `alembic` bare command) ดู URL ด้านบน |

> ✅ **ยืนยันแล้ว (2026-08-24):** โครงนี้รันได้จริง ไม่ใช่แค่โค้ดที่ยังไม่เคยรัน — ทดสอบผ่าน `docker compose up db` + `alembic upgrade head` + `pytest` **ครบ 20 เคสจริง** (concurrency, RBAC, soft-delete, stock isolation ระหว่างสาขา ฯลฯ) และผ่าน CI จริงบน GitHub Actions ด้วย (ดู badge ด้านบน) พบและแก้บัคจริงหลายจุดระหว่างทาง (ดู `docs/02-AI-Usage-Log.md`) **แต่ทีมควรรันเองอีกครั้งเพื่อ independent verification ก่อนอ้างเป็นหลักฐานส่งอาจารย์**

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
