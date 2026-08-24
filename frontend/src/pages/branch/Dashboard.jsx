import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../../api/client'
import ProductDetailModal from '../../components/ProductDetailModal'
import SortableHeader, { compareValues } from '../../components/SortableHeader'
import {
  ChartCard,
  DailySalesChart,
  StockAgingChart,
  TopProductsChart,
  WeekdaySalesChart,
} from '../../components/dashboard/charts'
import {
  KpiTile,
  PendingRequestTable,
  RangePicker,
  StockoutTable,
  TableCard,
} from '../../components/dashboard/panels'

/**
 * FR-003, FR-008, FR-014 — หน้าภาพรวมของสาขา
 *
 * CR-013 — ชุดเดียวกับหน้าสำนักงานใหญ่แต่ตัดส่วนที่สาขาไม่ควรเห็นออก:
 *   - ไม่มีกราฟ "อัตราระบายรายสาขา" และตารางเทียบสาขา เพราะสาขาไม่ควรเห็นตัวเลขสาขาอื่น
 *   - ไม่มีตัวกรองสาขา เพราะ server ล็อกไว้ที่สาขาตัวเองอยู่แล้ว (NFR-SEC-02)
 *     การใส่ dropdown ให้เลือกทั้งที่เลือกไม่ได้จริงจะทำให้ผู้ใช้เข้าใจผิด
 *
 * ส่วนที่สาขาได้เพิ่มมาจากหน้าสำนักงานใหญ่คือปุ่ม "ขอสั่งซื้อ" ในตารางของใกล้หมด
 * เพราะสาขาคือคนที่ลงมือทำเรื่องนี้จริง ไม่ใช่สำนักงานใหญ่
 */

const SORT_COLUMNS = {
  category: { label: 'หมวดหมู่', getValue: (r) => r.category },
  model: { label: 'ยี่ห้อ / รุ่น', getValue: (r) => `${r.brand} ${r.model}` },
  on_hand: { label: 'คงเหลือ', getValue: (r) => r.on_hand },
  reorder_point: { label: 'จุดสั่งซื้อ', getValue: (r) => r.reorder_point ?? -1 },
}

function pctChange(now, prev) {
  if (!prev) return null
  return Math.round(((now - prev) / prev) * 100)
}

