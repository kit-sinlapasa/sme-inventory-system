import { useEffect, useState } from 'react'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import client from '../../api/client'
import ProductDetailModal from '../../components/ProductDetailModal'

// FR-003 — Admin เห็นสต็อกทุกสาขา
// หมายเหตุ: ยังไม่มี alert/notification จริง (FR-012 partial) — ไฮไลท์แถวสีแดงเป็น
// ตัวช่วยมองเห็นเบื้องต้นจากข้อมูลที่มีอยู่แล้ว ไม่ใช่ระบบแจ้งเตือนแบบ push
// FR-014 (CR-008) — KPI card สรุปภาพรวม เสริมของหน้าเดิม ไม่ใช่หน้าใหม่ ไม่มี sales-revenue
// KPI (ไม่มี field ราคา/endpoint รายการขาย ดู CR-008)
// CR-010 — ธีมหน้านี้เท่านั้น อิงสีจริงจาก dashboard.render.com (ตรวจด้วย getComputedStyle
// จริง) — สว่าง ไม่ใช่มืด ตามที่ตรวจสอบพบว่า Render ใช้ธีมสว่างจริง ไม่ใช่ธีมมืดอย่างที่
// สันนิษฐานไว้รอบแรกจากภาพตัวอย่างที่ไม่เกี่ยวกับ Render
// รูปแบบกราฟ: horizontal bar ไม่ใช่ pie/donut — ตาม dataviz skill "part-to-whole/
// compare magnitude" ควรใช้ bar ไม่ใช่ pie (pie เป็น all-pairs comparison ที่ validate แล้ว
// ว่ารองรับได้แค่ 3 สี)
// CATEGORY_COLORS: palette นี้ validate ผ่าน CVD-safety check ครบทุกข้อในโหมด adjacent-pairs
// ซึ่งเป็นโหมดที่ถูกต้องสำหรับ bar chart (แท่งเรียงติดกัน ไม่ได้เทียบทุกคู่พร้อมกันแบบ pie)
// worst adjacent CVD ΔE 9.1 / normal-vision 19.6 — ผ่านเกณฑ์ทั้งคู่
// contrast บางสีต่ำกว่า 3:1 แต่ทุกแท่งมี label ชื่อหมวดหมู่กำกับตรงแกน Y เสมอ (mitigation ที่
// เอกสารกำหนด) จึงไม่ต้องพึ่งสีอย่างเดียวในการอ่าน
// สถานะ PR = fixed status palette ตาม dataviz skill (มี label กำกับทุกแท่งเช่นกัน)
// ไม่มีตัวเลขเทรนด์/% เปลี่ยนแปลงปลอม เพราะระบบไม่มี time-series data จริง
// สีผูกกับ "หมวดหมู่" ไม่ใช่ลำดับในกราฟ — ตาราง/กราฟเรียงตามยอดคงเหลือซึ่งเปลี่ยนได้ตลอด
// ถ้าผูกสีกับ index สีของแต่ละหมวดหมู่จะสลับไปมาเมื่อข้อมูลเปลี่ยน (ผิดหลัก dataviz skill:
// "color follows the entity, never its rank")
const CATEGORY_ORDER = ['RAM', 'Mainboard', 'CPU', 'GPU', 'Storage', 'PSU']
const CATEGORY_COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']
const UNKNOWN_CATEGORY_COLOR = '#898781' // หมวดหมู่นอกรายการ = เทากลาง ไม่แย่งสีของหมวดที่มีอยู่

function categoryColor(name) {
  const i = CATEGORY_ORDER.indexOf(name)
  return i === -1 ? UNKNOWN_CATEGORY_COLOR : CATEGORY_COLORS[i]
}

const STATUS_COLORS = { Pending: '#fab219', Approved: '#0ca30c', Rejected: '#d03b3b' }

const SORT_COLUMNS = {
  branch: { label: 'สาขา', getValue: (r) => r.branch_name ?? '' },
  category: { label: 'หมวดหมู่', getValue: (r) => r.category },
  model: { label: 'ยี่ห้อ / รุ่น', getValue: (r) => `${r.brand} ${r.model}` },
  on_hand: { label: 'คงเหลือ', getValue: (r) => r.on_hand },
  reorder_point: { label: 'จุดสั่งซื้อ', getValue: (r) => r.reorder_point ?? -1 },
}

