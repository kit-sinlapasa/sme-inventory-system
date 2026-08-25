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

📄 **เอกสารประกอบทั้งหมดอยู่ใน [`docs/`](docs/)** — Requirement Package + RTM, Architecture & Design, AI Usage Log, Retrospective, Project Report, Usability Test และ [Release Notes](docs/07-Release-Notes.md)

📦 **เวอร์ชันที่นำเสนอ: `v1.0.0`** · ⚖️ License: [MIT](LICENSE)

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
```

> **ถ้าฐานข้อมูลมีข้อมูลอยู่แล้ว** `scripts.seed` จะ**ไม่ทำอะไรและ exit 1** เพื่อกันการเขียนทับโดยไม่ตั้งใจ
> ต้องใส่ `--reset` ถึงจะเขียนทับ · `--reset` **ลบข้อมูลในทุกตารางทิ้งก่อน** ใช้กับฐานข้อมูลสาธิตเท่านั้น
>
> **อัปเดตข้อมูลสาธิตบน production (Windows):**
>
> ```powershell
> cd backend
> .\scripts\reseed_remote.ps1
> ```
>
> แล้ววาง **External** Database URL ตอนที่สคริปต์ถาม — อย่าพิมพ์เป็น `$env:DATABASE_URL="..."` เอง
> เพราะ PowerShell แปลง `$` ใน double quote เป็นชื่อตัวแปร ถ้ารหัสผ่านมี `$` URL จะเพี้ยนเงียบ ๆ
> จนรันแล้วเหมือนสำเร็จแต่ข้อมูลไม่เปลี่ยน (เกิดขึ้นจริงมาแล้ว) · สคริปต์รับค่าผ่าน `Read-Host`
> จึงไม่ผ่าน interpolation เลย และล้างตัวแปรทิ้งให้ตอนจบ
>
> **บน macOS/Linux หรือ Git Bash:**
>
> ```bash
> cd backend && DATABASE_URL='<External Database URL>' python -m scripts.seed --reset
> ```
>
> ใช้ single quote เสมอด้วยเหตุผลเดียวกัน · บรรทัดแรกที่ออกมาต้องขึ้น `☁️ รีโมต host=dpg-...render.com`
> ถ้าขึ้น `🖥️ เครื่องนี้ (local)` แปลว่าตัวแปรไม่ติด ให้หยุดทันที

```bash
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
| Dashboard เชิงวิเคราะห์ (FR-014) | ✅ ใช้งานได้ + test — **รื้อใหม่ทั้งหน้าใน CR-013**: 5 กราฟ + 3 ตาราง + KPI 4 ช่อง บน `/api/reports/*` 8 endpoint ที่สรุปผลใน SQL · เลือกช่วง 7/30/90 วัน · กรองสาขา · คลิกดูรายละเอียดสินค้า · ธีมสว่างสไตล์ Render (CR-010) สีผ่าน CVD-safety validator |
| Branch UI (สต็อก/บันทึกขาย/คำขอสั่งซื้อ) | ✅ ใช้งานได้ — click-through ผ่าน browser จริงครบ |
| Admin UI (สต็อกรวม/สินค้า/รับสต็อก/คำขอ/audit log) | ✅ ใช้งานได้ — click-through ผ่าน browser จริงครบ |
| Seed data สาธิต (CR-009 → CR-012 → CR-013) | ✅ 60 สินค้า (6 หมวดหมู่ x 10) · **4 สาขาขนาดลดหลั่นกันจริง** · **ประวัติย้อนหลัง 9 เดือน** พร้อม Pareto (บางรุ่นขายดี บางรุ่นไม่เคยขายเลย) และ seasonality รายสัปดาห์ — จำเป็นเพื่อให้กราฟแนวโน้มมีอะไรให้อ่านจริง |
| Purge ข้อมูลผู้ซื้อเก่า (NFR-PRIV-01) | ✅ ใช้งานได้ + test — `POST /api/admin/purge-old-buyer-data` manual purge ตาม retention policy |
| Load test สาธารณะ (NFR-PERF-01) | ✅ 200 concurrent request จริง — P95 1472-1533ms (เป้าหมาย ≤2000ms) ผ่าน 2 รอบ ดู `docs/03-Architecture-Design.md` หัวข้อ 9.5 |
| STRIDE mitigation verification | ✅ ทุกข้อมี automated test กำกับแล้ว (`test_stride_mitigations.py`) — ดู `docs/03-Architecture-Design.md` หัวข้อ 7 |
| Dependency security (`pip-audit` + `npm audit`) | ✅ Backend 23→1 vulnerability (เหลือ 1 จุดที่ unreachable, ดูเหตุผลหัวข้อ 9.1) · Frontend 2→0 vulnerability (production deps) |
| Usability test (NFR-USE-01) | 🟡 **เตรียมครบแล้ว ยังไม่ได้รันกับผู้ใช้จริง** — เดิน task จริง + heuristic evaluation + พบและแก้บั๊ก 2 จุด · สคริปต์และตารางบันทึกพร้อมใน [`docs/06`](docs/06-Usability-Test-NFR-USE-01.md) · ตัวเลข "≥90% ใน 60 วินาที" ต้องมีผู้ใช้จริง 5-8 คน AI สร้างแทนไม่ได้ |
| Deploy จริง (Render) | ✅ **Live** — deploy สำเร็จหลังแก้บั๊กจริง 2 จุด (Python version, `alembic` bare command) ดู URL ด้านบน — **auto-deploy ทุกครั้งที่ merge เข้า `main`** · ตรวจล่าสุดแล้วว่าใช้งานได้ครบ: ล็อกอิน 5 บัญชี, RBAC, CORS, ข้อมูล dashboard ครบถ้วน |

