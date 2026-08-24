# ============================================================================
#  reseed ฐานข้อมูลสาธิตบน Render (Windows / PowerShell)
#
#  วิธีใช้:  cd backend
#            .\scripts\reseed_remote.ps1
#            แล้ววาง External Database URL ตอนที่สคริปต์ถาม
#
#  ทำไมต้องมีสคริปต์นี้แทนการพิมพ์คำสั่งเอง — เจอปัญหาจริงมาแล้ว 2 รอบที่รันแล้ว
#  เหมือนสำเร็จแต่ข้อมูลบน production ไม่เปลี่ยนเลย โดยไม่มีอะไรฟ้อง สาเหตุที่เป็นไปได้:
#
#   1. PowerShell แปลง $ ใน "double quote" เป็นชื่อตัวแปร — ถ้ารหัสผ่านของ Render
#      มี $ อยู่ URL จะถูกตัดทิ้งบางส่วนเงียบ ๆ กลายเป็น URL ที่ต่อไม่ติดหรือต่อผิดที่
#      สคริปต์นี้รับค่าผ่าน Read-Host จึงไม่ผ่านการ interpolate ของ PowerShell เลย
#   2. ใช้ Internal Database URL ซึ่งต่อได้เฉพาะจากภายในเครือข่าย Render
#   3. วาง placeholder <External Database URL> ลงไปตรง ๆ
#   4. รันจากโฟลเดอร์ผิดจน import app.* ไม่เจอ
#
#  สคริปต์นี้จึงตรวจทั้ง 4 ข้อก่อนแตะข้อมูล และบอกผลตอนจบว่าสำเร็จจริงหรือไม่
# ============================================================================

$ErrorActionPreference = 'Stop'

# --- 1. ต้องรันจากโฟลเดอร์ backend ---
if (-not (Test-Path 'scripts\seed.py')) {
    Write-Host "[X] ต้องรันจากโฟลเดอร์ backend" -ForegroundColor Red
    Write-Host "    ลองใหม่:  cd backend  แล้วค่อย  .\scripts\reseed_remote.ps1"
    exit 1
}

# --- 2. รับ URL แบบไม่ผ่าน string interpolation ของ PowerShell ---
Write-Host ""
Write-Host "วาง External Database URL จาก Render dashboard" -ForegroundColor Cyan
Write-Host "  (หน้า sme-inventory-db -> Connect -> External Database URL)"
Write-Host "  ค่านี้อยู่แค่ในเครื่องคุณ ไม่ถูกส่งไปไหน และไม่ถูกบันทึกลงไฟล์"
$dbUrl = Read-Host "URL"
$dbUrl = $dbUrl.Trim().Trim('"').Trim("'")

# --- 3. ตรวจว่า URL ใช้ได้จริงก่อนไปต่อ ---
if ($dbUrl -match '^<|>$' -or $dbUrl -match 'External Database URL') {
    Write-Host "[X] ดูเหมือนวาง placeholder มา ไม่ใช่ URL จริง" -ForegroundColor Red
    exit 1
}
if ($dbUrl -notmatch '^postgres(ql)?://') {
    Write-Host "[X] URL ต้องขึ้นต้นด้วย postgres:// หรือ postgresql://" -ForegroundColor Red
    Write-Host "    ได้มา: $($dbUrl.Substring(0, [Math]::Min(30, $dbUrl.Length)))..."
    exit 1
}
# Internal URL ของ Render ไม่มี .render.com ต่อท้าย host และต่อจากนอกไม่ได้
if ($dbUrl -notmatch '\.render\.com') {
    Write-Host "[!] URL นี้ไม่มี '.render.com' — น่าจะเป็น Internal Database URL" -ForegroundColor Yellow
    Write-Host "    Internal URL ต่อได้เฉพาะจากภายใน Render เท่านั้น ต้องใช้ External"
    $go = Read-Host "จะไปต่อไหม (y/N)"
    if ($go -ne 'y') { exit 1 }
}

# --- 4. ส่งต่อให้ seed.py โดยไม่ให้ค่าไปโผล่ใน command line หรือ history ---
$env:DATABASE_URL = $dbUrl
Write-Host ""
Write-Host "กำลังรัน seed..." -ForegroundColor Cyan
Write-Host ""

$env:PYTHONUTF8 = '1'
python -m scripts.seed --reset
$code = $LASTEXITCODE

# --- 5. เก็บกวาด: ไม่ปล่อยให้ตัวแปรค้างจน dev server ชี้ production โดยไม่รู้ตัว ---
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue

Write-Host ""
if ($code -eq 0) {
    Write-Host "[OK] seed สำเร็จ" -ForegroundColor Green
    Write-Host "     ตรวจสอบได้ที่ https://sme-inventory-frontend.onrender.com"
    Write-Host "     กราฟยอดขายรายวันต้องมีเส้นต่อเนื่อง ไม่ใช่จุดเดียว"
} else {
    Write-Host "[X] seed ไม่สำเร็จ (exit code $code)" -ForegroundColor Red
    Write-Host "    ข้อความ error อยู่ด้านบน — ส่งมาให้ดูได้เลย"
}
Write-Host "ล้างตัวแปร DATABASE_URL ออกจาก session นี้แล้ว" -ForegroundColor DarkGray
exit $code
