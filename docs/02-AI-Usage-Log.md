# AI Usage Disclosure Log
## SME Inventory & Order Management (NC221 โครงงานปลายภาค)

> ตามรูปแบบ Deck 05 สไลด์ 5 — บันทึกทุกครั้งที่ใช้ AI ช่วยงาน พร้อม Human Verification จริง (ไม่ใช่แค่ "ใช้ AI" แต่ต้องบอกว่าทีม**ตรวจสอบอะไรบ้าง**และ**ตัดสินใจอย่างไร**)
>
> ⚠️ **หมายเหตุความซื่อสัตย์:** log นี้เขียนย้อนหลังครอบคลุมงานที่ทำไปแล้วทั้งเซสชัน บาง entry ทีมตรวจสอบอย่างละเอียด (มีการแก้ไข/correction จริง) บาง entry ทีมแค่ตอบ "โอเค"/"ทำเลย" แบบกว้าง ๆ — ระบุไว้ตรง ๆ ในคอลัมน์ Human Verification ไม่ปัดให้ดูดีกว่าความจริง

| # | Date | Tool/Model | Task | Prompt/Context Summary | Output Used | Human Verification | Final Decision |
|---|---|---|---|---|---|---|---|
| 1 | 2026-08-24 | Claude (claude-opus-5) | อ่านและสรุปสไลด์วิชา NC221 ทั้ง 5 deck (238 หน้า) | "อ่านและทำความเข้าใจทุก slide แบบละเอียด" | `COURSE-NOTES.md` — สรุปทุกสไลด์ + แกนความคิดร่วม + checklist โครงงาน | **บางส่วน** — ทีมไม่ได้ตรวจทุกบรรทัด แต่ใช้อ้างอิงต่อในงานถัดไปและไม่มีการทักท้วง | ใช้เป็นเอกสารอ้างอิงภายในทีม ไม่ใช่ deliverable ที่ส่งอาจารย์ |
| 2 | 2026-08-24 | Claude (claude-opus-5) | วิเคราะห์โน้ตลายมือร่าง requirement (2 หน้า) แยก Need/Solution/NFR | ส่งภาพโน้ตลายมือ P1–P11 (บางส่วนอ่านไม่ออก) | วิเคราะห์โครงสร้าง Need→Requirement + ระบุช่องว่าง 3 บรรทัดที่อ่านไม่ออก | **สูง** — AI ปฏิเสธเดาข้อความที่อ่านไม่ออก ขอให้ทีมพิมพ์เองแทน (หลีกเลี่ยง hallucination ตาม Deck 02 สไลด์ 67) | ทีมพิมพ์ข้อความที่ขาดมาให้ครบ (P1–P11 ฉบับเต็ม) |
| 3 | 2026-08-24 | Claude (claude-opus-5) | ร่าง FR/NFR ชุดแรกจากโน้ตที่ยังไม่สมบูรณ์ | ข้อมูล P1–P3 บางส่วน + สมมติฐานเรื่อง "Hardware" | FR/NFR ร่างแรก (ยังไม่ถูกต้อง — สมมติ Hardware = เครื่องมือช่าง) | **สูง — พบข้อผิดพลาดจริง** ทีมแก้ไขว่า Hardware = RAM/CPU/Mainboard ไม่ใช่ตามที่ AI สมมติไว้ | **Reject** ร่างชุดแรกบางส่วน → สั่งให้ทำใหม่ทั้ง Data Model |
| 4 | 2026-08-24 | Claude (claude-opus-5) | ร่าง FR 12 ข้อ + NFR 6 ข้อ ใหม่ทั้งหมดหลัง clarify | P1–P11 ฉบับเต็ม + คำตอบเรื่อง Hardware = อุปกรณ์คอมพิวเตอร์ + ขอบเขต ihavecpu.com (เอาแค่หน้าตา/หมวดหมู่) | Requirement Package v1.0: Problem Statement, Stakeholder List (7 กลุ่ม), FR 12, NFR 6, User Story 8 + AC, Priority, RTM เริ่มต้น | **กว้าง** — ทีมตอบ "โอเค" ยืนยัน baseline แบบภาพรวม ไม่ได้ทวนทีละบรรทัด | Baseline v1.0 (ตาม Deck 02 สไลด์ 53) — **ทีมควรกลับมาอ่านละเอียดอีกรอบก่อนส่งจริง** |
| 5 | 2026-08-24 | Claude (claude-opus-5) | เสนอ CR-001 (NFR-PRIV-01) และ CR-002 (reorder point ต่อสาขา) | ทีมถาม "มีอะไรแนะนำเพิ่มไหม" | 2 Change Request พร้อม Impact Analysis | **ต่ำ** — ทีมสั่ง "ทำเลย" โดยไม่ระบุรายละเอียดเอง AI เลือก default เอง (เช่น เก็บข้อมูล 3 ปี) | Approved แบบมีเงื่อนไข — **ทีมยังไม่ได้ตรวจตัวเลข/รายละเอียดจริง ต้องทำก่อนส่งงาน** |
| 6 | 2026-08-24 | Claude (claude-opus-5) | ปรับ scope ตามไทม์ไลน์ที่แก้ไข 3 รอบ (1→4→8 สัปดาห์) → CR-003, CR-004, CR-005 | ทีมแจ้งเวลาที่เหลือทีละครั้ง | Priority ของ FR-009/010/012/NFR ถูกปรับขึ้น-ลงตามเวลาจริง | **กลาง** — ทีมยืนยันตัวเลขสัปดาห์เองโดยตรง แต่ไม่ได้ทวนรายละเอียดผลกระทบต่อ priority ทีละข้อ | Approved — ทีมควรตรวจสอบว่า priority สุดท้ายตรงกับที่ต้องการจริง |
| 7 | 2026-08-24 | Claude (claude-opus-5) | สร้าง Architecture & Design เต็มรูปแบบ: ADR-001/002, ER Model, REST API spec, User Flow 3 persona, STRIDE threat model | ทีมสั่ง "ทำต่อ" | `03-Architecture-Design.md` + อัปเดตคอลัมน์ Design ใน RTM | **ยังไม่ตรวจ** — เอกสารเพิ่งสร้าง ทีมยังไม่ได้อ่าน | Draft — **ทีมต้องอ่านและยืนยันก่อนเริ่ม implement จริงในสัปดาห์ 2** โดยเฉพาะ ADR-002 (วิธีจัดการ concurrency) ซึ่งเป็นการตัดสินใจทางเทคนิคที่สำคัญที่สุดของโปรเจกต์ |
| 8 | 2026-08-24 | Claude (claude-opus-5) | เลือก Tech Stack (ADR-003) + สร้าง repo skeleton: FastAPI backend (models/auth/sales/public warranty ใช้งานได้จริง), React frontend (หน้าเช็คประกัน), Alembic, Docker Compose, GitHub Actions CI, concurrency test | ทีมถาม "มี free ไหม" แล้วสั่ง "ทำ" | โครง repo เต็มใน `sme-inventory-system/` รวม endpoint ที่ implement จริงแล้ว 3 ตัว (`/api/auth/login`, `/api/sales`, `/api/public/warranty/{serial}`) + test 7 เคส (concurrency, idempotency, privacy schema) | ดู entry #9 | Draft (ก่อนรัน test จริง) |
| 9 | 2026-08-24 | Claude (claude-opus-5) | **รันจริง** ไม่ใช่แค่เขียน: เปิด Postgres จริงผ่าน Docker, generate+apply Alembic migration, รัน pytest ทั้ง 7 test รวม concurrency test (10 thread แข่งกันจริง) | (AI ทำเองโดยไม่ต้องให้ทีมสั่ง เพราะเป็นการตรวจสอบผลงานตัวเอง) | พบบัคจริง 2 จุดจากการรันจริง (ไม่ใช่แค่จากการอ่านโค้ด): ① test fixtures commit ข้อมูลจริงทำให้ test ตัวถัดไปชนกัน (unique constraint) ② passlib 1.7.4 เข้ากันไม่ได้กับ bcrypt รุ่นใหม่ (5.0) — แก้ทั้งคู่แล้ว pin `bcrypt==4.0.1` ใน requirements.txt | **สูงสุดเท่าที่ AI ทำเองได้** — รันจริงบน infra จริง ไม่ใช่แค่อ่านโค้ดแล้วบอกว่า "น่าจะถูก" | ผลจริง: **7/7 tests PASSED** รวม concurrency test ที่ยืนยันว่า ADR-002 ทำงานถูกต้อง — **แต่นี่คือ AI ตรวจสอบงานของ AI เอง ทีมยังต้องรันด้วยตัวเองอย่างน้อย 1 ครั้งเพื่อความมั่นใจอิสระ (independent verification) ก่อนนับเป็นหลักฐานส่งอาจารย์** |
| 10 | 2026-08-24 | Claude (claude-opus-5) | สร้าง GitHub repo จริง (`gh repo create`) + push + **debug CI failures จริงบน GitHub Actions infrastructure** (ไม่ใช่ local) | ทีมให้ URL GitHub จริงและสั่ง "push it" | Push แรกล้มเหลว 3 ครั้งจากปัญหาจริง: ① token ขาด `workflow` scope (แก้ด้วย `gh auth refresh`) ② branch default เป็น `master` แต่ CI workflow อ้างอิง `main`/`develop` (เปลี่ยนเป็น `main` + ตั้ง default บน GitHub) ③ CI ที่รันจริงพบ lint error 27 จุด (forward-reference type hint ที่ยังไม่มี `TYPE_CHECKING` import) และ frontend build ล้มเหลวเพราะไม่มี `package-lock.json` — แก้ครบแล้ว push ใหม่ | **สูงสุด — verify บน production infrastructure จริง (GitHub Actions) ไม่ใช่แค่เครื่อง local** | **ผลจริงจาก GitHub Actions: ทั้ง 2 job (backend-test, frontend-build) เขียวสมบูรณ์** — repo: https://github.com/kit-sinlapasa/sme-inventory-system |

