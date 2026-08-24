import { useEffect, useState } from 'react'
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import client from '../../api/client'

// FR-003 — Admin เห็นสต็อกทุกสาขา
// หมายเหตุ: ยังไม่มี alert/notification จริง (FR-012 partial) — ไฮไลท์แถวสีแดงเป็น
// ตัวช่วยมองเห็นเบื้องต้นจากข้อมูลที่มีอยู่แล้ว ไม่ใช่ระบบแจ้งเตือนแบบ push
// FR-014 (CR-008) — KPI card สรุปภาพรวม เสริมของหน้าเดิม ไม่ใช่หน้าใหม่ ไม่มี sales-revenue
// KPI (ไม่มี field ราคา/endpoint รายการขาย ดู CR-008)
// CR-010 — ธีมมืดเฉพาะหน้านี้เท่านั้น (ดูขอบเขต/เหตุผลใน docs/01-Requirements-Package.md)
// กราฟใช้ข้อมูลจริงที่มีอยู่แล้วเท่านั้น (breakdown ตามหมวดหมู่/สถานะ) — ไม่มีตัวเลขเทรนด์/%
// เปลี่ยนแปลงปลอม เพราะระบบไม่ได้เก็บ time-series data จริง
const CATEGORY_COLORS = ['#8b5cf6', '#ec4899', '#22d3ee', '#34d399', '#fbbf24', '#f87171']
const STATUS_COLORS = { Pending: '#fbbf24', Approved: '#34d399', Rejected: '#f87171' }

export default function AdminDashboard() {
  const [stock, setStock] = useState([])
  const [products, setProducts] = useState([])
  const [pendingPRs, setPendingPRs] = useState([])
  const [allPRs, setAllPRs] = useState([])
  const [branches, setBranches] = useState([])
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    const [stockRes, productsRes, prRes, allPrRes, branchesRes] = await Promise.all([
      client.get('/stock'),
      client.get('/products'),
      client.get('/purchase-requests?status=Pending'),
      client.get('/purchase-requests'),
      client.get('/branches'),
    ])
    setStock(stockRes.data)
    setProducts(productsRes.data)
    setPendingPRs(prRes.data)
    setAllPRs(allPrRes.data)
    setBranches(branchesRes.data)
    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [])

  const lowStockCount = stock.filter((r) => r.reorder_point != null && r.on_hand <= r.reorder_point).length
  const totalOnHand = stock.reduce((sum, r) => sum + r.on_hand, 0)

  const stockByCategory = Object.values(
    stock.reduce((acc, r) => {
      acc[r.category] = acc[r.category] || { name: r.category, value: 0 }
      acc[r.category].value += r.on_hand
      return acc
    }, {}),
  )

  const prByStatus = ['Pending', 'Approved', 'Rejected']
    .map((status) => ({ name: status, value: allPRs.filter((pr) => pr.status === status).length }))
    .filter((row) => row.value > 0)

  return (
    <div className="-m-6 p-6 bg-ink-bg min-h-[calc(100vh-57px)]">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold text-ink-text">สต็อกรวมทุกสาขา</h1>
        <button onClick={load} className="text-sm text-ink-muted hover:text-ink-text transition">
          รีเฟรช
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <StatCard label="สินค้าที่ใช้งานอยู่" value={products.length} />
        <StatCard label="จำนวนชิ้นคงเหลือรวม" value={totalOnHand} />
        <StatCard
          label="รายการใกล้หมด"
          value={lowStockCount}
          gradient={lowStockCount > 0 ? 'from-rose-500 to-orange-500' : null}
        />
        <StatCard
          label={`คำขอสั่งซื้อรออนุมัติ (${branches.length} สาขา)`}
          value={pendingPRs.length}
          gradient={pendingPRs.length > 0 ? 'from-violet-500 to-fuchsia-500' : null}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <ChartCard title="สต็อกคงเหลือตามหมวดหมู่" data={stockByCategory} colors={CATEGORY_COLORS} />
        <ChartCard
          title="คำขอสั่งซื้อตามสถานะ"
          data={prByStatus}
          colors={prByStatus.map((row) => STATUS_COLORS[row.name])}
        />
      </div>

      {lowStockCount > 0 && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm rounded-lg px-4 py-2 mb-4">
          ⚠ มี {lowStockCount} รายการที่คงเหลือต่ำกว่าจุดสั่งซื้อ
        </div>
      )}

      {loading ? (
        <p className="text-ink-muted">กำลังโหลด...</p>
      ) : (
        <div className="bg-ink-surface border border-ink-border rounded-xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-ink-muted">
              <tr>
                <th className="text-left px-4 py-3 font-medium">สาขา</th>
                <th className="text-left px-4 py-3 font-medium">หมวดหมู่</th>
                <th className="text-left px-4 py-3 font-medium">ยี่ห้อ / รุ่น</th>
                <th className="text-right px-4 py-3 font-medium">คงเหลือ</th>
                <th className="text-right px-4 py-3 font-medium">จุดสั่งซื้อ</th>
              </tr>
            </thead>
            <tbody>
              {stock.map((row, i) => {
                const low = row.reorder_point != null && row.on_hand <= row.reorder_point
                return (
                  <tr
                    key={`${row.sku_id}-${row.branch_id}-${i}`}
                    className={`border-t border-ink-border ${low ? 'bg-rose-500/10' : ''}`}
                  >
                    <td className="px-4 py-3 text-ink-text">สาขา #{row.branch_id}</td>
                    <td className="px-4 py-3 text-ink-muted">{row.category}</td>
                    <td className="px-4 py-3 text-ink-text">
                      {row.brand} {row.model}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-ink-text">{row.on_hand}</td>
                    <td className="px-4 py-3 text-right text-ink-muted">{row.reorder_point ?? '—'}</td>
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

function StatCard({ label, value, gradient }) {
  if (gradient) {
    return (
      <div className={`rounded-xl p-4 bg-gradient-to-br ${gradient} shadow-lg shadow-black/20`}>
        <p className="text-xs text-white/80 mb-1">{label}</p>
        <p className="text-2xl font-semibold text-white">{value}</p>
      </div>
    )
  }
  return (
    <div className="rounded-xl p-4 bg-ink-surface border border-ink-border">
      <p className="text-xs text-ink-muted mb-1">{label}</p>
      <p className="text-2xl font-semibold text-ink-text">{value}</p>
    </div>
  )
}

function ChartCard({ title, data, colors }) {
  return (
    <div className="rounded-xl p-4 bg-ink-surface border border-ink-border">
      <p className="text-sm text-ink-muted mb-2">{title}</p>
      {data.length === 0 ? (
        <p className="text-ink-muted text-sm py-8 text-center">ไม่มีข้อมูล</p>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={2}>
              {data.map((entry, i) => (
                <Cell key={entry.name} fill={colors[i % colors.length]} stroke="none" />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: '#1e2233', border: '1px solid #2a2f42', borderRadius: 8, color: '#f4f5f9' }}
            />
            <Legend wrapperStyle={{ fontSize: 12, color: '#9297ab' }} />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
