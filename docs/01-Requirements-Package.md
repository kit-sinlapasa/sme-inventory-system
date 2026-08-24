# Requirement Package — SME Inventory & Order Management
## ระบบจัดการสต็อกและตรวจสอบการรับประกันอะไหล่คอมพิวเตอร์ (ชื่อชั่วคราว)

> ✅ **สถานะ: Baseline v1.0** — ทีมยืนยันแล้วเมื่อ 2026-08-24 (ตาม Deck 02 สไลด์ 53) การเปลี่ยนแปลงจากนี้ต้องผ่าน Change Request Process (Deck 02 สไลด์ 54) และบันทึกไว้ใน Change Log ท้ายเอกสาร ไม่แก้เงียบ ๆ

## Change Log

| Version | วันที่ | การเปลี่ยนแปลง |
|---|---|---|
| v1.0 | 2026-08-24 | Baseline แรก — ทีมยืนยัน Problem Statement, Stakeholder List, FR 12, NFR 6, User Story 8 + AC, Priority, RTM เริ่มต้น |
| v1.1 | 2026-08-24 | CR-001, CR-002 อนุมัติ (ดูรายละเอียดด้านล่าง) — ⚠️ ทีมสั่ง "ทำเลย" โดยไม่ระบุรายละเอียดเอง AI จึงตัดสินใจแทนตาม default ที่สมเหตุสมผล **ทีมควร double-check ทั้ง 2 CR นี้อีกครั้งก่อนส่งงานจริง** |
| v1.2 | 2026-08-24 | **CR-003 ถูกสร้างขึ้นจากสมมติฐานผิด** (เข้าใจว่าเหลือเวลา 1 สัปดาห์ ทีมยังไม่ยืนยัน) → ทีมแจ้งจริงว่าเหลือ **4 สัปดาห์** → CR-004 แก้ไข/คืน scope บางส่วน (ดูด้านล่าง) |
| v1.3 | 2026-08-24 | ทีมแจ้งแก้ไขอีกครั้ง — เวลาจริงคือ **8 สัปดาห์** → CR-005 คืน scope เพิ่มเติม (ดูด้านล่าง) |

### CR-001: เพิ่ม NFR-PRIV-01 (data retention สำหรับข้อมูลผู้ซื้อ)
- **เหตุผล:** พบช่องว่างระหว่างทวน — FR-004 เก็บชื่อ/เบอร์โทรผู้ซื้อ แต่ไม่มีข้อกำหนดเรื่องเก็บนานแค่ไหน/ใครดูได้/ลบเมื่อไหร่ (Deck 02 สไลด์ 18: Collect→Use→Store→Share→**Delete** — ขาด Delete)
- **Impact:** เพิ่ม NFR ใหม่ 1 ข้อ · กระทบ ER Model (ต้องมี field วันหมดอายุการเก็บข้อมูล/สถานะ anonymize ในตาราง Sale) · ไม่กระทบ FR ที่มีอยู่
- **ตัดสินใจ:** Approved — ตั้งค่า default 3 ปีหลังหมดประกัน (อิงตามระยะเวลาที่ข้อมูลยังมีประโยชน์ทางธุรกิจ) **ทีมควรยืนยันตัวเลขนี้กับนโยบายจริงของร้าน**

### CR-002: ชี้แจง FR-012 ให้ reorder point เป็นระดับ "ต่อ SKU ต่อสาขา" แทน "ต่อ SKU" อย่างเดียว
- **เหตุผล:** FR-003 กำหนดให้แสดงยอดคงเหลือแยกตามสาขาอยู่แล้ว การตั้ง reorder point ต่อสาขาจึงไม่เพิ่ม complexity ของ data model และสมเหตุสมผลกว่าทางธุรกิจ (แต่ละสาขามีความต้องการต่างกัน)
- **Impact:** แก้ถ้อยคำ FR-012 และ US-08 · reorder_point ย้ายไปอยู่ในตาราง Branch_SKU แทนตาราง SKU (บันทึกไว้สำหรับขั้น ER Model)
- **ตัดสินใจ:** Approved

---

## 1. Problem Statement

ร้านค้า SME ที่จำหน่ายอะไหล่คอมพิวเตอร์ (RAM, Mainboard, CPU ฯลฯ) ผ่านหลายสาขา มีปัญหาในการติดตามสต็อกที่สินค้าแต่ละชิ้นมีหมายเลขซีเรียล (S/N) และระยะเวลารับประกันเป็นของตัวเอง ทำให้:

- **HQ** ไม่สามารถทราบได้แบบเรียลไทม์ว่าใครซื้อสินค้าชิ้นไหน เมื่อไหร่ ที่สาขาใด — ขาด audit trail ที่ตรวจสอบย้อนกลับได้
- **สาขา** ไม่มีช่องทางตรวจสอบสต็อกกลางเพื่อวางแผนสั่งซื้อ (PR/PO) ทำให้สินค้าขาดสต็อกโดยไม่รู้ตัวหรือสั่งซื้อผิดพลาด
- **ลูกค้าปลายทาง** ไม่มีช่องทางตรวจสอบสถานะการรับประกันด้วยตนเอง ต้องติดต่อร้านทุกครั้ง
- ไม่มีการควบคุมสิทธิ์ที่ชัดเจนระหว่างสาขากับ HQ — เสี่ยงต่อการแก้ไขสต็อกหลักโดยไม่ได้รับอนุญาต