export default function BranchDashboard() {
  const navigate = useNavigate()
  const branchName = localStorage.getItem('branch_name') || 'สาขาของฉัน'

  const [days, setDays] = useState(30)
  const [data, setData] = useState(null)
  const [stock, setStock] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('category')
  const [sortDir, setSortDir] = useState('asc')
  const [detailSkuId, setDetailSkuId] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [summary, daily, top, aging, weekday, risk, pending, stockRes] = await Promise.all([
        client.get(`/reports/summary?days=${days}`),
        client.get(`/reports/daily-sales?days=${days}`),
        client.get(`/reports/top-products?days=${days}&limit=10`),
        client.get('/reports/stock-aging'),
        client.get(`/reports/weekday-sales?days=${days}`),
        client.get(`/reports/stockout-risk?days=${days}&limit=15`),
        client.get('/reports/pending-requests?limit=10'),
        client.get('/stock'),
      ])
      setData({
        summary: summary.data,
        daily: daily.data,
        top: top.data,
        aging: aging.data,
        weekday: weekday.data,
        risk: risk.data,
        pending: pending.data,
      })
      setStock(stockRes.data)
    } catch (err) {
      setError('โหลดข้อมูลสรุปไม่สำเร็จ')
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    load()
  }, [load])

  const q = search.trim().toLowerCase()
  const visibleStock = stock
    .filter(
      (r) =>
        !q ||
        r.category.toLowerCase().includes(q) ||
        r.brand.toLowerCase().includes(q) ||
        r.model.toLowerCase().includes(q),
    )
    .sort((a, b) =>
      compareValues(SORT_COLUMNS[sortKey].getValue(a), SORT_COLUMNS[sortKey].getValue(b), sortDir),
    )

  function toggleSort(key) {
    if (key === sortKey) setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  // ส่ง sku ไปให้หน้าคำขอสั่งซื้อกรอกไว้ให้ล่วงหน้า — ผู้ใช้เพิ่งเห็นว่าของชิ้นนี้กำลังจะหมด
  // ไม่ควรต้องไปไล่หาในรายการสินค้า 60 รายการอีกรอบ
  function requestRestock(row) {
    navigate('/branch/requests', { state: { prefillSkuId: row.sku_id } })
  }

  const s = data?.summary

  return (
    <div className="-m-6 p-6 bg-ink-bg min-h-[calc(100vh-57px)]">
      <div className="flex items-end justify-between mb-5 flex-wrap gap-3">
        <div>
          <h1 className="rd-title">ภาพรวม{branchName}</h1>
          <p className="text-xs text-ink-muted mt-1">
            แสดงเฉพาะข้อมูลของสาขานี้ · ตัวเลขคิดตามวันเวลาไทย
          </p>
        </div>
        <div className="flex items-center gap-2">
          <RangePicker value={days} onChange={setDays} />
          <button onClick={load} className="rd-link text-sm">
            รีเฟรช
          </button>
        </div>
      </div>

      {error && <p className="text-[#d03b3b] text-sm mb-4">{error}</p>}
      {loading && !data && <p className="text-ink-muted">กำลังโหลด...</p>}

      {data && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
            <KpiTile
              label={`ขายได้ใน ${days} วัน`}
              value={s.sold_in_period}
              delta={pctChange(s.sold_in_period, s.sold_prev_period)}
              sub={`ช่วงก่อนหน้า ${s.sold_prev_period} ชิ้น`}
            />
            <KpiTile label="คงเหลือรวม" value={s.on_hand} sub="ชิ้นที่ยังไม่ถูกขาย" />
            <KpiTile
              label="รายการใกล้หมด"
              value={s.low_stock_skus}
              tone={s.low_stock_skus > 0 ? 'critical' : null}
              /* บอกให้ชัดว่าเลขนี้รวมของที่หมดเกลี้ยงแล้วด้วย เพราะตารางสต็อกด้านล่าง
                 แสดงเฉพาะรายการที่ยังมีของเหลืออยู่ แถวแดงในตารางจึงน้อยกว่าเลขนี้เสมอ */
              sub={
                s.out_of_stock_skus > 0
                  ? `ต่ำกว่าหรือเท่าจุดสั่งซื้อ (หมดแล้ว ${s.out_of_stock_skus} รายการ)`
                  : 'ต่ำกว่าหรือเท่าจุดสั่งซื้อ'
              }
            />
            <KpiTile
              label="ค้างสต็อกเกิน 180 วัน"
              value={s.dead_stock_items}
              tone={s.dead_stock_items > 0 ? 'warning' : null}
              sub="ชิ้นที่ยังไม่ขยับตั้งแต่รับเข้า"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 mb-4">
            <ChartCard title="ยอดขายรายวันของสาขา">
              {/* สาขาเดียว = เส้นเดียว จึงไม่ต้องมี legend (หัวข้อกราฟบอกอยู่แล้วว่าเส้นนี้คืออะไร) */}
              <DailySalesChart
                data={data.daily}
                branchNames={[...new Set(data.daily.map((d) => d.branch_name))]}
                hidden={[]}
                onToggleBranch={() => {}}
              />
            </ChartCard>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <ChartCard title="สินค้าขายดี 10 อันดับของสาขา" hint="คลิกแท่งเพื่อดูรายละเอียดสินค้า">
              <TopProductsChart data={data.top} onSelect={setDetailSkuId} />
            </ChartCard>
            <ChartCard title="ยอดขายตามวันในสัปดาห์" hint="ใช้วางแผนกำลังคนหน้าร้าน">
              <WeekdaySalesChart data={data.weekday} />
            </ChartCard>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
            <ChartCard title="อายุของสินค้าที่ยังค้างสต็อก" hint="ยิ่งเข้มยิ่งเก่า — เงินจมอยู่ตรงนั้น">
              <StockAgingChart data={data.aging} />
            </ChartCard>
            <TableCard
              title={`คำขอสั่งซื้อค้างพิจารณา (${s.pending_requests})`}
              hint="คำขอของสาขานี้ที่สำนักงานใหญ่ยังไม่ตัดสินใจ"
              isEmpty={data.pending.length === 0}
              empty="ไม่มีคำขอค้างพิจารณา"
            >
              <PendingRequestTable rows={data.pending} showBranch={false} />
            </TableCard>
          </div>

          <div className="grid grid-cols-1 gap-4 mb-6">
            <TableCard
              title="รายการเสี่ยงของขาด"
              hint="เรียงตามจำนวนวันที่เหลือก่อนของหมด ไม่ใช่ยอดคงเหลือ — กด 'ขอสั่งซื้อ' เพื่อสร้างคำขอทันที"
              isEmpty={data.risk.length === 0}
              empty="ไม่มีรายการที่เสี่ยงของขาดในช่วงนี้"
            >
              <StockoutTable
                rows={data.risk}
                showBranch={false}
                onSelectSku={setDetailSkuId}
                onRequest={requestRestock}
              />
            </TableCard>
          </div>
        </>
      )}

      <div className="flex items-end justify-between mb-3 flex-wrap gap-2">
        <h2 className="rd-title">สต็อกทั้งหมดของสาขา</h2>
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="ค้นหาหมวดหมู่ / ยี่ห้อ / รุ่น..."
            className="rd-input max-w-sm"
          />
          <p className="text-xs text-ink-muted whitespace-nowrap">
            {visibleStock.length} / {stock.length} รายการ
          </p>
        </div>
      </div>
      <div className="rd-card overflow-x-auto">
        <table className="rd-table">
          <thead>
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
                <td colSpan={4} className="px-4 py-8 text-center text-ink-muted">
                  {stock.length === 0 ? 'ยังไม่มีสินค้าในสต็อก' : 'ไม่พบรายการที่ตรงกับเงื่อนไข'}
                </td>
              </tr>
            ) : (
              visibleStock.map((row) => {
                const low = row.reorder_point != null && row.on_hand <= row.reorder_point
                return (
                  <tr
                    key={row.sku_id}
                    onClick={() => setDetailSkuId(row.sku_id)}
                    title="คลิกเพื่อดูรายละเอียดสินค้า"
                    className={`rd-tr cursor-pointer hover:bg-ink-accentSoft ${low ? 'bg-[#fdf2f2]' : ''}`}
                  >
                    <td className="rd-td text-ink-muted">{row.category}</td>
                    <td className="rd-td text-ink-accent underline decoration-dotted underline-offset-2">
                      {row.brand} {row.model}
                    </td>
                    <td className="rd-td text-right font-medium">
                      {row.on_hand}
                      {low && <span className="ml-2 text-[#d03b3b] text-xs">⚠ ใกล้หมด</span>}
                    </td>
                    <td className="rd-td text-right text-ink-muted">{row.reorder_point ?? '—'}</td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {detailSkuId != null && (
        <ProductDetailModal skuId={detailSkuId} onClose={() => setDetailSkuId(null)} />
      )}
    </div>
  )
}
