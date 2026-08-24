import { useEffect, useState } from 'react'
import client from '../../api/client'

// FR-003, FR-008 — ดูสต็อกเรียลไทม์ของสาขาตัวเอง (server บังคับ scope ให้แล้ว)
export default function BranchDashboard() {
  const [stock, setStock] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    try {
      const { data } = await client.get('/stock')
      setStock(data)
    } catch (err) {
      setError('โหลดข้อมูลสต็อกไม่สำเร็จ')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold text-brand-900">สต็อกสาขาของฉัน</h1>
        <button onClick={load} className="text-sm text-brand-600 hover:underline">
          รีเฟรช
        </button>
      </div>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
      {loading ? (
        <p className="text-gray-500">กำลังโหลด...</p>
      ) : stock.length === 0 ? (
        <p className="text-gray-500">ยังไม่มีสินค้าในสต็อก</p>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-100 text-brand-900">
              <tr>
                <th className="text-left px-4 py-2">หมวดหมู่</th>
                <th className="text-left px-4 py-2">ยี่ห้อ / รุ่น</th>
                <th className="text-right px-4 py-2">คงเหลือ</th>
                <th className="text-right px-4 py-2">จุดสั่งซื้อ</th>
              </tr>
            </thead>
            <tbody>
              {stock.map((row) => {
                const low = row.reorder_point != null && row.on_hand <= row.reorder_point
                return (
                  <tr key={row.sku_id} className={`border-t border-brand-50 ${low ? 'bg-red-50' : ''}`}>
                    <td className="px-4 py-2">{row.category}</td>
                    <td className="px-4 py-2">
                      {row.brand} {row.model}
                    </td>
                    <td className="px-4 py-2 text-right font-medium">
                      {row.on_hand}
                      {low && <span className="ml-2 text-red-600 text-xs">⚠ ใกล้หมด</span>}
                    </td>
                    <td className="px-4 py-2 text-right text-gray-500">{row.reorder_point ?? '—'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
