const { chromium } = require('playwright')
const path = require('path')

const OUT_DIR = process.argv[2]
const BASE = process.argv[3] || 'https://sme-inventory-frontend.onrender.com'
const API = 'https://sme-inventory-api.onrender.com'

async function shot(page, name, opts = {}) {
  await page.screenshot({ path: path.join(OUT_DIR, name), ...opts })
  console.log('  saved', name)
}

// เปิดหน้าแล้วรอ "response ของ API ที่หน้านั้นต้องใช้" — เป็นสัญญาณเชิงบวกที่ใช้ได้ทุกหน้า
// ไม่ผูกกับโครงสร้าง DOM · รอบก่อนใช้ selector 'table tbody tr' แล้วค้าง เพราะหน้าคำขอสั่งซื้อ
// เรนเดอร์เป็นการ์ด ไม่ได้ใช้ <table> เลย
async function gotoAndWait(page, url, apiPath) {
  const waiting = page.waitForResponse(
    (r) => r.url().includes(apiPath) && r.status() === 200,
    { timeout: 45000 },
  )
  await page.goto(url, { waitUntil: 'commit' })
  await waiting
  await settle(page)
}

// รอให้ loading หายแบบนิ่ง + ให้ animation ของกราฟจบ
async function settle(page) {
  const deadline = Date.now() + 20000
  let stable = 0
  while (Date.now() < deadline) {
    const n = await page.locator('text=กำลังโหลด').count()
    if (n === 0) {
      if (++stable >= 3) break
    } else stable = 0
    await page.waitForTimeout(400)
  }
  await page.waitForTimeout(1800)
}

async function login(page, username, password) {
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
  await page.fill('form input:not([type="password"])', username)
  await page.fill('input[type="password"]', password)
  const waiting = page.waitForResponse(
    (r) => r.url().includes('/api/reports/summary') && r.status() === 200,
    { timeout: 45000 },
  )
  await page.click('button[type="submit"]')
  await waiting
  await page.waitForSelector('.recharts-surface', { timeout: 45000 })
  await settle(page)
}

async function logout(page) {
  const btn = page.locator('button', { hasText: 'ออกจากระบบ' })
  if ((await btn.count()) > 0) {
    await btn.first().click()
    await page.waitForTimeout(600)
  }
}

// เลื่อนไปที่การ์ด/หัวข้อที่ต้องการแล้วจับเฉพาะช่วงนั้น — dashboard ใหม่ยาวเกินหนึ่งจอ
async function shotSection(page, headingText, name) {
  // ใช้ scrollIntoView({block:'start'}) ไม่ใช่ scrollIntoViewIfNeeded — ตัวหลังไม่ขยับเลย
  // ถ้า element อยู่ในจออยู่แล้ว ทำให้ได้ภาพซ้ำกับช็อตก่อนหน้า (เจอจริง: 03c กับ 03d
  // ออกมาเป็นไฟล์เดียวกันเป๊ะ md5 ตรงกัน)
  await page.locator(`text=${headingText}`).first()
    .evaluate((e) => e.scrollIntoView({ block: 'start', behavior: 'instant' }))
  await page.waitForTimeout(1200)
  await shot(page, name)
}