**ระบบนี้จะช่วย** ให้ HQ ควบคุมสต็อกกลางแบบรายชิ้น (serialized inventory), ให้สาขาดูสต็อกและสร้างคำขอสั่งซื้อได้โดยไม่แก้ไขข้อมูลหลัก, และให้ลูกค้าเช็คสถานะประกันได้เองแบบสาธารณะโดยไม่เปิดเผยข้อมูลส่วนบุคคล

### Assumptions
- "Hardware" = อะไหล่คอมพิวเตอร์ (RAM, Mainboard, CPU ฯลฯ) ไม่ใช่เครื่องมือช่าง
- ไม่มีตะกร้าสินค้า/ชำระเงิน/จัดส่งออนไลน์ — อ้างอิง ihavecpu.com เฉพาะด้าน**หน้าตาและการจัดหมวดหมู่สินค้า**เท่านั้น
- มี 1 สำนักงานใหญ่ (HQ) และหลายสาขา (Branch) — สมมติ ≥2 สาขาเพื่อทดสอบ concurrency
- การขายเกิดขึ้นหน้าร้าน พนักงานเป็นผู้บันทึกรายการขายเข้าระบบ ไม่ใช่ลูกค้ากรอกเอง

### Constraints
- ต้องพัฒนาและส่งงานภายในกรอบเวลาของวิชา NC221 (ดู [COURSE-NOTES.md](../COURSE-NOTES.md) สัปดาห์ 3–11)
- ต้อง upload ขึ้น GitHub และใช้ Git workflow ตามที่วิชากำหนด (Deck 04)
- ต้องมี AI Usage Disclosure ครบทุกจุดที่ใช้ AI ช่วยงาน (รวมถึงเอกสารฉบับนี้)

---

## 2. Stakeholder List

| กลุ่ม | Stakeholder | Needs | Responsibility |
|---|---|---|---|
| **Primary** | HQ Admin / Inventory Manager | ควบคุมสต็อกกลางให้ถูกต้อง แม่นยำ ตรวจสอบย้อนกลับได้ | เพิ่ม/แก้ไขสินค้า, รับสินค้าเข้าสต็อก, อนุมัติ PR→PO |
| **Primary** | พนักงานสาขา (Branch Staff) | รู้สต็อกที่มีจริง ไม่ให้ของขาดจนขายไม่ได้ | บันทึกการขาย, ดูสต็อก (อ่านอย่างเดียว), สร้าง PR |
| **Primary** | ลูกค้าปลายทาง (End Customer) | ตรวจสอบสถานะประกันได้เองโดยไม่ต้องโทรถามร้าน | กรอก S/N เพื่อเช็คสถานะ (ไม่ login) |
| **Secondary** | พนักงานขาย ณ จุดขาย | บันทึกข้อมูลผู้ซื้อผูกกับ S/N ได้รวดเร็วตอนขาย | กรอกข้อมูลผู้ซื้อ + ยืนยันการขาย |
| **Secondary** | ทีมพัฒนา/QA (นักศึกษาในทีม) | requirement ชัดเจน ทดสอบได้ ไม่เปลี่ยนกลางทาง | พัฒนา ทดสอบ ดูแล repository |
| **Secondary** | ผู้ดูแลระบบ/Support | แก้ปัญหาระบบได้เร็วเมื่อเกิด incident | ดูแล deployment, log, สิทธิ์ผู้ใช้ |
| **External** | อาจารย์ผู้สอน/ผู้ประเมิน | ตรวจสอบหลักฐานทางวิศวกรรมได้ครบตาม rubric | ประเมินผลงานตาม 8 หมวด (ดู Deck 05 rubric) |

---

## 3. Functional Requirements (FR) — 12 ข้อ

