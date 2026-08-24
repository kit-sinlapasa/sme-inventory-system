import { useCallback, useEffect, useState } from 'react'
import client from '../../api/client'
import ProductDetailModal from '../../components/ProductDetailModal'
import SortableHeader, { compareValues } from '../../components/SortableHeader'
import {
  ChartCard,
  DailySalesChart,
  SellThroughChart,
  StockAgingChart,
  TopProductsChart,
  WeekdaySalesChart,
} from '../../components/dashboard/charts'
import {
  BranchComparisonTable,
  KpiTile,
  PendingRequestTable,
  RangePicker,
  StockoutTable,
  TableCard,
} from '../../components/dashboard/panels'

/**
 * FR-003, FR-014 — หน้าภาพรวมของสำนักงานใหญ่
 *
 * CR-013 — ออกแบบใหม่ทั้งหน้า จากเดิมที่เป็น "กราฟสต็อกคงเหลือตามหมวดหมู่"
 * ซึ่งตอบได้แค่ว่าตอนนี้มีของหมวดไหนเยอะ แต่ไม่ได้ช่วยตัดสินใจอะไรเลย:
 * ไม่รู้ว่าขายดีขึ้นหรือแย่ลง ไม่รู้ว่าอะไรกำลังจะหมด ไม่รู้ว่าเงินจมอยู่กับอะไร
 *
 * หน้าใหม่ตอบคำถามที่ใช้ตัดสินใจได้จริง 5 ข้อ:
 *   1. ยอดขายเป็นอย่างไรเทียบกับช่วงก่อน และสาขาไหนขับเคลื่อนยอด  -> กราฟเส้นรายวัน
 *   2. อะไรขายดี (ควรสต็อกเพิ่ม)                                  -> แท่งสินค้าขายดี
 *   3. เงินจมอยู่กับของเก่าแค่ไหน                                  -> แท่งอายุสต็อก
 *   4. สาขาไหนบริหารสต็อกได้ดี (เทียบข้ามขนาดสาขาได้)              -> แท่งอัตราระบาย
 *   5. ควรจัดคนเยอะวันไหน                                        -> แท่งรายวันในสัปดาห์
 *
 * ⚠️ ไม่มีกราฟใดแสดงยอดเงิน/กำไร เพราะฐานข้อมูลไม่มีฟิลด์ราคา — จะทำได้ต้องกุตัวเลขขึ้นมา
 * ซึ่งทำให้ทั้ง dashboard เชื่อถือไม่ได้ (ดู CR-008 ที่ตัดสินใจแบบเดียวกันไว้แล้ว)
 */

const SORT_COLUMNS = {
  branch: { label: 'สาขา', getValue: (r) => r.branch_name ?? '' },
  category: { label: 'หมวดหมู่', getValue: (r) => r.category },
  model: { label: 'ยี่ห้อ / รุ่น', getValue: (r) => `${r.brand} ${r.model}` },
  on_hand: { label: 'คงเหลือ', getValue: (r) => r.on_hand },
  reorder_point: { label: 'จุดสั่งซื้อ', getValue: (r) => r.reorder_point ?? -1 },
}

function pctChange(now, prev) {
  if (!prev) return null // ไม่มีฐานให้เทียบ = ไม่แสดง % ดีกว่าแสดง "เพิ่มขึ้น ∞%"
  return Math.round(((now - prev) / prev) * 100)
}

