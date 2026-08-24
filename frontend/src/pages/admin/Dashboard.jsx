import { useEffect, useState } from 'react'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import client from '../../api/client'

// FR-003 — Admin เห็นสต็อกทุกสาขา
// หมายเหตุ: ยังไม่มี alert/notification จริง (FR-012 partial) — ไฮไลท์แถวสีแดงเป็น
// ตัวช่วยมองเห็นเบื้องต้นจากข้อมูลที่มีอยู่แล้ว ไม่ใช่ระบบแจ้งเตือนแบบ push
// FR-014 (CR-008) — KPI card สรุปภาพรวม เสริมของหน้าเดิม ไม่ใช่หน้าใหม่ ไม่มี sales-revenue
// KPI (ไม่มี field ราคา/endpoint รายการขาย ดู CR-008)
// CR-010 — ธีมหน้านี้เท่านั้น อิงสีจริงจาก dashboard.render.com (ตรวจด้วย getComputedStyle
// จริง) — สว่าง ไม่ใช่มืด ตามที่ตรวจสอบพบว่า Render ใช้ธีมสว่างจริง ไม่ใช่ธีมมืดอย่างที่
// สันนิษฐานไว้รอบแรกจากภาพตัวอย่างที่ไม่เกี่ยวกับ Render
// รูปแบบกราฟ: horizontal bar ไม่ใช่ pie/donut — ตาม dataviz skill "part-to-whole/
// compare magnitude" ควรใช้ bar ไม่ใช่ pie และ pie เป็น all-pairs comparison ที่ผ่าน
// CVD-safety check ได้แค่ 3 สีเท่านั้น (validate จริงแล้วว่า 6 สีพร้อมกันบน pie ล้มเหลว)
// หมวดหมู่สินค้า = สีเดียว (sequential, ไม่ใช่ identity) + label ตรงบนแท่ง — เลี่ยงปัญหา CVD
// ไปเลยเพราะไม่ต้องแยกสีต่อหมวดหมู่ · สถานะ PR = fixed status palette ตาม dataviz skill
// (แม้ contrast ต่ำกว่าเกณฑ์ตามที่เอกสารระบุไว้ แต่มี label กำกับทุกแท่งตามข้อกำหนด mitigation)
// ไม่มีตัวเลขเทรนด์/% เปลี่ยนแปลงปลอม เพราะระบบไม่มี time-series data จริง
const MAGNITUDE_COLOR = '#7a3ff1'
const STATUS_COLORS = { Pending: '#fab219', Approved: '#0ca30c', Rejected: '#d03b3b' }

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
  ).sort((a, b) => b.value - a.value)

  const prByStatus = ['Pending', 'Approved', 'Rejected']
    .map((status) => ({ name: status, value: allPRs.filter((pr) => pr.status === status).length }))
    .filter((row) => row.value > 0)

  return (
    <div className="-m-6 p-6 bg-ink-bg min-h-[calc(100vh-57px)]">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold text-ink-text">สต็อกรวมทุกสาขา</h1>
        <button onClick={load} className="text-sm text-ink-accent hover:underline">
          รีเฟรช
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <StatCard label="สินค้าที่ใช้งานอยู่" value={products.length} />
        <StatCard label="จำนวนชิ้นคงเหลือรวม" value={totalOnHand} />
        <StatCard label="รายการใกล้หมด" value={lowStockCount} tone={lowStockCount > 0 ? 'critical' : null} />
        <StatCard
          label={`คำขอสั่งซื้อรออนุมัติ (${branches.length} สาขา)`}
          value={pendingPRs.length}
          tone={pendingPRs.length > 0 ? 'warning' : null}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <ChartCard title="สต็อกคงเหลือตามหมวดหมู่" data={stockByCategory} color={MAGNITUDE_COLOR} />
        <ChartCard
          title="คำขอสั่งซื้อตามสถานะ"
          data={prByStatus}
          colors={prByStatus.map((row) => STATUS_COLORS[row.name])}
        />
      </div>

      {lowStockCount > 0 && (
        <div className="bg-white border border-[#d03b3b]/30 text-[#d03b3b] text-sm rounded-lg px-4 py-2 mb-4">
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
                    className={`border-t border-ink-border ${low ? 'bg-[#fdf2f2]' : ''}`}
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

const TONE_TEXT = { warning: 'text-[#a3690f]', critical: 'text-[#d03b3b]' }

function StatCard({ label, value, tone }) {
  return (
    <div className="rounded-xl p-4 bg-ink-surface border border-ink-border">
      <p className="text-xs text-ink-muted mb-1">{label}</p>
      <p className={`text-2xl font-semibold ${tone ? TONE_TEXT[tone] : 'text-ink-text'}`}>{value}</p>
    </div>
  )
}

function ChartCard({ title, data, color, colors }) {
  // แท่งแนวนอน (recharts layout="vertical") — ชื่อหมวดหมู่/สถานะเป็น direct label
  // บนแกน Y เสมอ ไม่ต้องพึ่งสีอย่างเดียวในการแยกแยะ (ตาม dataviz skill mitigation rule)
  const height = Math.max(data.length * 40, 80)
  return (
    <div className="rounded-xl p-4 bg-ink-surface border border-ink-border">
      <p className="text-sm text-ink-muted mb-2">{title}</p>
      {data.length === 0 ? (
        <p className="text-ink-muted text-sm py-8 text-center">ไม่มีข้อมูล</p>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="name"
              width={90}
              tick={{ fontSize: 12, fill: '#0b0b0b' }}
              axisLine={{ stroke: '#e5e7eb' }}
              tickLine={false}
            />
            <Tooltip
              cursor={{ fill: '#f4f0ff' }}
              contentStyle={{ background: '#fcfcfb', border: '1px solid #e5e7eb', borderRadius: 8, color: '#0b0b0b' }}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={18}>
              {data.map((entry, i) => (
                <Cell key={entry.name} fill={colors ? colors[i % colors.length] : color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