## ขอบเขตการใช้ AI ในโครงงานนี้ (ตามหมวดที่ Deck 05 กำหนด)
✅ Requirements · ✅ Architecture · ✅ Code · ✅ Test · ✅ Documentation · ⬜ Debugging · ⬜ Data Generation · ⬜ Presentation

## ⚠️ หมายเหตุสำคัญเรื่องตำแหน่งไฟล์
ตั้งแต่ entry #8 เป็นต้นไป เอกสารชุดนี้ (`docs/*.md` ใน `sme-inventory-system/`) คือ**ฉบับหลัก** — ไฟล์ในโฟลเดอร์ `../project/` ที่สร้างไว้ก่อนหน้าเป็นเพียงสำเนาช่วงร่างต้นทาง (ก่อนมี repo) **อย่าแก้ทั้ง 2 ที่พร้อมกันเพราะจะทำให้เอกสารไม่ตรงกัน** — แก้ที่นี่ที่เดียวแล้ว commit เข้า git

## สิ่งที่ AI ถูก Reject หรือแก้ไข (ต้องมีอย่างน้อย 1 จุดตาม Deck 05 สไลด์ 7)
- **Entry #3:** AI สมมติผิดว่า "Hardware" หมายถึงเครื่องมือช่าง ทีมแก้เป็นอุปกรณ์คอมพิวเตอร์ (RAM/CPU/Mainboard) — ทำให้ต้องออกแบบ Data Model ใหม่ทั้งหมดเป็นแบบ serialized inventory (รายชิ้นมี S/N)
- **Entry #2:** AI ปฏิเสธเดาข้อความลายมือ 3 บรรทัดที่อ่านไม่ออก แทนที่จะสร้างคำตอบที่ดูน่าเชื่อถือแต่ไม่มีหลักฐาน (ตรงกับหลัก Deck 02 สไลด์ 67: "AI ที่ดีควรบอกว่า 'ฉันไม่แน่ใจ'")

## ข้อห้ามที่ทีมต้องยึดตลอดโครงการ
🚫 ห้ามใส่ Password, API Key, Personal Data ของลูกค้าจริงลงในเครื่องมือ AI
🚫 ห้ามให้ AI ตัดสินใจ Architecture/Design ขั้นสุดท้ายโดยไม่มี human review (Deck 03 สไลด์ 29)

---

## หมายเหตุสำหรับทีม

**Entry #4 และ #5 คือจุดอ่อนที่สุดของ log นี้ในตอนนี้** — การ verify แบบ "โอเค"/"ทำเลย" ไม่ใช่สิ่งที่ Deck 05 rubric ต้องการจริง ๆ (rubric ให้คะแนนจาก **"ความรับผิดชอบต่อ output + คุณภาพของการตรวจสอบโดยทีม"** ไม่ใช่แค่ปริมาณการใช้ AI) ก่อนส่งงานจริง ทีมควรกลับมานั่งอ่าน [01-Requirements-Package.md](01-Requirements-Package.md) ทีละบรรทัดจริง ๆ อย่างน้อย 1 รอบ แล้วอัปเดตคอลัมน์ Human Verification ของ entry #4–5 ให้สะท้อนการตรวจสอบจริง
