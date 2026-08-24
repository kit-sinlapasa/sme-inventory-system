# SME Inventory & Order Management (ชื่อชั่วคราว)

ระบบจัดการสต็อกและตรวจสอบการรับประกันอะไหล่คอมพิวเตอร์แบบรายชิ้น (serialized inventory)
โครงงานปลายภาค NC221 วิศวกรรมซอฟต์แวร์ — ม.หอการค้าไทย

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
| บันทึกการขาย + concurrency (FR-004/005, NFR-REL-01) | ✅ ใช้งานได้ + **รันจริงแล้ว: 7/7 test ผ่าน รวม concurrency test 10 thread แข่งกัน** |
| เช็คประกันสาธารณะ (FR-006) | ✅ ใช้งานได้ (backend+frontend) |
| ส่วนที่เหลือ (products, items, stock, PR/PO, audit log, alerts) | 🔲 TODO สัปดาห์ 2-3 — ดู endpoint list เต็มใน `docs/03-Architecture-Design.md` ส่วนที่ 5 |

> ✅ **ยืนยันแล้ว (2026-08-24):** โครงนี้รันได้จริง ไม่ใช่แค่โค้ดที่ยังไม่เคยรัน — ทดสอบผ่าน `docker compose up db` + `alembic upgrade head` + `pytest` ครบ 7 เคสจริง พบและแก้บัค 2 จุดระหว่างทดสอบ (ดู `docs/02-AI-Usage-Log.md` entry #9) **แต่ทีมควรรันเองอีกครั้งเพื่อ independent verification ก่อนอ้างเป็นหลักฐานส่งอาจารย์**

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
