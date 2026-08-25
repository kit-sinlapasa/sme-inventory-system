# Release Notes

> ครอบคลุมหัวข้อ **Release** ตามตาราง Technical Evidence: Version/Tag · Environment ·
> Deployment evidence · Rollback · Known issues

---

## v1.1.0 — เวอร์ชันที่นำเสนอ (2026-08-25)

**Git tag:** `v1.1.0` · **Branch:** `main`

ดู commit ที่ถูก tag ได้ด้วย `git show v1.1.0` และเทียบกับเวอร์ชันก่อนด้วย `git log v1.0.0..v1.1.0`

### Environment

| Environment | URL | ใช้ทำอะไร | ฐานข้อมูล |
|---|---|---|---|
| **Production** | [sme-inventory-frontend.onrender.com](https://sme-inventory-frontend.onrender.com) · [API](https://sme-inventory-api.onrender.com) | เวอร์ชันที่ใช้นำเสนอ | Render PostgreSQL (free tier) |
| **CI** | GitHub Actions | รัน lint + test ทุก push/PR | Postgres service container |
| **Local dev** | `localhost:5173` · `localhost:8000` | พัฒนา | Postgres ใน Docker |

> ⚠️ Render free tier **หยุดทำงานหลังไม่มีคนใช้ 15 นาที** — request แรกหลังจากนั้นใช้เวลา
> ~30-60 วินาที เป็นพฤติกรรมปกติของ tier นี้ ไม่ใช่บั๊ก · **ตอน demo ควรเปิดเว็บทิ้งไว้ก่อน
> เริ่มนำเสนอ** เพื่อให้เครื่องตื่นแล้ว

### Deployment evidence

| หลักฐาน | ตรวจได้ที่ |
|---|---|
| CI ผ่านทุก job ก่อน merge | [GitHub Actions](https://github.com/kit-sinlapasa/sme-inventory-system/actions/workflows/ci.yml) — badge บน README |
| Deploy อัตโนมัติเมื่อ merge เข้า `main` | Render auto-deploy (ไม่ได้ตั้ง `autoDeploy: false` ใน `render.yaml`) |
| ระบบ live จริง | `GET /health` → `{"status":"ok"}` · หน้าเว็บโหลดได้ |
| ตรวจหลังส่งมอบ | 17/17 ข้อ — ล็อกอิน 5 บัญชี, RBAC, CORS, ความครบถ้วนของข้อมูล dashboard |

### ขอบเขตของเวอร์ชันนี้

ครบทุก FR-001 ถึง FR-015 (15 ข้อ) และ NFR ทั้ง 8 ข้อ ครบทั้ง 7 หมวด · **NFR-USE-01 ทดสอบกับผู้ใช้จริง 5 คนแล้ว
เมื่อ 2026-08-25 สำเร็จ 5/5** โดยระบุข้อจำกัดเรื่องขนาดกลุ่มไว้ตรง ๆ (ดู K-01) · รายละเอียดการ trace กลับไปหา requirement อยู่ใน
[RTM](01-Requirements-Package.md)

---

## Rollback

ระบบ deploy จาก `main` โดยตรง การย้อนกลับจึงทำได้ 2 ทาง

**ทางที่ 1 — Render dashboard (เร็วที่สุด ~1 นาที)**
เข้า service `sme-inventory-api` → **Deploys** → เลือก deploy ที่ต้องการ → **Redeploy**
ไม่ต้องแตะ git เลย เหมาะกับกรณีที่ต้องกู้คืนทันทีระหว่าง demo

**ทางที่ 2 — ย้อนผ่าน git (เก็บประวัติไว้ครบ)**

```bash
git revert -m 1 <merge-commit-ที่มีปัญหา>
```

แล้วเปิด PR ตามปกติ — **`main` มี branch protection อยู่ push ตรงไม่ได้** ต้องผ่าน PR และ CI
เสมอแม้ในกรณีฉุกเฉิน (ตั้งใจให้เป็นแบบนั้น ถ้าจำเป็นจริง ๆ เจ้าของ repo ปิด protection
ชั่วคราวได้จาก Settings)

> **ข้อควรระวังเรื่องฐานข้อมูล:** การ rollback โค้ดไม่ย้อน migration ที่รันไปแล้ว
> ถ้าเวอร์ชันที่มีปัญหามี migration ที่ทำลายโครงสร้าง ต้องเขียน downgrade migration แยก —
> เวอร์ชันนี้ไม่มี migration แบบนั้น (การเปลี่ยนแปลงล่าสุดเป็น additive ทั้งหมด)

---

## Known issues

จัดตามความรุนแรง — ทุกข้อบันทึกไว้ตั้งใจ ไม่ได้ซ่อน

### 🟡 ต้องดำเนินการก่อนใช้งานจริง

| # | เรื่อง | ผลกระทบ | ทางแก้ |
|---|---|---|---|
| K-02 | **Code review ยังไม่มีคนที่ 2** | PR ทุกใบ `reviews = 0` ผู้เขียนกับผู้ merge เป็นคนเดียวกัน | ให้เพื่อนร่วมชั้นรีวิว PR |
| K-03 | **อีเมลแจ้งเตือนบน production ยังเป็น dev-mode** | `SMTP_HOST`/`ALERT_EMAIL` บน Render ยังว่าง ระบบ log แทนการส่งจริง — ตั้งใจ เพราะ credential ต้องตั้งโดยทีมเท่านั้น ไม่ผ่าน AI | ตั้งค่าใน Render dashboard |

### 🟢 ยอมรับความเสี่ยงไว้ พร้อมเหตุผล

| # | เรื่อง | ทำไมยอมรับได้ |
|---|---|---|
| K-01 | **ปิดแล้ว 2026-08-25** — NFR-USE-01 ทดสอบกับผู้ใช้จริง 5 คน สำเร็จ 5/5 เฉลี่ย 19.6 วิ | เหลือข้อจำกัดที่ระบุไว้ตรง ๆ: **n=5 ยังไม่พอยืนยันเกณฑ์ ≥90% เชิงสถิติ** ต้องราว 30 คน · คงเลข K-01 ไว้ไม่ลบทิ้ง เพราะเอกสารอื่นเคยอ้างถึง |
| K-04 | `ecdsa` 0.19.2 (PYSEC-2026-1325) ยังไม่มี patch | unreachable จริง — ระบบใช้ HS256 เท่านั้น ไม่แตะ ECDSA |
| K-05 | esbuild/vite dev-server CVE | กระทบเฉพาะตอนรัน `npm run dev` บนเครื่อง dev ไม่กระทบ production ที่เสิร์ฟไฟล์ build แล้ว · แก้ต้อง major bump vite 5→8 |
| K-06 | Purge ข้อมูลผู้ซื้อเป็น manual endpoint | ลด scope ไว้ตั้งแต่ CR-005 — ถ้าไม่มีใครกดเรียก ข้อมูลจะไม่ถูกลบอัตโนมัติ |
| K-07 | `/api/items` และ `/api/stock` จำกัด 200/500 แถว ยังไม่มี pagination | พอสำหรับขนาดข้อมูลปัจจุบัน (~1,200 ชิ้น) · **รายงานสรุปทั้งหมดใช้ `/api/reports/*` ที่ group ใน SQL จึงไม่ถูก limit นี้กระทบ** |
| K-08 | ฐานข้อมูลสาธิตมีรายการขายชื่อ "สมชาย ทดสอบระบบ" หลายรายการ | เกิดจากการถ่ายภาพหน้าจอ "บันทึกขายสำเร็จ" ซึ่งต้องขายจริงถึงถ่ายได้ ไม่ใช่ข้อมูลลูกค้าจริง |

---

## ประวัติเวอร์ชัน

| เวอร์ชัน | วันที่ | สาระสำคัญ |
|---|---|---|
| **v1.1.0** | 2026-08-25 | **เวอร์ชันนำเสนอ** — เพิ่ม FR-015 ค้นประวัติการซื้อจากเบอร์โทร (CR-014) ปิดช่องว่างโดเมน Customer · เพิ่ม unit test 14 เคส · LICENSE (MIT) |
| v1.0.0 | 2026-08-25 | FR-001~014 + NFR ครบ · Dashboard เชิงวิเคราะห์ (CR-013) · deploy จริงบน Render |

> **ทำไมมี 2 เวอร์ชันในวันเดียว:** tag `v1.0.0` ถูกสร้างก่อน แล้วการตรวจขอบเขตเทียบกับ
> 6 โดเมนของโจทย์พบว่าโดเมน Customer ยังไม่มีความสามารถใช้งาน (CR-014) จึงเพิ่ม FR-015
> เข้ามา · การแก้ tag เดิมให้ชี้ commit ใหม่จะทำให้ tag ไม่ตรงกับสิ่งที่เคยเผยแพร่ไปแล้ว
> จึงออกเวอร์ชันใหม่ตามหลัก semver แทน (เพิ่มความสามารถแบบ backward-compatible = minor)

> ก่อนหน้า v1.0.0 ไม่ได้ tag ไว้ เพราะยังพัฒนาต่อเนื่องบน `main` โดยไม่มีจุดส่งมอบที่ชัดเจน —
> ดูการเปลี่ยนแปลงย้อนหลังได้จาก [Change Log ของ requirement (CR-001 ถึง CR-013)](01-Requirements-Package.md)
> และประวัติ commit