> ✅ **ยืนยันแล้ว (2026-08-24):** โครงนี้รันได้จริง ไม่ใช่แค่โค้ดที่ยังไม่เคยรัน — ทดสอบผ่าน `docker compose up db` + `alembic upgrade head` + `pytest` **ครบ 91 เคสจริง** (ตรวจซ้ำได้ด้วย `python -m pytest -q`) (concurrency, RBAC, soft-delete, stock isolation ระหว่างสาขา, PR→PO lifecycle, audit trail, low-stock alert debounce, product image limit, STRIDE mitigation, buyer-data purge ฯลฯ) และผ่าน CI จริงบน GitHub Actions ด้วย (ดู badge ด้านบน) **UI ทั้ง Branch และ Admin ถูกคลิกทดสอบจริงผ่าน browser** ครบ flow: login → เพิ่มสินค้า → รับสต็อก → ขาย (S/N lookup) → เช็คประกันสาธารณะ → สร้าง/ปฏิเสธคำขอสั่งซื้อ → ดู audit log → จัดการรูปสินค้า → ดู KPI dashboard พบและแก้บัคจริงหลายจุดระหว่างทาง (ดู `docs/02-AI-Usage-Log.md`) **แต่ทีมควรรันเองอีกครั้งเพื่อ independent verification ก่อนอ้างเป็นหลักฐานส่งอาจารย์**

## Test Login (ใช้ได้ทั้ง local dev และระบบที่ deploy จริง — สร้างจาก `python -m scripts.seed`)

> ไม่ระบุจำนวนชิ้นเป๊ะ ๆ เพราะ seed สุ่มใหม่ทุกครั้ง สิ่งที่คงที่คือ**ลำดับขนาดสาขา** (สำนักงานใหญ่ > สยาม > รัชดา > รังสิต) ซึ่งตั้งใจให้ไม่เท่ากันเพื่อให้ dashboard เทียบสาขาได้อย่างมีความหมาย
| Role | Username | Password | สังกัด | สต็อกตัวอย่าง |
|---|---|---|---|---|
| Admin | `admin` | `admin1234` | ทุกสาขา | — (ดูได้ทุกสาขา แต่**ขายเองไม่ได้**) |
| Branch Staff | `hq1` | `hq1234` | สำนักงานใหญ่ | ใหญ่สุด — สต็อกครบทุกรุ่น |
| Branch Staff | `branch1` | `branch1234` | สาขาสยาม | รองลงมา |
| Branch Staff | `branch2` | `rachada1234` | สาขารัชดา | กลาง ๆ |
| Branch Staff | `branch3` | `rangsit1234` | สาขารังสิต | เล็กสุด — สาขาใหม่ สต็อกยังไม่ครบ |

> **ทำไม Admin ขายเองไม่ได้:** endpoint บันทึกขายดึง `branch_id` จาก token เสมอ (ไม่เชื่อค่าจาก client ตาม STRIDE-T) แต่ Admin ไม่สังกัดสาขาใด ระบบจึงไม่รู้ว่าจะบันทึกขายเข้าสาขาไหน — และเป็นการแยกหน้าที่ (separation of duties) ระหว่างคนอนุมัติ PR กับคนขายหน้าร้าน สำนักงานใหญ่ที่ต้องการขายจริงใช้บัญชี `hq1` ซึ่งสังกัดสาขาชัดเจน

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