export default function AdminDashboard() {
  const [days, setDays] = useState(30)
  const [branchFilter, setBranchFilter] = useState('') // '' = ทุกสาขา (scope ที่ server)
  const [hiddenBranches, setHiddenBranches] = useState([]) // ซ่อนเส้นในกราฟเท่านั้น
  const [data, setData] = useState(null)
  const [stock, setStock] = useState([])
  const [branches, setBranches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('branch')
  const [sortDir, setSortDir] = useState('asc')
  const [detailSkuId, setDetailSkuId] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const scope = branchFilter ? `&branch_id=${branchFilter}` : ''
      const agingUrl = branchFilter ? `/reports/stock-aging?branch_id=${branchFilter}` : '/reports/stock-aging'
      const [summary, daily, top, aging, perf, weekday, risk, pending, stockRes, branchRes] =
        await Promise.all([
          client.get(`/reports/summary?days=${days}${scope}`),
          client.get(`/reports/daily-sales?days=${days}${scope}`),
          client.get(`/reports/top-products?days=${days}&limit=10${scope}`),
          client.get(agingUrl),
          client.get(`/reports/branch-performance?days=${days}`),
          client.get(`/reports/weekday-sales?days=${days}${scope}`),
          client.get(`/reports/stockout-risk?days=${days}&limit=15${scope}`),
          client.get(`/reports/pending-requests?limit=10${scope}`),
          client.get('/stock'),
          client.get('/branches'),
        ])
      setData({
        summary: summary.data,
        daily: daily.data,
        top: top.data,
        aging: aging.data,
        perf: perf.data,
        weekday: weekday.data,
        risk: risk.data,
        pending: pending.data,
      })
      setStock(stockRes.data)
      setBranches(branchRes.data)
    } catch (err) {
      setError('โหลดข้อมูลสรุปไม่สำเร็จ')
    } finally {
      setLoading(false)
    }
  }, [days, branchFilter])

  useEffect(() => {
    load()
  }, [load])

  const q = search.trim().toLowerCase()
  const visibleStock = stock
    .filter((r) => (branchFilter ? r.branch_id === Number(branchFilter) : true))
    .filter((r) => {
      if (!q) return true
      return (
        r.category.toLowerCase().includes(q) ||
        r.brand.toLowerCase().includes(q) ||
        r.model.toLowerCase().includes(q) ||
        (r.branch_name ?? '').toLowerCase().includes(q)
      )
    })
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

  function toggleBranchLine(name) {
    setHiddenBranches((prev) => (prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]))
  }

  const branchNames = branches.map((b) => b.name)
  const s = data?.summary

  return (
    <div className="-m-6 p-6 bg-ink-bg min-h-[calc(100vh-57px)]">
      <div className="flex items-end justify-between mb-5 flex-wrap gap-3">
        <div>
          <h1 className="rd-title">ภาพรวมธุรกิจ</h1>
          <p className="text-xs text-ink-muted mt-1">
            ตัวเลขทั้งหมดคิดตามวันเวลาไทย · ช่วงที่เลือกมีผลกับทุกกราฟยกเว้น "อายุสต็อก"
            ซึ่งเป็นภาพ ณ ปัจจุบัน
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {/* ตัวกรองสาขานี้ส่งไปกรองที่ server จริง ต่างจากการคลิก legend ในกราฟเส้น
              ซึ่งแค่ซ่อนเส้นไว้ดูเปรียบเทียบชั่วคราว */}
          <select
            value={branchFilter}
            onChange={(e) => setBranchFilter(e.target.value)}
            className="rd-input w-auto py-1.5"
          >
            <option value="">ทุกสาขา</option>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
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
            {/* ใบเด่นใบเดียวของหน้า — ยอดขายคือตัวเลขที่คนเปิดหน้านี้มาดูก่อนเสมอ
                ที่เหลือเป็นการ์ดพื้นอ่อน ถ้าทำเด่นหมดก็เท่ากับไม่มีใบไหนเด่น */}
            <KpiTile
              hero
              icon="sales"
              label={`ขายได้ใน ${days} วัน`}
              value={s.sold_in_period}
              delta={pctChange(s.sold_in_period, s.sold_prev_period)}
              sub={`ช่วงก่อนหน้า ${s.sold_prev_period} ชิ้น`}
            />
            <KpiTile icon="stock" label="คงเหลือรวม" value={s.on_hand} sub="ชิ้นที่ยังไม่ถูกขาย" />
            <KpiTile
              icon="alert"
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
              icon="clock"
              label="ค้างสต็อกเกิน 180 วัน"
              value={s.dead_stock_items}
              tone={s.dead_stock_items > 0 ? 'warning' : null}
              sub="ชิ้นที่ยังไม่ขยับตั้งแต่รับเข้า"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 mb-4">
            <ChartCard
              title="ยอดขายรายวัน"
              hint="คลิกชื่อสาขาด้านล่างกราฟเพื่อซ่อน/แสดงเส้นนั้น"
            >
              <DailySalesChart
                data={data.daily}
                branchNames={branchFilter ? branchNames.filter((n) => data.daily.some((d) => d.branch_name === n)) : branchNames}
                hidden={hiddenBranches}
                onToggleBranch={toggleBranchLine}
              />
            </ChartCard>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <ChartCard title="สินค้าขายดี 10 อันดับ" hint="คลิกแท่งเพื่อดูรายละเอียดสินค้า">
              <TopProductsChart data={data.top} onSelect={setDetailSkuId} />
            </ChartCard>
            <ChartCard
              title="อัตราการระบายสต็อกรายสาขา"
              hint="ขายได้ ÷ (ขายได้ + คงเหลือ) — เทียบข้ามขนาดสาขาได้"
            >
              <SellThroughChart data={data.perf} branchNames={branchNames} />
            </ChartCard>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
            <ChartCard title="อายุของสินค้าที่ยังค้างสต็อก" hint="ยิ่งเข้มยิ่งเก่า — เงินจมอยู่ตรงนั้น">
              <StockAgingChart data={data.aging} />
            </ChartCard>
            <ChartCard title="ยอดขายตามวันในสัปดาห์" hint="ใช้วางแผนกำลังคนหน้าร้าน">
              <WeekdaySalesChart data={data.weekday} />
            </ChartCard>
          </div>

          <div className="grid grid-cols-1 gap-4 mb-4">
            <TableCard
              title="รายการเสี่ยงของขาด"
              hint="เรียงตามจำนวนวันที่เหลือก่อนของหมด ไม่ใช่ยอดคงเหลือ — เหลือน้อยไม่เท่ากับเสี่ยง"
              isEmpty={data.risk.length === 0}
              empty="ไม่มีรายการที่เสี่ยงของขาดในช่วงนี้"
            >
              <StockoutTable rows={data.risk} showBranch={!branchFilter} onSelectSku={setDetailSkuId} />
            </TableCard>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
            <TableCard
              title={`คำขอสั่งซื้อค้างพิจารณา (${s.pending_requests})`}
              hint="เรียงจากที่ค้างนานที่สุด"
              isEmpty={data.pending.length === 0}
              empty="ไม่มีคำขอค้างพิจารณา"
            >
              <PendingRequestTable rows={data.pending} showBranch={!branchFilter} />
            </TableCard>
            <TableCard title="เทียบผลงานรายสาขา" isEmpty={data.perf.length === 0} empty="ยังไม่มีข้อมูลสาขา">
              <BranchComparisonTable rows={data.perf} days={days} />
            </TableCard>
          </div>
        </>
      )}

      {/* ตารางสต็อกเต็ม — ยังคงไว้เพราะเป็นมุมมองรายการที่ผู้ใช้ใช้ค้นหาของจริงประจำวัน
          ส่วนด้านบนคือมุมมองสรุปไว้ตัดสินใจ คนละหน้าที่กัน */}
      <div className="flex items-end justify-between mb-3 flex-wrap gap-2">
        <h2 className="rd-title">สต็อกรวมทุกสาขา</h2>
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="ค้นหาสาขา / หมวดหมู่ / ยี่ห้อ / รุ่น..."
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
                <td colSpan={5} className="px-4 py-8 text-center text-ink-muted">
                  ไม่พบรายการที่ตรงกับเงื่อนไข
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
                    className={`rd-tr cursor-pointer hover:bg-ink-accentSoft ${low ? 'bg-[#fdf2f2]' : ''}`}
                  >
                    <td className="rd-td">{row.branch_name}</td>
                    <td className="rd-td text-ink-muted">{row.category}</td>
                    <td className="rd-td text-ink-accent underline decoration-dotted underline-offset-2">
                      {row.brand} {row.model}
                    </td>
                    <td className="rd-td text-right font-medium whitespace-nowrap">
                      {row.on_hand}
                      {/* เตือนเป็นข้อความด้วย ไม่ใช่แค่พื้นแถวสีแดง — สีอย่างเดียวคนตาบอดสี
                          หรือคนพิมพ์เอกสารขาวดำจะไม่เห็น */}
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
