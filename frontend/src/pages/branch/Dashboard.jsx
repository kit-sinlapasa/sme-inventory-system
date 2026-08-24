import { useEffect, useState } from 'react'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import client from '../../api/client'

// FR-003, FR-008 — ดูสต็อกเรียลไทม์ของสาขาตัวเอง (server บังคับ scope ให้แล้ว)
// FR-014 (CR-008) — KPI card สรุปภาพรวมของสาขาตัวเอง เสริมของหน้าเดิม
// CR-010 — ธีมหน้านี้เท่านั้น อิงสีจริงจาก dashboard.render.com (สว่าง ไม่ใช่มืด — ดูเหตุผล
// ที่แก้ไขใน docs/01-Requirements-Package.md)
// รูปแบบกราฟ: horizontal bar ไม่ใช่ pie/donut — ตาม dataviz skill "part-to-whole/compare
// magnitude" ควรใช้ bar และ pie เป็น all-pairs comparison ที่ผ่าน CVD-safety check ได้แค่ 3 สี
// (validate จริงแล้วว่า 6 สีพร้อมกันบน pie ล้มเหลว) หมวดหมู่สินค้า = สีเดียว + label บนแท่ง
// สถานะ PR = fixed status palette ตาม dataviz skill (มี label กำกับทุกแท่งตาม mitigation rule)
// ไม่มีตัวเลขเทรนด์ปลอม (ระบบไม่เก็บ time-series จริง)
const MAGNITUDE_COLOR = '#7a3ff1'
const STATUS_COLORS = { Pending: '#fab219', Approved: '#0ca30c', Rejected: '#d03b3b' }

export default function BranchDashboard() {
  const [stock, setStock] = useState([])
  const [pendingPRs, setPendingPRs] = useState([])
  const [allPRs, setAllPRs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    try {
      const [stockRes, prRes, allPrRes] = await Promise.all([
        client.get('/stock'),
        client.get('/purchase-requests?status=Pending'),
        client.get('/purchase-requests'),
      ])
      setStock(stockRes.data)
      setPendingPRs(prRes.data)
      setAllPRs(allPrRes.data)
    } catch (err) {
      setError('โหลดข้อมูลสต็อกไม่สำเร็จ')
    } finally {
      setLoading(false)
    }
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
        <h1 className="text-lg font-semibold text-ink-text">สต็อกสาขาของฉัน</h1>
        <button onClick={load} className="text-sm text-ink-accent hover:underline">
          รีเฟรช
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <StatCard label="ชิ้นคงเหลือทั้งหมด" value={totalOnHand} />
        <StatCard label="รายการใกล้หมด" value={lowStockCount} tone={lowStockCount > 0 ? 'critical' : null} />
        <StatCard label="คำขอสั่งซื้อรออนุมัติ" value={pendingPRs.length} tone={pendingPRs.length > 0 ? 'warning' : null} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <ChartCard title="สต็อกคงเหลือตามหมวดหมู่" data={stockByCategory} color={MAGNITUDE_COLOR} />
        <ChartCard
          title="คำขอสั่งซื้อตามสถานะ"
          data={prByStatus}
          colors={prByStatus.map((row) => STATUS_COLORS[row.name])}
        />
      </div>

      {error && <p className="text-[#d03b3b] text-sm mb-4">{error}</p>}
      {loading ? (
        <p className="text-ink-muted">กำลังโหลด...</p>
      ) : stock.length === 0 ? (
        <p className="text-ink-muted">ยังไม่มีสินค้าในสต็อก</p>
      ) : (
        <div className="bg-ink-surface border border-ink-border rounded-xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-ink-muted">
              <tr>
                <th className="text-left px-4 py-3 font-medium">หมวดหมู่</th>
                <th className="text-left px-4 py-3 font-medium">ยี่ห้อ / รุ่น</th>
                <th className="text-right px-4 py-3 font-medium">คงเหลือ</th>
                <th className="text-right px-4 py-3 font-medium">จุดสั่งซื้อ</th>
              </tr>
            </thead>
            <tbody>
              {stock.map((row) => {
                const low = row.reorder_point != null && row.on_hand <= row.reorder_point
                return (
                  <tr key={row.sku_id} className={`border-t border-ink-border ${low ? 'bg-[#fdf2f2]' : ''}`}>
                    <td className="px-4 py-3 text-ink-muted">{row.category}</td>
                    <td className="px-4 py-3 text-ink-text">
                      {row.brand} {row.model}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-ink-text">
                      {row.on_hand}
                      {low && <span className="ml-2 text-[#d03b3b] text-xs">⚠ ใกล้หมด</span>}
                    </td>
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