| ID | Requirement (เขียนให้ทดสอบได้) | Actor หลัก | Priority | มาจาก |
|---|---|---|---|---|
| **FR-001** | ระบบต้องให้ Admin เพิ่ม/แก้ไข/ระงับข้อมูลสินค้า (SKU) โดยระบุ หมวดหมู่ (RAM/Mainboard/CPU ฯลฯ), ยี่ห้อ, รุ่น, สเปก, และระยะเวลารับประกัน (หน่วยเดือน) | HQ Admin | **Must** | P3, P11 |
| **FR-002** | ระบบต้องรับสินค้าเข้าสต็อกเป็น**รายชิ้นพร้อม S/N** โดย S/N ต้องไม่ซ้ำกันทั้งระบบ และผูกกับ SKU + สาขาที่รับเข้า | HQ Admin | **Must** | P2, P3 |
| **FR-003** | ระบบต้องแสดงยอดคงเหลือแบบเรียลไทม์ แยกตาม SKU และตามสาขา/คลัง | ทุก role | **Must** | P2, P8 |
| **FR-004** | ระบบต้องบันทึกการขาย/จ่ายออกสินค้า โดยผูก **S/N ↔ ผู้ซื้อ ↔ วันที่ ↔ สาขาที่ขาย** (5W2H) | Branch Staff | **Must** | P1 |
| **FR-005** | ระบบต้องคำนวณวันหมดประกันของแต่ละ S/N อัตโนมัติจาก *วันที่ขาย + ระยะประกันของ SKU* | ระบบ (automated) | **Must** | P2 |
| **FR-006** | เว็บสาธารณะต้องให้ผู้ใช้กรอก S/N เพื่อตรวจสอบสถานะการรับประกันได้ **โดยไม่ต้อง login** และไม่แสดงข้อมูลส่วนบุคคลของผู้ซื้อ | End Customer | **Must** | P7 |
| **FR-007** | ระบบต้องมี Backoffice ที่เข้าใช้ด้วย username/password พร้อมกำหนดสิทธิ์ตาม role (Admin / Branch Staff) | HQ Admin, Branch Staff | **Must** | โน้ตเดิม FR#2 |
| **FR-008** | เว็บ B2B ต้องให้พนักงานสาขา login แล้วดูรายการสินค้าและจำนวนคงเหลือของสต็อกกลางได้ **แบบอ่านอย่างเดียว** | Branch Staff | **Must** | P8 |
| **FR-009** | สาขาต้องสร้างคำขอสั่งซื้อ (PR) ได้ และระบบต้องแจ้งเตือน HQ เมื่อมี PR ใหม่เข้ามา | Branch Staff | **Must** *(คืนเต็มโดย CR-005)* | P8 |
| **FR-010** | HQ ต้องตรวจสอบ/อนุมัติ/ปฏิเสธ PR และแปลงเป็น PO ได้ พร้อมบันทึกผู้อนุมัติ วันที่ และเหตุผล (ถ้าปฏิเสธ) | HQ Admin | **Must** *(คืนเต็มโดย CR-005)* | P8 |
| **FR-011** | ระบบต้องบันทึก audit log ทุกการเปลี่ยนแปลงสต็อกและสถานะ PR/PO: ใคร/ทำอะไร/เมื่อไหร่/ที่ไหน/ค่าก่อน-หลัง | ระบบ (automated) | **Must** | P1 (5W2H) |
| **FR-012** | ระบบต้องแจ้งเตือน Admin เมื่อยอดคงเหลือของ SKU ใดในสาขาใดต่ำกว่าจุดสั่งซื้อ (reorder point) ที่กำหนดไว้**ต่อ SKU ต่อสาขา** *(แก้ตาม CR-002)* | HQ Admin | **Should** *(คืนโดย CR-005)* | โน้ตหน้า 2 (alert สินค้าใกล้หมด) |

> 📌 **หมายเหตุ:** P9 (เป็นเว็บ), P10 (concept แบบ ihavecpu) และ P5 (อัพโหลด GitHub) **ไม่ใช่ FR** — P9/P10 เป็น solution decision (บันทึกไว้ใน NFR-USE-01 และจะกลายเป็น ADR ในขั้น Architecture) ส่วน P5 เป็นข้อกำหนดของวิชา ไม่ใช่ requirement ของระบบ จึงไม่ใส่ใน SRS (ดู Deck 02 สไลด์ 22 — anti-pattern "Implementation-biased")

---

## 4. Non-Functional Requirements (NFR) — 6 ข้อ

