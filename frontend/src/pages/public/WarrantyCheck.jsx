import { useState } from 'react'
import client from '../../api/client'

// FR-006, US-01 — เช็คประกันสาธารณะ ไม่ต้อง login
//
// NFR-USE-01 — หน้านี้คือ task ที่ NFR วัดผลโดยตรง ("ผู้ใช้ใหม่เช็คประกันสำเร็จ
// ภายใน 60 วินาที โดยไม่ต้องมีคนสอน") ตัวอย่างและข้อความ error จึงเป็นส่วนหนึ่ง
// ของ requirement ไม่ใช่แค่ข้อความประกอบ
//
// รูปแบบ S/N จริงที่ระบบออกให้คือ SN-<ประเภทสินค้า>-<เลข 5 หลัก> (ดู scripts/seed.py)
// เดิมช่องกรอกยกตัวอย่างเป็น "SN-0001234" ซึ่ง **ผิดรูปแบบ** — ไม่มีส่วนประเภทสินค้า
// และเลขยาว 7 หลัก ผู้ใช้ใหม่ที่ไม่มีคนสอนย่อมพิมพ์ตามตัวอย่างบนหน้าจอแล้วล้มเหลวทันที
//
// ค่านี้เป็น **ตัวอย่างรูปแบบ** ไม่ใช่ S/N ที่มีอยู่จริงในฐานข้อมูล และตั้งใจให้เป็นแบบนั้น —
// ถ้า hardcode S/N จริงตัวใดตัวหนึ่ง มันจะหายไปทุกครั้งที่ seed ใหม่ กลายเป็นบั๊กเดิมอีกรอบ
// (ตรวจแล้วว่าเกิดขึ้นจริง: S/N ที่เคยมีบน production หายไปหลัง reseed)
const SERIAL_FORMAT_EXAMPLE = 'SN-GPU-00042'

export default function WarrantyCheck() {
  const [serial, setSerial] = useState('')
  const [result, setResult] = useState(null)
  const [notFound, setNotFound] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleCheck(e) {
    e.preventDefault()
    setNotFound(false)
    setResult(null)
    setLoading(true)
    try {
      const { data } = await client.get(`/public/warranty/${encodeURIComponent(serial)}`)
      setResult(data)
    } catch (err) {
      setNotFound(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="rd-page flex items-center justify-center p-6">
      <div className="rd-card p-8 w-full max-w-md">
        <h1 className="rd-title text-xl mb-1">ตรวจสอบสถานะการรับประกัน</h1>
        <p className="text-sm text-ink-muted mb-4">
          กรอกหมายเลขซีเรียล (S/N) ที่อยู่บนสติกเกอร์ข้างตัวสินค้าหรือบนกล่อง
        </p>

        <form onSubmit={handleCheck} className="flex gap-2">
          <input
            className="rd-input flex-1"
            placeholder={`เช่น ${SERIAL_FORMAT_EXAMPLE}`}
            value={serial}
            onChange={(e) => setSerial(e.target.value)}
            required
          />
          <button
            className="rd-btn"
            type="submit"
            disabled={loading}
          >
            {loading ? 'กำลังตรวจสอบ...' : 'ตรวจสอบ'}
          </button>
        </form>

        {result && (
          <div className="mt-4 p-4 bg-ink-accentSoft rounded-lg space-y-1 text-ink-text">
            <p>
              <span className="font-medium">รุ่นสินค้า:</span> {result.model}
            </p>
            <p>
              <span className="font-medium">สถานะ:</span> {result.warranty_status}
            </p>
            <p>
              <span className="font-medium">วันหมดประกัน:</span>{' '}
              {new Date(result.warranty_expires_at).toLocaleDateString('th-TH')}
            </p>
          </div>
        )}

        {/* ข้อความ error ต้องบอก "รูปแบบที่ถูกต้อง" ด้วย ไม่ใช่แค่บอกว่าไม่พบ —
            ไม่งั้นผู้ใช้ที่พิมพ์ผิดรูปแบบจะไม่มีทางรู้เลยว่าต้องแก้อะไร กลายเป็นทางตัน
            (สาเหตุที่พบตอนเดินทดสอบ task ตาม NFR-USE-01) */}
        {notFound && (
          <div className="mt-4 text-sm">
            <p className="text-[#d03b3b]">ไม่พบ S/N นี้ในระบบ</p>
            <p className="text-ink-muted mt-1">
              ตรวจสอบว่าพิมพ์ครบตามรูปแบบ <span className="font-mono">{SERIAL_FORMAT_EXAMPLE}</span> หรือไม่
              (ขึ้นต้นด้วย SN- ตามด้วยประเภทสินค้า และตัวเลข 5 หลัก)
            </p>
            <p className="text-ink-muted mt-1">
              ถ้ายังไม่พบ แปลว่าสินค้าชิ้นนี้อาจยังไม่ถูกบันทึกการขาย กรุณาติดต่อสาขาที่ซื้อ
            </p>
          </div>
        )}
      </div>
    </main>
  )
}