// ดึง S/N จริงจาก API มาใช้ ไม่ hardcode — S/N เปลี่ยนทุกครั้งที่ reseed
async function pickSerials() {
  const res = await fetch(`${API}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'branch1', password: 'branch1234' }),
  })
  const { access_token } = await res.json()
  const h = { Authorization: `Bearer ${access_token}` }
  const sold = await (await fetch(`${API}/api/items?status=Sold&limit=5`, { headers: h })).json()
  const inStock = await (await fetch(`${API}/api/items?status=InStock&limit=5`, { headers: h })).json()
  return { sold: sold[0].serial_number, inStock: inStock[0].serial_number }
}

async function main() {
  const { sold, inStock } = await pickSerials()
  console.log(`ใช้ S/N จริง — ขายแล้ว: ${sold} · พร้อมขาย: ${inStock}\n`)

  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1280, height: 860 } })
  page.on('pageerror', (e) => console.log('  [pageerror]', e.message))

  // 1. หน้าสาธารณะ เช็คประกัน (ผลสำเร็จ)
  await page.goto(BASE, { waitUntil: 'networkidle' })
  await page.fill('input[placeholder*="SN"]', sold)
  await page.click('button[type="submit"]')
  await page.waitForTimeout(1200)
  await shot(page, '01-public-warranty-check.png')

  // 1b. หน้าสาธารณะ — พิมพ์ S/N ผิดรูปแบบ เพื่อแสดงข้อความ error ที่บอกรูปแบบที่ถูกต้อง
  // (NFR-USE-01 — เดิมบอกแค่ "ไม่พบข้อมูล" ซึ่งเป็นทางตันสำหรับผู้ใช้ที่ไม่มีคนสอน)
  await page.goto(BASE, { waitUntil: 'networkidle' })
  await page.fill('input[placeholder*="SN"]', 'SN-0001234')
  await page.click('button[type="submit"]')
  await page.waitForTimeout(1500)
  await shot(page, '01b-public-warranty-format-help.png')

  // 2. หน้าเข้าสู่ระบบ
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
  await shot(page, '02-login.png')

  // 3. สำนักงานใหญ่ — KPI + กราฟยอดขายรายวัน (CR-013)
  await login(page, 'admin', 'admin1234')
  await shot(page, '03-admin-dashboard-kpi.png')

  // 3b/3c/3d — dashboard ใหม่ยาวกว่าหนึ่งจอ แยกจับเป็นช่วง
  await shotSection(page, 'สินค้าขายดี 10 อันดับ', '03b-admin-dashboard-charts.png')
  await shotSection(page, 'อายุของสินค้าที่ยังค้างสต็อก', '03c-admin-dashboard-aging.png')
  await shotSection(page, 'รายการเสี่ยงของขาด', '03d-admin-stockout-risk.png')

  // 4. รายละเอียดสินค้า (คลิกแถวในตารางสต็อก)
  await page.locator('table tbody tr').first().click()
  await page.waitForTimeout(1800)
  await shot(page, '10-product-detail-modal.png')
  await page.keyboard.press('Escape')
  await page.waitForTimeout(500)

  // 5. สินค้า + รูป (FR-013)
  await gotoAndWait(page, `${BASE}/admin/products`, '/api/products')
  const imgBtn = page.locator('button', { hasText: '/5 รูป' }).first()
  if ((await imgBtn.count()) > 0) {
    await imgBtn.click()
    await page.waitForTimeout(1200)
  }
  await shot(page, '04-admin-products-images.png')

  // 6. คำขอสั่งซื้อรออนุมัติ
  await gotoAndWait(page, `${BASE}/admin/requests`, '/api/purchase-requests')
  await shot(page, '05-admin-purchase-requests-pending.png')

  // 7. Audit log
  await gotoAndWait(page, `${BASE}/admin/audit-log`, '/api/audit-log')
  await shot(page, '06-admin-audit-log.png')

  await logout(page)

  // 8. หน้าสาขา — KPI + กราฟ (scope เฉพาะสาขาตัวเอง)
  await login(page, 'branch1', 'branch1234')
  await shot(page, '07-branch-dashboard-kpi.png')
  await shotSection(page, 'รายการเสี่ยงของขาด', '07b-branch-stockout-restock.png')

  // 9. บันทึกขาย — ค้น S/N ที่พร้อมขาย
  await gotoAndWait(page, `${BASE}/branch/sell`, '/api/items')
  await page.fill('form input', inStock)
  await page.click('button:has-text("ค้นหา")')
  await page.waitForTimeout(1200)
  await shot(page, '08-branch-record-sale-lookup.png')

  // 9b. กรอกผู้ซื้อแล้วยืนยัน — ขั้นนี้เขียนข้อมูลจริง 1 รายการ (ตั้งใจ เป็นหลักฐาน flow)
  const inputs = page.locator('form input')
  await inputs.nth(0).fill('สมชาย ทดสอบระบบ')
  await inputs.nth(1).fill('0899999999')
  await page.click('button:has-text("ยืนยันการขาย")')
  await page.waitForTimeout(1800)
  await shot(page, '08b-branch-record-sale-success.png')

  // 10. เคสผิดพลาดฝั่งสาขา — S/N ที่ไม่มีในสาขานี้
  // (คนละหน้ากับข้อความ error ที่แก้ตาม NFR-USE-01 ซึ่งอยู่หน้าเช็คประกันสาธารณะ — ดู 01b)
  await gotoAndWait(page, `${BASE}/branch/sell`, '/api/items')
  await page.fill('form input', 'SN-DOES-NOT-EXIST-999')
  await page.click('button:has-text("ค้นหา")')
  await page.waitForTimeout(1200)
  await shot(page, '09-branch-record-sale-not-found-error.png')

  await browser.close()
  console.log('\nเสร็จ')
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
