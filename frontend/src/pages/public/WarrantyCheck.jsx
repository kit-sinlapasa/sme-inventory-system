import { useState } from 'react'
import client from '../../api/client'

// FR-006, US-01 — เช็คประกันสาธารณะ ไม่ต้อง login
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
        <p className="text-sm text-ink-muted mb-4">กรอกหมายเลขซีเรียล (S/N) บนตัวสินค้า</p>

        <form onSubmit={handleCheck} className="flex gap-2">
          <input
            className="rd-input flex-1"
            placeholder="เช่น SN-0001234"
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

        {notFound && (
          <p className="mt-4 text-[#d03b3b] text-sm">ไม่พบข้อมูล กรุณาตรวจสอบ S/N อีกครั้ง</p>
        )}
      </div>
    </main>
  )
}
