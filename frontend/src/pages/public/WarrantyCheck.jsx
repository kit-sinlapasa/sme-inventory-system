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
    <main className="min-h-screen bg-brand-50 flex items-center justify-center p-6">
      <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-md">
        <h1 className="text-xl font-semibold text-brand-900 mb-1">ตรวจสอบสถานะการรับประกัน</h1>
        <p className="text-sm text-gray-500 mb-4">กรอกหมายเลขซีเรียล (S/N) บนตัวสินค้า</p>

        <form onSubmit={handleCheck} className="flex gap-2">
          <input
            className="flex-1 border border-brand-100 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-600"
            placeholder="เช่น SN-0001234"
            value={serial}
            onChange={(e) => setSerial(e.target.value)}
            required
          />
          <button
            className="bg-brand-600 text-white px-4 py-2 rounded hover:bg-brand-900 transition disabled:opacity-50"
            type="submit"
            disabled={loading}
          >
            {loading ? 'กำลังตรวจสอบ...' : 'ตรวจสอบ'}
          </button>
        </form>

        {result && (
          <div className="mt-4 p-4 bg-brand-100 rounded space-y-1 text-brand-900">
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
          <p className="mt-4 text-red-600 text-sm">ไม่พบข้อมูล กรุณาตรวจสอบ S/N อีกครั้ง</p>
        )}
      </div>
    </main>
  )
}