| ID | Requirement (มี metric + threshold + context) | หมวด | Priority | วิธีพิสูจน์ |
|---|---|---|---|---|
| **NFR-PERF-01** | หน้าเช็คประกันสาธารณะ (FR-006) ต้องตอบกลับภายใน **2 วินาทีที่ P95** เมื่อมีผู้ใช้เข้าพร้อมกัน **200 คน** *(คืน spec เต็มโดย CR-005)* | ประสิทธิภาพ | Should | Load test |
| **NFR-SEC-01** | เว็บสาธารณะ (FR-006) ต้องไม่เปิดเผยชื่อ เบอร์โทร หรือที่อยู่ของผู้ซื้อ — แสดงได้เฉพาะรุ่นสินค้าและสถานะ/วันหมดประกัน | ความปลอดภัย | **Must** | Security review + test |
| **NFR-SEC-02** | Role Branch Staff ต้องไม่มีสิทธิ์เพิ่ม/แก้ไข/ลบสินค้าหรือจำนวนสต็อกในสต็อกหลัก — **ต้องบังคับใช้ที่ server ทุก endpoint** ไม่ใช่แค่ซ่อนปุ่มใน UI | ความปลอดภัย | **Must** | Automated test: ยิง API ตรงด้วย token สาขา → ต้องได้ 403 |
| **NFR-REL-01** | การตัดสต็อก/จ่าย S/N ต้องเป็น **atomic operation** — S/N หนึ่งชิ้นต้องจ่ายออกได้เพียงครั้งเดียว แม้มี concurrent request เข้ามาพร้อมกัน | ความน่าเชื่อถือ | **Must** | Concurrency test |
| **NFR-USE-01** | หน้าจอทั้งหมดใช้โทนสีขาว-ฟ้าสะอาดตา จัดหมวดหมู่สินค้าตามประเภทอะไหล่ (อ้างอิง ihavecpu.com) และผู้ใช้ใหม่ต้องทำ task ค้นหา/เช็คประกันสำเร็จ **≥90% ภายใน 60 วินาที** โดยไม่ต้องมีคนสอน | ความใช้งานง่าย | Should | Task-based user test |
| **NFR-MAINT-01** | Audit log (FR-011) ต้องเก็บข้อมูลย้อนหลังได้อย่างน้อย **1 ปี** และค้นหาตาม S/N ได้ภายใน **3 วินาที** | การบำรุงรักษา | **Should** *(ยกจาก Could โดย CR-005 — low effort, ผูกกับ FR-011 ที่เป็น Must อยู่แล้ว)* | `GET /api/audit-log` ใช้ index บน `entity_id`/`occurred_at` แล้ว — ยังไม่มี load test วัดเวลาจริงที่ scale ใหญ่ |
| **NFR-PRIV-01** *(เพิ่มโดย CR-001)* | ข้อมูลผู้ซื้อ (ชื่อ/เบอร์โทร ใน FR-004) ต้องถูกเก็บไม่เกิน **3 ปีหลังวันหมดประกัน** หลังจากนั้นต้อง anonymize หรือลบ · เข้าถึงได้เฉพาะ role Admin/Branch Staff ที่เกี่ยวข้องกับการขายนั้น | ความเป็นส่วนตัว | **Must** | Data retention job test + access log review |

---

## 5. User Stories + Acceptance Criteria (8 เรื่อง)

### US-01 — เช็คประกัน (End Customer) · Priority: Must · เชื่อมกับ FR-005, FR-006
**As a** เจ้าของอุปกรณ์ **I want** กรอกหมายเลขซีเรียล (S/N) เพื่อตรวจสอบสถานะการรับประกัน **so that** ฉันรู้ว่าสินค้ายังอยู่ในประกันหรือไม่โดยไม่ต้องโทรถามร้าน

- **Given** ผู้ใช้เปิดหน้าเว็บสาธารณะ (ไม่ login) **When** กรอก S/N ที่ถูกต้องและมีในระบบ **Then** ระบบแสดงรุ่นสินค้า วันเริ่มประกัน วันหมดประกัน และสถานะ (อยู่ในประกัน/หมดประกัน)
- **Given** ผู้ใช้กรอก S/N ที่ไม่มีในระบบ **When** กดค้นหา **Then** ระบบแสดง "ไม่พบข้อมูล กรุณาตรวจสอบ S/N อีกครั้ง"
- **Given** S/N ถูกต้อง **When** ระบบแสดงผล **Then** ต้องไม่แสดงชื่อ เบอร์โทร หรือที่อยู่ของผู้ซื้อ

### US-02 — เพิ่มสินค้าใหม่ (HQ Admin) · Priority: Must · เชื่อมกับ FR-001
**As a** Admin สำนักงานใหญ่ **I want** เพิ่มสินค้าประเภทใหม่ (SKU) พร้อมกำหนดระยะเวลารับประกัน **so that** ระบบคำนวณวันหมดประกันให้อัตโนมัติเมื่อมีการขาย

- **Given** Admin login เข้า Backoffice **When** กรอกข้อมูล SKU ครบ (ชื่อ/หมวดหมู่/ยี่ห้อ/รุ่น/ระยะประกัน) แล้วกดบันทึก **Then** ระบบสร้าง SKU ใหม่และแสดงในรายการสินค้า
- **Given** Admin กรอกระยะประกันเป็นค่าติดลบหรือไม่ใช่ตัวเลข **When** กดบันทึก **Then** ระบบแสดง error และไม่บันทึกข้อมูล

### US-03 — รับสินค้าเข้าสต็อก (HQ Admin) · Priority: Must · เชื่อมกับ FR-002
**As a** Admin คลังสินค้า **I want** รับสินค้าเข้าสต็อกพร้อมกรอก S/N ของแต่ละชิ้น **so that** ระบบมีข้อมูลรายชิ้นครบถ้วนสำหรับติดตามในอนาคต

- **Given** Admin เลือก SKU ที่มีอยู่ **When** กรอก S/N ที่ยังไม่เคยมีในระบบแล้วกดรับเข้า **Then** ระบบเพิ่ม item ใหม่สถานะ "In Stock" ผูกกับสาขาที่รับเข้า
- **Given** Admin กรอก S/N ที่ซ้ำกับที่มีอยู่แล้ว **When** กดรับเข้า **Then** ระบบแสดง error "S/N นี้มีอยู่แล้วในระบบ" และไม่บันทึกซ้ำ

