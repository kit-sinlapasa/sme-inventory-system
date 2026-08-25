// วัดสิ่งที่วัดได้โดยไม่ต้องมีผู้ใช้จริง — คนละเรื่องกับ task success rate ที่ต้องใช้คน
const { chromium } = require('playwright')
const BASE = 'https://sme-inventory-frontend.onrender.com'
const API = 'https://sme-inventory-api.onrender.com'
const R = []
// (c, n, d) = เงื่อนไข, ชื่อ, รายละเอียด — เรียงตามลำดับที่เรียกจริง
// รอบแรกเขียนสลับเป็น (n, c, d) ทำให้ชื่อ (string) ถูกใช้เป็นเงื่อนไข = truthy เสมอ
// ผลคือขึ้น ผ่าน ทุกข้อทั้งที่มีข้อที่ตกจริง — บั๊กชนิดเดียวกับ test ที่ fail ไม่ได้
const ok = (c, n, d = '') => { R.push([!!c, n, d]); console.log(`  ${c ? '✅' : '❌'} ${n}${d ? '  · ' + d : ''}`) }

;(async () => {
  // หา S/N จริงมาใช้
  const lr = await fetch(`${API}/api/auth/login`, { method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({username:'branch1',password:'branch1234'}) })
  const tok = (await lr.json()).access_token
  const sold = (await (await fetch(`${API}/api/items?status=Sold&limit=1`, {headers:{Authorization:'Bearer '+tok}})).json())[0].serial_number

  const b = await chromium.launch()

  console.log('=== 1. ความเร็วในการเข้าถึงงาน (งบเวลาทั้งงานคือ 60 วินาที) ===')
  let page = await b.newPage({ viewport: { width: 1280, height: 860 } })
  let t0 = Date.now()
  await page.goto(BASE, { waitUntil: 'domcontentloaded' })
  const domReady = Date.now() - t0
  await page.waitForSelector('input', { state: 'visible' })
  const interactive = Date.now() - t0
  ok(interactive < 15000, 'ช่องกรอกพร้อมใช้ภายใน 15 วิ', `DOM ${domReady}ms · พร้อมพิมพ์ ${interactive}ms`)

  console.log('\n=== 2. ทำ task ได้ด้วยคีย์บอร์ดอย่างเดียวไหม (ผู้ใช้ที่ใช้เมาส์ไม่ได้) ===')
  await page.keyboard.press('Tab')
  const focused = await page.evaluate(() => document.activeElement.tagName + (document.activeElement.placeholder ? ':'+document.activeElement.placeholder : ''))
  ok(focused.startsWith('INPUT'), 'กด Tab ครั้งแรกโฟกัสที่ช่องกรอกเลย', focused)
  await page.keyboard.type(sold)
  await page.keyboard.press('Enter')
  await page.waitForTimeout(2500)
  const txt = await page.locator('main').innerText()
  ok(txt.includes('อยู่ในประกัน') || txt.includes('หมดประกัน'), 'กด Enter ส่งฟอร์มได้ ไม่ต้องเอื้อมกดปุ่ม')

  console.log('\n=== 3. ป้ายกำกับสำหรับโปรแกรมอ่านหน้าจอ ===')
  const a11y = await page.evaluate(() => {
    const i = document.querySelector('input')
    const btn = document.querySelector('button[type=submit]')
    const labelFor = i.id ? !!document.querySelector(`label[for="${i.id}"]`) : false
    return {
      hasAriaLabel: !!i.getAttribute('aria-label'),
      hasLabelEl: labelFor,
      wrappedInLabel: !!i.closest('label'),
      placeholder: i.placeholder,
      btnText: btn ? btn.textContent.trim() : null,
      h1: document.querySelector('h1')?.textContent.trim() || null,
      lang: document.documentElement.lang || '(ไม่ได้ตั้ง)',
    }
  })
  ok(!!a11y.h1, 'มี <h1> บอกว่าหน้านี้คืออะไร', a11y.h1)
  ok(!!a11y.btnText, 'ปุ่มมีข้อความ ไม่ใช่ไอคอนเปล่า', a11y.btnText)
  const labelled = a11y.hasAriaLabel || a11y.hasLabelEl || a11y.wrappedInLabel
  ok(labelled, 'ช่องกรอกมีป้ายกำกับที่โปรแกรมอ่านหน้าจออ่านได้', labelled ? '' : `มีแค่ placeholder "${a11y.placeholder}" ซึ่งหายไปเมื่อเริ่มพิมพ์`)
  ok(a11y.lang !== '(ไม่ได้ตั้ง)', 'ตั้ง lang ของหน้าเว็บ (บอกโปรแกรมอ่านว่าเป็นภาษาอะไร)', a11y.lang)

  console.log('\n=== 4. ใช้บนมือถือได้ไหม (375px) ===')
  const m = await b.newPage({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true })
  await m.goto(BASE, { waitUntil: 'networkidle' })
  const mob = await m.evaluate(() => {
    const i = document.querySelector('input'); const btn = document.querySelector('button[type=submit]')
    const ir = i.getBoundingClientRect(); const br = btn.getBoundingClientRect()
    return { overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
             scrollW: document.documentElement.scrollWidth, winW: window.innerWidth,
             btnH: Math.round(br.height), btnW: Math.round(br.width), inputVisible: ir.width > 0 }
  })
  ok(!mob.overflow, 'ไม่มีการเลื่อนแนวนอน', `เนื้อหา ${mob.scrollW}px / จอ ${mob.winW}px`)
  ok(mob.btnH >= 44, 'ปุ่มสูงพอสำหรับนิ้ว (>=44px ตาม WCAG 2.5.5)', `สูง ${mob.btnH}px กว้าง ${mob.btnW}px`)
  await m.fill('input', sold); await m.click('button[type=submit]'); await m.waitForTimeout(2500)
  const mtxt = await m.locator('main').innerText()
  ok(mtxt.includes('ประกัน'), 'ทำ task สำเร็จบนมือถือ')

  console.log(`\n${'='.repeat(48)}\nผ่าน ${R.filter(r=>r[0]).length} · ตก ${R.filter(r=>!r[0]).length}`)
  R.filter(r=>!r[0]).forEach(r=>console.log(`  ต้องแก้: ${r[1]} — ${r[2]}`))
  await b.close()
})().catch(e => { console.error(e.message); process.exit(1) })