export default function AdminDashboard() {
  const [stock, setStock] = useState([])
  const [products, setProducts] = useState([])
  const [pendingPRs, setPendingPRs] = useState([])
  const [allPRs, setAllPRs] = useState([])
  const [branches, setBranches] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('branch')
  const [sortDir, setSortDir] = useState('asc')
  const [detailSkuId, setDetailSkuId] = useState(null)

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

  const q = search.trim().toLowerCase()
  const visibleStock = stock
    .filter((r) => {
      if (!q) return true
      return (
        r.category.toLowerCase().includes(q) ||
        r.brand.toLowerCase().includes(q) ||
        r.model.toLowerCase().includes(q) ||
        (r.branch_name ?? '').toLowerCase().includes(q)
      )
    })
    .sort((a, b) => {
      const va = SORT_COLUMNS[sortKey].getValue(a)
      const vb = SORT_COLUMNS[sortKey].getValue(b)
      const cmp = typeof va === 'string' ? va.localeCompare(vb) : va - vb
      return sortDir === 'asc' ? cmp : -cmp
    })

  function toggleSort(key) {
    if (key === sortKey) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

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
        <ChartCard
          title="สต็อกคงเหลือตามหมวดหมู่"
          data={stockByCategory}
          colors={stockByCategory.map((row) => categoryColor(row.name))}
        />
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
        <>
          <div className="flex items-center justify-between mb-3">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="ค้นหาสาขา / หมวดหมู่ / ยี่ห้อ / รุ่น..."
              className="w-full max-w-sm rounded-lg border border-ink-border bg-ink-surface px-3 py-2 text-sm text-ink-text placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-ink-accent/40"
            />
            <p className="text-xs text-ink-muted ml-3 whitespace-nowrap">
              {visibleStock.length} / {stock.length} รายการ
            </p>
          </div>
          <div className="bg-ink-surface border border-ink-border rounded-xl overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-ink-muted">
                <tr>
                  {Object.entries(SORT_COLUMNS).map(([key, col]) => (
                    <SortableHeader
                      key={key}
                      label={col.label}
                      active={sortKey === key}
                      dir={sortDir}
                      align={key === 'on_hand' || key === 'reorder_point' ? 'right' : 'left'}
                      onClick={() => toggleSort(key)}
                    />
                  ))}
                </tr>
              </thead>
              <tbody>
                {visibleStock.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-ink-muted">
                      ไม่พบรายการที่ตรงกับ "{search}"
                    </td>
                  </tr>
                ) : (
                  visibleStock.map((row, i) => {
                    const low = row.reorder_point != null && row.on_hand <= row.reorder_point
                    return (
                      <tr
                        key={`${row.sku_id}-${row.branch_id}-${i}`}
                        onClick={() => setDetailSkuId(row.sku_id)}
                        title="คลิกเพื่อดูรายละเอียดสินค้า"
                        className={`border-t border-ink-border cursor-pointer hover:bg-ink-accentSoft ${
                          low ? 'bg-[#fdf2f2]' : ''
                        }`}
                      >
                        <td className="px-4 py-3 text-ink-text">{row.branch_name}</td>
                        <td className="px-4 py-3 text-ink-muted">{row.category}</td>
                        <td className="px-4 py-3 text-ink-accent underline decoration-dotted underline-offset-2">
                          {row.brand} {row.model}
                        </td>
                        <td className="px-4 py-3 text-right font-medium text-ink-text">{row.on_hand}</td>
                        <td className="px-4 py-3 text-right text-ink-muted">{row.reorder_point ?? '—'}</td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {detailSkuId != null && (
        <ProductDetailModal skuId={detailSkuId} onClose={() => setDetailSkuId(null)} />
      )}
    </div>
  )
}

function SortableHeader({ label, active, dir, align, onClick }) {
  return (
    <th
      onClick={onClick}
      className={`px-4 py-3 font-medium cursor-pointer select-none hover:text-ink-text ${
        align === 'right' ? 'text-right' : 'text-left'
      }`}
    >
      <span className={align === 'right' ? 'inline-flex flex-row-reverse items-center gap-1' : 'inline-flex items-center gap-1'}>
        {label}
        <span className={`text-[10px] ${active ? 'text-ink-accent' : 'text-ink-border'}`}>
          {active ? (dir === 'asc' ? '▲' : '▼') : '▲'}
        </span>
      </span>
    </th>
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