### US-04 — บันทึกการขาย (Branch Staff) · Priority: Must · เชื่อมกับ FR-004, FR-005, NFR-REL-01
**As a** พนักงานสาขา **I want** บันทึกการขายสินค้าโดยผูก S/N กับข้อมูลผู้ซื้อ **so that** ระบบคำนวณวันหมดประกันและตรวจสอบย้อนกลับได้ว่าใครซื้อเมื่อไหร่

- **Given** สินค้า S/N นั้นมีสถานะ "In Stock" ที่สาขาของพนักงาน **When** พนักงานกรอกข้อมูลผู้ซื้อและกดยืนยันการขาย **Then** ระบบเปลี่ยนสถานะเป็น "Sold" บันทึกวันที่/ผู้ซื้อ/สาขา และคำนวณวันหมดประกันอัตโนมัติ
- **Given** สินค้า S/N นั้นถูกขายไปแล้ว **When** มีการพยายามขายซ้ำด้วย S/N เดียวกันพร้อมกัน (concurrent request) **Then** ระบบอนุญาตให้สำเร็จได้เพียงครั้งเดียว รายการที่สองต้องได้รับข้อความ "สินค้านี้ถูกขายไปแล้ว"

### US-05 — ดูสต็อกกลาง (Branch Staff) · Priority: Must · เชื่อมกับ FR-003, FR-008, NFR-SEC-02
**As a** พนักงานสาขา **I want** ดูจำนวนสินค้าคงเหลือของสต็อกกลางแบบเรียลไทม์ **so that** ฉันรู้ว่าควรสั่งซื้อสินค้าใดเพิ่มก่อนขาดสต็อก

- **Given** พนักงานสาขา login เข้าเว็บ B2B **When** เปิดหน้ารายการสินค้า **Then** ระบบแสดงยอดคงเหลือของแต่ละ SKU ที่เป็นข้อมูลล่าสุด
- **Given** พนักงานสาขาพยายามเรียก API แก้ไขจำนวนสต็อกโดยตรง **When** request ถูกส่งไปยัง server **Then** ระบบต้องปฏิเสธด้วย HTTP 403

### US-06 — สร้างคำขอสั่งซื้อ (Branch Staff) · Priority: Should · เชื่อมกับ FR-009
**As a** พนักงานสาขา **I want** สร้างคำขอสั่งซื้อ (PR) เมื่อสินค้าใกล้หมด **so that** สาขาของฉันมีสินค้าเพียงพอต่อการขาย

- **Given** พนักงานสาขาเลือก SKU และระบุจำนวนที่ต้องการ **When** กดส่งคำขอ **Then** ระบบสร้าง PR สถานะ "Pending" และแจ้งเตือน HQ Admin
- **Given** PR ถูกสร้างโดยไม่ระบุจำนวน หรือระบุเป็น 0/ค่าติดลบ **When** กดส่ง **Then** ระบบแสดง error และไม่สร้าง PR

### US-07 — อนุมัติ PR/PO (HQ Admin) · Priority: Should · เชื่อมกับ FR-010
**As a** Admin สำนักงานใหญ่ **I want** ตรวจสอบและอนุมัติ/ปฏิเสธ PR ที่สาขาส่งมา **so that** ฉันควบคุมการกระจายสินค้าระหว่างสาขาได้อย่างเหมาะสม

- **Given** มี PR สถานะ "Pending" **When** Admin กดอนุมัติ **Then** ระบบเปลี่ยนสถานะเป็น "Approved" สร้าง PO ที่เชื่อมโยงกับ PR นั้น และบันทึกผู้อนุมัติ+วันเวลา
- **Given** Admin กดปฏิเสธ PR **When** ระบบร้องขอเหตุผล **Then** Admin ต้องกรอกเหตุผลก่อนระบบจะเปลี่ยนสถานะเป็น "Rejected" ได้

### US-08 — แจ้งเตือนสินค้าใกล้หมด (HQ Admin) · Priority: Could · เชื่อมกับ FR-012
**As a** Admin คลังสินค้า **I want** ได้รับการแจ้งเตือนเมื่อสินค้าคงเหลือ**ของสาขาใดสาขาหนึ่ง**ต่ำกว่าจุดสั่งซื้อ **so that** ฉันวางแผนสั่งซื้อล่วงหน้าให้สาขานั้นก่อนสินค้าหมดสต็อกจริง *(ปรับตาม CR-002)*

- **Given** SKU หนึ่ง**ที่สาขาหนึ่ง**ตั้งค่า reorder point ไว้ที่ N ชิ้น **When** ยอดคงเหลือของ SKU นั้น**ในสาขานั้น**ลดลงต่ำกว่า N **Then** ระบบสร้างการแจ้งเตือนให้ Admin เห็นในหน้า Dashboard ภายใน 5 นาที พร้อมระบุชื่อสาขา
- **Given** SKU-สาขานั้นยังไม่ได้ตั้งค่า reorder point เฉพาะ **When** ยอดคงเหลือลดลงถึง 0 **Then** ระบบแจ้งเตือนด้วยค่าเริ่มต้น (default threshold) ของระบบ

