import { useEffect, useState } from 'react'
import client from '../../api/client'

// FR-003 — Admin เห็นสต็อกทุกสาขา
// หมายเหตุ: ยังไม่มี alert/notification จริง (FR-012 partial) — ไฮไลท์แถวสีแดงเป็น
// ตัวช่วยมองเห็นเบื้องต้นจากข้อมูลที่มีอยู่แล้ว ไม่ใช่ระบบแจ้งเตือนแบบ push
// FR-014 (CR-008) — KPI card สรุปภาพรวม เสริมของหน้าเดิม ไม่ใช่หน้าใหม่ ไม่มี sales-revenue
// KPI (ไม่มี field ราคา/endpoint รายการขาย ดู CR-008)
export default function AdminDashboard() {
  const [stock, setStock] = useState([])
  const [products, setProducts] = useState([])
  const [pendingPRs, setPendingPRs] = useState([])
  const [branches, setBranches] = useState([])
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    const [stockRes, productsRes, prRes, branchesRes] = await Promise.all([
      client.get('/stock'),
      client.get('/products'),
      client.get('/purchase-requests?status=Pending'),
      client.get('/branches'),
    ])
    setStock(stockRes.data)
    setProducts(productsRes.data)
    setPendingPRs(prRes.data)
    setBranches(branchesRes.data)
    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [])

  const lowStockCount = stock.filter((r) => r.reorder_point != null && r.on_hand <= r.reorder_point).length
  const totalOnHand = stock.reduce((sum, r) => sum + r.on_hand, 0)

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold text-brand-900">สต็อกรวมทุกสาขา</h1>
        <button onClick={load} className="text-sm text-brand-600 hover:underline">
          รีเฟรช
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-xs text-gray-500 mb-1">สินค้าที่ใช้งานอยู่</p>
          <p className="text-2xl font-semibold text-brand-900">{products.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-xs text-gray-500 mb-1">จำนวนชิ้นคงเหลือรวม</p>
          <p className="text-2xl font-semibold text-brand-900">{totalOnHand}</p>
        </div>
        <div className={`rounded-lg shadow p-4 ${lowStockCount > 0 ? 'bg-red-50' : 'bg-white'}`}>
          <p className="text-xs text-gray-500 mb-1">รายการใกล้หมด</p>
          <p className={`text-2xl font-semibold ${lowStockCount > 0 ? 'text-red-700' : 'text-brand-900'}`}>
            {lowStockCount}
          </p>
        </div>
        <div className={`rounded-lg shadow p-4 ${pendingPRs.length > 0 ? 'bg-amber-50' : 'bg-white'}`}>
          <p className="text-xs text-gray-500 mb-1">คำขอสั่งซื้อรออนุมัติ ({branches.length} สาขา)</p>
          <p className={`text-2xl font-semibold ${pendingPRs.length > 0 ? 'text-amber-700' : 'text-brand-900'}`}>
            {pendingPRs.length}
          </p>
        </div>
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
