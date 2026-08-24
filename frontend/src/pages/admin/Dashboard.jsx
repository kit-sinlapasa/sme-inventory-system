import { useEffect, useState } from 'react'
import client from '../../api/client'

// FR-003 — Admin เห็นสต็อกทุกสาขา
// หมายเหตุ: ยังไม่มี alert/notification จริง (FR-012 partial) — ไฮไลท์แถวสีแดงเป็น
// ตัวช่วยมองเห็นเบื้องต้นจากข้อมูลที่มีอยู่แล้ว ไม่ใช่ระบบแจ้งเตือนแบบ push
export default function AdminDashboard() {
  const [stock, setStock] = useState([])
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    const { data } = await client.get('/stock')
    setStock(data)
    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [])

  const lowStockCount = stock.filter((r) => r.reorder_point != null && r.on_hand <= r.reorder_point).length

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold text-brand-900">สต็อกรวมทุกสาขา</h1>
        <button onClick={load} className="text-sm text-brand-600 hover:underline">
          รีเฟรช
        </button>
      </div>

      {lowStockCount > 0 && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2 mb-4">
          ⚠ มี {lowStockCount} รายการที่คงเหลือต่ำกว่าจุดสั่งซื้อ
        </div>
      )}

      {loading ? (
        <p className="text-gray-500">กำลังโหลด...</p>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-100 text-brand-900">
              <tr>
                <th className="text-left px-4 py-2">สาขา</th>
                <th className="text-left px-4 py-2">หมวดหมู่</th>
                <th className="text-left px-4 py-2">ยี่ห้อ / รุ่น</th>
                <th className="text-right px-4 py-2">คงเหลือ</th>
                <th className="text-right px-4 py-2">จุดสั่งซื้อ</th>
              </tr>
            </thead>
            <tbody>
              {stock.map((row, i) => {
                const low = row.reorder_point != null && row.on_hand <= row.reorder_point
                return (
                  <tr key={`${row.sku_id}-${row.branch_id}-${i}`} className={`border-t border-brand-50 ${low ? 'bg-red-50' : ''}`}>
                    <td className="px-4 py-2">สาขา #{row.branch_id}</td>
                    <td className="px-4 py-2">{row.category}</td>
                    <td className="px-4 py-2">
                      {row.brand} {row.model}
                    </td>
                    <td className="px-4 py-2 text-right font-medium">{row.on_hand}</td>
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