---

## 6. Requirement Traceability Matrix (RTM) — เริ่มต้น

> คอลัมน์ Design / Code / Test ยังว่างเพราะยังไม่เข้าสู่ขั้น Architecture (สัปดาห์ 5) — สร้างโครง RTM ไว้ตั้งแต่ตอนนี้เพื่อให้ trace ได้ทันทีที่แต่ละขั้นเสร็จ ตาม Deck 02 สไลด์ 49 (Traceability ต้องทำตลอด lifecycle ไม่ใช่ย้อนทำตอนท้าย)

| Req ID | Source (P#) | User Story | Design | Test Case | Status |
|---|---|---|---|---|---|
| FR-001 | P3, P11 | US-02 | ER: `PRODUCT` · API: `POST/PUT/DELETE /api/products` | `test_products.py` (5 tests) | ✅ Implemented + Tested |
| FR-002 | P2, P3 | US-03 | ER: `ITEM` · API: `POST /api/items` | `test_items_and_stock.py` (2 tests) | ✅ Implemented + Tested |
| FR-003 | P2, P8 | US-05 | API: `GET /api/stock` | `test_items_and_stock.py` (2 tests) | ✅ Implemented + Tested |
| FR-004 | P1 | US-04 | ER: `SALE` · API: `POST /api/sales` · ADR-002 | `test_sale_race_condition.py` (4 tests) | ✅ Implemented + Tested |
| FR-005 | P2 | US-01, US-04 | ER: `SALE.warranty_expires_at` (computed field) | `test_public_warranty.py` | ✅ Implemented + Tested |
| FR-006 | P7 | US-01 | API: `GET /api/public/warranty/{serial}` | `test_public_warranty.py` (3 tests) | ✅ Implemented + Tested |
| FR-007 | โน้ตเดิม FR#2 | — (cross-cutting) | API: `POST /api/auth/login` | ครอบคลุมทางอ้อมทุก test ที่ login | ✅ Implemented + Tested |
| FR-008 | P8 | US-05 | API: `GET /api/products`, `GET /api/stock` (role=Branch) | `test_items_and_stock.py::test_branch_staff_only_sees_own_branch_stock` | ✅ Implemented + Tested |
| FR-009 | P8 | US-06 | ER: `PURCHASE_REQUEST` · API: `POST /api/purchase-requests` | `test_purchase_requests.py` (4 tests) | ✅ Implemented + Tested |
| FR-010 | P8 | US-07 | ER: `PURCHASE_ORDER` · API: `POST .../approve`, `.../reject` (conditional-update pattern เดียวกับ ADR-002) | `test_purchase_requests.py` (4 tests รวม double-approve) | ✅ Implemented + Tested |
| FR-011 | P1 | — (cross-cutting) | ER: `AUDIT_LOG` + `services/audit.py` เรียกจากทุก mutating endpoint · API: `GET /api/audit-log` | `test_audit_log.py` (3 tests) | ✅ Implemented + Tested — **ยกเว้น**: FR-009 "แจ้งเตือน HQ" ยังเป็นแค่ query ผ่าน `?status=Pending` ไม่มี push/email จริง |
| FR-012 | โน้ตหน้า 2 | US-08 | ER: `BRANCH_SKU.reorder_point` · API: `GET/PUT /api/branch-sku/{branch_id}/{sku_id}` | `test_branch_sku.py` (4 tests) | 🟡 ตั้งค่า+แสดงผลทำแล้ว **แต่ยังไม่มีกลไกแจ้งเตือน (alert) จริง** |
| NFR-PERF-01 | — | US-01 | Quality Attribute Scenario #2 | ยังไม่ทำ load test | 🏗️ Design Complete (สัปดาห์ 7) |
| NFR-SEC-01 | — | US-01 | API response schema (ไม่มี field buyer) · STRIDE-I | `test_public_warranty.py::test_warranty_check_valid_serial_returns_status_without_buyer_info` | ✅ Implemented + Tested |
| NFR-SEC-02 | P8 | US-05 | Middleware role-check ทุก endpoint · STRIDE-T | 4 test ยืนยัน 403 (products, branch_sku, sales, stock) | ✅ Implemented + Tested |
| NFR-REL-01 | ความท้าทายโครงการ | US-04 | ADR-002 · Quality Attribute Scenario #1 | `test_sale_race_condition.py::test_only_one_concurrent_sale_succeeds` (10 concurrent thread) | ✅ Implemented + Tested |
| NFR-USE-01 | P4, P10 | — (cross-cutting) | หน้าเว็บครบ 3 persona (Public/Branch/Admin) โทนขาว-ฟ้าตาม Tailwind brand colors | ทดสอบด้วยมือผ่าน browser จริง (login→ขาย→PR→approve→audit log ครบ loop) ยังไม่มี usability test แบบมีผู้ใช้จริงมาวัด task success rate | 🟡 ใช้งานได้ครบ verify ด้วยตาเปล่าแล้ว **แต่ยังไม่มี formal usability test ตาม spec เดิม** |
| NFR-MAINT-01 | — | — (cross-cutting) | index บน `audit_logs.occurred_at`/`entity_id` มีแล้วใน DB แต่ยังไม่มี endpoint ให้ query | — | 🏗️ Design Complete |
| NFR-PRIV-01 | CR-001 | US-04 | ยังไม่ implement `POST /api/admin/purge-old-buyer-data` | — | 🏗️ Design Complete (สัปดาห์ 7 ตามแผน) |

**⚠️ Orphan check:** ทุก FR/NFR มี Source และเกือบทุกข้อมี User Story เชื่อม ยกเว้น FR-007, FR-011, NFR-USE-01, NFR-MAINT-01 ที่เป็น cross-cutting requirement (ไม่ผูกกับ story เดียว แต่ครอบทั้งระบบ) — เป็นเรื่องปกติตาม Deck 02 สไลด์ 64 (NFR และ cross-cutting constraints ต้องบริหารแยกจาก backlog ปกติ)

---

## ขั้นตอนถัดไปที่ทีมต้องทำ

1. ✅ ~~ทุกคนอ่านเอกสารนี้ทั้งฉบับ~~ — ทีมยืนยันแล้ว (baseline v1.0)
2. **ทวน CR-001 และ CR-002 อีกครั้งโดยละเอียด** — AI ตัดสินใจแทนทีมภายใต้คำสั่ง "ทำเลย" (ตัวเลข 3 ปีใน NFR-PRIV-01 เป็น default ที่ยังไม่ผ่านทีมจริง)
3. ✅ ยืนยันแล้ว — Backoffice + เว็บ B2B สาขา เป็น**ระบบเดียวกัน** (role-based) → จะบันทึกเป็น ADR-001 ในขั้น Architecture
4. ✅ ยืนยันแล้ว — Reorder point แยกตามสาขา และ**แจ้งเตือนอิสระต่อสาขา** แม้สาขาอื่นจะมีของเหลือเยอะ (CR-002 ถูกต้องแล้ว)
5. ✅ **แก้ไขแล้ว — เหลือเวลาจริง 4 สัปดาห์** (ดู CR-004) → แผนงานรายสัปดาห์อยู่ท้ายเอกสารนี้

## แผนงาน 8 สัปดาห์ (ฉบับละเอียด — ครบทุกรายการ ไม่ตัด scope)

| สัปดาห์ | โฟกัส | รายการงานย่อย | ผลลัพธ์ปลายสัปดาห์ |
|---|---|---|---|
| **1** | Architecture & Design | ADR-001 (ระบบเดียว role-based), ADR-002 (วิธีจัดการ concurrency — เลือกจริง เช่น DB unique constraint + transaction), ER Model เต็ม (รวม Branch_SKU + reorder_point ตาม CR-002), REST API spec ทุก endpoint, Wireframe 3 persona, STRIDE threat table | Architecture doc สมบูรณ์ พร้อมเข้ารายงานส่วนที่ 4 ได้ทันที |
| **2** | Repo & Skeleton | ตั้ง repo, branching strategy, coding standard + linter, CI pipeline เปล่า (build only), auth ระบบ (FR-007), โครง DB จริงตาม ER Model | Repo พร้อมใช้งาน ทุกคนมี branch/PR แรกแล้ว |
| **3** | Core Data Flow | FR-001 (SKU), FR-002 (รับเข้าสต็อกรายชิ้น), FR-003 (ดูสต็อกเรียลไทม์), FR-008 (มุมมองสาขา read-only) | CRUD หลักใช้งานได้ผ่าน UI จริง ไม่ใช่แค่ API |
| **4** | Transaction-Critical | FR-004 (บันทึกขาย), FR-005 (คำนวณประกัน) + **NFR-REL-01** (atomic stock — เขียน concurrency test คู่กับโค้ด) + **NFR-SEC-02** (role enforcement — เขียน 403 test คู่กับโค้ด) | ส่วนที่ยากที่สุดของโปรเจกต์เสร็จและมี test คุ้มกันแล้ว |
| **5** | Public + Audit + PR/PO | FR-006 (เช็คประกันสาธารณะ) + NFR-SEC-01 (privacy) + FR-011 (audit log) + FR-009/FR-010 (PR→PO flow เต็มรูปแบบ) | ครบทุก FR ที่เป็น Must/Should |
| **6** | Nice-to-have + CI/CD เต็มรูปแบบ | FR-012 (reorder alert) + ตั้ง CI/CD จริง (test+lint+quality gate อัตโนมัติ) + ขยาย unit/integration/acceptance test ให้ trace กลับ RTM ครบ | Feature ครบ 12/12 FR + CI/CD เขียว + RTM ไม่มี orphan |
| **7** | Hardening | Security pass (secrets scan, dependency/license check, ยืนยัน STRIDE mitigation ทุกข้อ) + NFR-PRIV-01 (manual purge function + test) + NFR-PERF-01 (load test 200 concurrent) + NFR-USE-01 (usability test) + bug fix buffer | Technical Evidence ครบทุกแถวตามตาราง Deck 05 |
| **8** | Report & Demo | เขียนรายงาน 11 ส่วนเต็ม + จบ AI Usage Log (verify ทุก entry จริง ไม่ใช่แค่ "โอเค") + Retrospective + เตรียม+ซ้อม slide/demo (happy path + edge case) | พร้อมส่งครบทุกข้อของ rubric |

> เวลานี้เพียงพอให้ทำ**ครบทุก FR/NFR ที่ร่างไว้ทั้งหมด** ไม่ต้องตัดอะไรออกถาวร — ยังคงเก็บ buffer ไว้ที่สัปดาห์ 7-8 สำหรับบั๊กที่คาดไม่ถึง ซึ่งเกิดขึ้นแน่นอนในโปรเจกต์จริง

### CR-003: ตัด Scope ฉุกเฉินเพราะเหลือเวลา 1 สัปดาห์
- **เหตุผล:** งานที่เหลือทั้งหมด (Architecture, ER Model, API, Code, Test, CI/CD, Report, Demo) ต้องเสร็จใน 7 วัน — scope เต็ม 12 FR + 6 NFR ไม่สามารถทำครบพร้อมหลักฐานทางวิศวกรรมที่มีคุณภาพได้ในเวลานี้
- **Impact:** FR-009, FR-010 เปลี่ยนจาก Should → **Deferred (ไม่ทำในรอบส่งนี้)** · FR-012 เปลี่ยนจาก Could → **Deferred** · NFR-PERF-01 (load test 200 users), NFR-MAINT-01, NFR-PRIV-01 (automated deletion job) ลดขอบเขตเหลือแค่ "ออกแบบ/บันทึกไว้ในเอกสาร" แทนการสร้างจริงที่ทำงานอัตโนมัติ
- **ตัดสินใจ:** Approved (ฉุกเฉิน) — รายการที่ Deferred ทั้งหมดต้องใส่ใน **Retrospective: "What we would improve"** ของรายงานฉบับสมบูรณ์ เพื่อแสดงว่าทีมตัดสินใจอย่างมีเหตุผล ไม่ใช่ลืมทำ

### CR-004: แก้ไข CR-003 — เหลือเวลาจริง 4 สัปดาห์ ไม่ใช่ 1 สัปดาห์
- **เหตุผล:** CR-003 สร้างจากสมมติฐานที่ยังไม่ยืนยัน (AI อ่าน "5. เหลือเวลากี่ 1 สัปดาห์" ผิด) ทีมแจ้งจริงว่าเหลือ **4 สัปดาห์** — เวลาเพียงพอสำหรับคืน scope บางส่วนที่ตัดไปเกินความจำเป็น
- **Impact:** คืน Priority บางรายการ (ดูตาราง FR ด้านล่าง — คอลัมน์ Priority อัปเดตแล้ว) NFR-PERF-01 กลับมาทำ load test จริง (ลดจาก 200 เหลือ ~50-100 concurrent เพื่อให้เหมาะกับเวลา) · NFR-PRIV-01 ทำเป็นฟังก์ชัน manual purge ที่ Admin กดเรียกได้ (มี evidence จริง ไม่ใช่แค่เอกสาร)
- **ตัดสินใจ:** Approved — แผนงาน 4 สัปดาห์อยู่ในสรุปท้ายเอกสารนี้และในแชท

### CR-005: แก้ไข CR-004 อีกครั้ง — เหลือเวลาจริง 8 สัปดาห์ ไม่ใช่ 4 สัปดาห์
- **เหตุผล:** ทีมแจ้งแก้ไขไทม์ไลน์เป็นครั้งที่ 3 (1 → 4 → 8 สัปดาห์) — เวลาที่เพิ่มขึ้นทำให้ FR ที่เคย defer/ลดขอบเขตกลับมาทำได้เต็มรูปแบบ
- **Impact:** FR-009, FR-010 (PR→PO flow) กลับเป็น **Must** เต็มรูปแบบ (ตรงกับ "business rules" ที่โจทย์ระบุเป็นความท้าทายหลัก ไม่ควรเป็นแค่ทางเลือกอีกต่อไปเมื่อมีเวลาพอ) · FR-012 กลับเป็น **Should** · NFR-PERF-01 คืนเป็น spec เดิม (200 concurrent users ที่ P95 2 วินาที) แทนที่จะลดเหลือ 50-100
- **ตัดสินใจ:** Approved — แผนงาน 8 สัปดาห์อยู่ในสรุปท้ายเอกสารนี้และในแชท
- ⚠️ **หมายเหตุถึงทีม:** ไทม์ไลน์เปลี่ยน 3 ครั้งในรอบเดียวกัน หากยังไม่แน่ใจ 100% แนะนำให้ยืนยันกับอาจารย์/ปฏิทินจริงอีกครั้งก่อนวางแผนต่อ เพราะทุกครั้งที่แก้ต้องเสียเวลา re-scope Architecture ที่กำลังจะเริ่ม
