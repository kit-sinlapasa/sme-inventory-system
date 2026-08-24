/**
 * CR-013 — สีของ dashboard เชิงวิเคราะห์
 *
 * ทุกชุดสีในไฟล์นี้ผ่าน scripts/validate_palette.js จริง ไม่ได้เลือกด้วยสายตา
 * ผลที่รันไว้บันทึกกำกับแต่ละชุด ถ้าจะแก้สีต้องรัน validator ซ้ำ ไม่ใช่แก้แล้วดูว่าสวย
 */

/**
 * สีประจำสาขา — ใช้กับกราฟเส้นยอดขายรายวัน (หลายเส้นทับกัน)
 *
 * ต้อง validate โหมด **all-pairs** ไม่ใช่ adjacent-pairs เหมือนกราฟแท่ง เพราะเส้นทุกเส้น
 * อยู่บนแกนเดียวกันและถูกเปรียบเทียบพร้อมกันหมด (ชุดสีหมวดหมู่เดิมของโปรเจกต์
 * ผ่านเฉพาะ adjacent-pairs จึงเอามาใช้ที่นี่ไม่ได้)
 *
 * ผลจริง: node scripts/validate_palette.js "#2a78d6,#D55E00,#009E73,#B0489A" --mode light --pairs all
 *   [PASS] Lightness band · [PASS] Chroma floor
 *   [PASS] CVD separation      worst all-pairs #B0489A↔#009E73 ΔE 9.3 (deutan)
 *   [PASS] Normal-vision floor worst all-pairs #B0489A↔#D55E00 ΔE 20.3
 *   [PASS] Contrast vs surface all 4 >= 3:1
 *
 * ⚠️ สีผูกกับ "ชื่อสาขา" ไม่ใช่ลำดับในกราฟ — ผู้ใช้กรองสาขาออกได้ ถ้าผูกกับ index
 * สาขาที่เหลือจะเปลี่ยนสีทุกครั้งที่กรอง ("color follows the entity, never its rank")
 */
const BRANCH_PALETTE = ['#2a78d6', '#D55E00', '#009E73', '#B0489A']
const OVERFLOW_BRANCH_COLOR = '#6b6b6b' // สาขาที่ 5 ขึ้นไป: เทากลาง ไม่สร้างสีใหม่เอง

/** คืนฟังก์ชันแปลงชื่อสาขา -> สี โดยล็อกลำดับจากรายชื่อสาขาที่เรียงคงที่ */
export function makeBranchColorScale(branchNames) {
  const order = [...new Set(branchNames)].sort((a, b) => a.localeCompare(b, 'th'))
  const map = Object.fromEntries(order.map((name, i) => [name, BRANCH_PALETTE[i] ?? OVERFLOW_BRANCH_COLOR]))
  return (name) => map[name] ?? OVERFLOW_BRANCH_COLOR
}

/**
 * เส้นประประจำสาขา — secondary encoding นอกเหนือจากสี
 * จำเป็นสำหรับกราฟเส้นที่พิมพ์ขาวดำหรือดูผ่านตาที่แยกสีไม่ได้
 */
export const BRANCH_DASH = [null, '6 3', '2 3', '10 3 2 3']

/**
 * ไล่เฉดเดียวสำหรับ "อายุสต็อก" — ข้อมูลมีลำดับ (ใหม่ -> เก่า) ต้องใช้ ramp ไม่ใช่สีคนละหมวด
 *
 * ผลจริง: node scripts/validate_palette.js "#84b4ea,#4f8dd8,#2467b6,#0f4478" --mode light --ordinal
 *   [PASS] Lightness monotone · [PASS] Adjacent ΔL · [PASS] Light-end contrast 2.11:1 · [PASS] Single hue (3°)
 */
export const AGING_RAMP = ['#84b4ea', '#4f8dd8', '#2467b6', '#0f4478']

/** สีเดียวสำหรับกราฟที่มีชุดข้อมูลเดียว — ไม่ต้องแยกตัวตน จึงไม่ควรใช้หลายสีให้เข้าใจผิด */
export const SINGLE_SERIES = '#2a78d6'

/** สีสถานะ (สงวนไว้ ห้ามเอาไปใช้เป็น "สีชุดที่ 4" ของข้อมูลทั่วไป) */
export const STATUS = { good: '#0a7d0a', warning: '#a3690f', critical: '#d03b3b' }

/**
 * พื้น gradient ของการ์ด KPI ใบเด่น — **เป็นการตกแต่ง ไม่ได้เข้ารหัสข้อมูล**
 *
 * ที่ใส่ gradient ตรงนี้ได้แต่ใส่ในกราฟไม่ได้ เพราะการ์ดใบนี้มีตัวเลขตัวเดียว
 * สีจึงไม่ได้สื่ออะไรเลยนอกจากดึงสายตา · ต่างจาก donut ในภาพอ้างอิงที่ไล่ gradient
 * ข้ามเซกเมนต์ ซึ่งทำให้สีเลิกบอกว่าเซกเมนต์ไหนคือหมวดไหน (ผิดหลัก
 * "color follows the entity") จึงไม่ลอกมา
 *
 * ทุกจุดของไล่สีเข้มพอให้ **ตัวหนังสือขาวทึบ** ผ่าน WCAG AA:
 *   #1f6fd0 4.95:1 · #4d57ca 5.95:1 · #7b3fc4 6.27:1 · #963cb0 5.88:1 · #b0399c 5.37:1
 *
 * ⚠️ ห้ามใช้ตัวหนังสือขาวแบบโปร่งแสงบนพื้นนี้ — วัดแล้วขาว 90% เหลือ 4.34:1 (ตก AA)
 * ถ้าต้องการลดน้ำหนักตัวอักษรให้ใช้ขนาด/ความหนาแทน อย่าใช้ opacity
 */
export const HERO_GRADIENT = 'linear-gradient(135deg, #1f6fd0 0%, #7b3fc4 55%, #b0399c 100%)'

/** สีพื้นอ่อนของไอคอนประจำการ์ดปกติ — ตกแต่งล้วน ไม่ได้แทนค่าข้อมูล */
export const TILE_ICON_BG = '#eaf2fd'

export const AXIS = { grid: '#eef0f2', tick: '#6b6b6b', label: '#0b0b0b' }

export const TOOLTIP_STYLE = {
  background: '#fcfcfb',
  border: '1px solid #e5e7eb',
  borderRadius: 8,
  color: '#0b0b0b',
  fontSize: 12,
}
