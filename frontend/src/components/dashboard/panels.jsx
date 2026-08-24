/**
 * CR-013 — ชิ้นส่วนที่ไม่ใช่กราฟของ dashboard: KPI, ตัวเลือกช่วงเวลา, ตารางสรุป
 *
 * ที่แยกออกมาเป็นตาราง ไม่ทำเป็นกราฟ เพราะแต่ละแถวมีมากกว่า 4 ค่าที่ต้องอ่านพร้อมกัน
 * (คงเหลือ, จุดสั่งซื้อ, ความเร็วขาย, จะหมดในกี่วัน) — เกินกว่าที่กราฟจะสื่อได้ครบ
 */

export const RANGES = [
  { days: 7, label: '7 วัน' },
  { days: 30, label: '30 วัน' },
  { days: 90, label: '90 วัน' },
]

export function RangePicker({ value, onChange }) {
  return (
    <div className="inline-flex rounded-lg border border-ink-border overflow-hidden">
      {RANGES.map((r) => (
        <button
          key={r.days}
          onClick={() => onChange(r.days)}
          aria-pressed={value === r.days}
          className={`px-3 py-1.5 text-sm transition ${
            value === r.days
              ? 'bg-ink-accentSoft text-ink-accent font-medium'
              : 'text-ink-muted hover:text-ink-text'
          }`}
        >
          {r.label}
        </button>
      ))}
    </div>
  )
}

/**
 * KPI tile — ตัวเลขเดียวไม่ต้องมีกราฟ (dataviz: "sometimes the answer is not a chart")
 * delta แสดงเฉพาะเมื่อมีข้อมูลช่วงก่อนหน้าให้เทียบจริง ไม่แต่งตัวเลขเทรนด์ขึ้นมาเอง
 */
export function KpiTile({ label, value, sub, delta, tone, invertDelta }) {
  const toneClass =
    tone === 'critical' ? 'text-[#d03b3b]' : tone === 'warning' ? 'text-[#a3690f]' : 'text-ink-text'

  let deltaNode = null
  if (delta != null && Number.isFinite(delta)) {
    // invertDelta = ตัวเลขที่ "เพิ่มขึ้นแล้วแย่ลง" เช่นของค้างสต็อก
    const good = invertDelta ? delta < 0 : delta > 0
    const color = delta === 0 ? 'text-ink-muted' : good ? 'text-[#0a7d0a]' : 'text-[#d03b3b]'
    const arrow = delta === 0 ? '→' : delta > 0 ? '▲' : '▼'
    deltaNode = (
      <span className={`text-xs ${color}`}>
        {arrow} {Math.abs(delta)}%
      </span>
    )
  }

  return (
    <div className="rd-card p-4">
      <p className="text-xs text-ink-muted mb-1">{label}</p>
      <div className="flex items-baseline gap-2 flex-wrap">
        <p className={`text-2xl font-semibold ${toneClass}`}>{value}</p>
        {deltaNode}
      </div>
      {sub && <p className="text-xs text-ink-muted mt-1">{sub}</p>}
    </div>
  )
}

export function TableCard({ title, hint, children, empty, isEmpty }) {
  return (
    <div className="rd-card overflow-hidden">
      <div className="px-4 pt-4 pb-3">
        <p className="text-sm font-medium text-ink-text">{title}</p>
        {hint && <p className="text-xs text-ink-muted mt-0.5">{hint}</p>}
      </div>
      {isEmpty ? (
        <p className="text-ink-muted text-sm px-4 pb-6 pt-2 text-center">{empty}</p>
      ) : (
        <div className="overflow-x-auto">{children}</div>
      )}
    </div>
  )
}

/**
 * ตาราง 1 — รายการเสี่ยงของขาด
 *
 * เรียงตาม "จะหมดในกี่วัน" ไม่ใช่ยอดคงเหลือ เพราะเหลือน้อยไม่เท่ากับเสี่ยง:
 * เหลือ 2 ชิ้นแต่ขายเดือนละชิ้นคือปลอดภัย ส่วนเหลือ 8 ชิ้นแต่ขายวันละ 2 ชิ้นคือใกล้หมดจริง
 */
export function StockoutTable({ rows, showBranch, onSelectSku, onRequest }) {
  return (
    <table className="rd-table">
      <thead>
        <tr>
          {showBranch && <th className="rd-th">สาขา</th>}
          <th className="rd-th">สินค้า</th>
          <th className="rd-th text-right">คงเหลือ</th>
          <th className="rd-th text-right">ขาย/วัน</th>
          <th className="rd-th text-right">หมดในอีก</th>
          {onRequest && <th className="rd-th" />}
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => {
          const urgent = r.days_left != null && r.days_left <= 7
          return (
            <tr
              key={`${r.sku_id}-${r.branch_id}`}
              className="rd-tr cursor-pointer hover:bg-ink-accentSoft"
              onClick={() => onSelectSku?.(r.sku_id)}
              title="คลิกเพื่อดูรายละเอียดสินค้า"
            >
              {showBranch && <td className="rd-td text-ink-muted whitespace-nowrap">{r.branch_name}</td>}
              <td className="rd-td">
                <span className="text-ink-muted text-xs mr-1">{r.category}</span>
                <span className="text-ink-accent underline decoration-dotted underline-offset-2">
                  {r.brand} {r.model}
                </span>
              </td>
              <td className="rd-td text-right font-medium whitespace-nowrap">
                {r.on_hand}
                {r.reorder_point ? <span className="text-ink-muted text-xs"> / {r.reorder_point}</span> : null}
              </td>
              <td className="rd-td text-right text-ink-muted">{r.daily_velocity.toFixed(2)}</td>
              <td className={`rd-td text-right whitespace-nowrap ${urgent ? 'text-[#d03b3b] font-medium' : ''}`}>
                {r.days_left == null ? (
                  // ไม่เคยขายในช่วงที่ดู จึงประมาณวันหมดไม่ได้ — ต่างจาก "หมดวันนี้"
                  <span className="text-ink-muted text-xs">ไม่มียอดขาย</span>
                ) : (
                  <>
                    {r.days_left === 0 ? 'หมดแล้ว' : `${r.days_left} วัน`}
                    {urgent && r.days_left > 0 && <span className="ml-1 text-xs">⚠</span>}
                  </>
                )}
              </td>
              {onRequest && (
                <td className="rd-td text-right">
                  <button
                    onClick={(e) => {
                      e.stopPropagation() // ไม่ให้ไปเปิด modal รายละเอียดสินค้าแทน
                      onRequest(r)
                    }}
                    className="text-xs text-ink-accent hover:underline whitespace-nowrap"
                  >
                    ขอสั่งซื้อ
                  </button>
                </td>
              )}
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

/** ตาราง 2 — คำขอสั่งซื้อที่ค้างพิจารณา เรียงจากที่ค้างนานสุด */
export function PendingRequestTable({ rows, showBranch }) {
  return (
    <table className="rd-table">
      <thead>
        <tr>
          {showBranch && <th className="rd-th">สาขา</th>}
          <th className="rd-th">สินค้า</th>
          <th className="rd-th text-right">จำนวน</th>
          <th className="rd-th text-right">ค้างมา</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => {
          const stale = r.age_days >= 14
          return (
            <tr key={r.id} className="rd-tr">
              {showBranch && <td className="rd-td text-ink-muted whitespace-nowrap">{r.branch_name}</td>}
              <td className="rd-td">
                <span className="text-ink-muted text-xs mr-1">{r.category}</span>
                {r.brand} {r.model}
              </td>
              <td className="rd-td text-right">{r.quantity}</td>
              <td className={`rd-td text-right whitespace-nowrap ${stale ? 'text-[#a3690f] font-medium' : 'text-ink-muted'}`}>
                {r.age_days} วัน
                {stale && <span className="ml-1 text-xs">⚠</span>}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

/** ตาราง 3 — เทียบสาขา (เฉพาะสำนักงานใหญ่) */
export function BranchComparisonTable({ rows, days }) {
  return (
    <table className="rd-table">
      <thead>
        <tr>
          <th className="rd-th">สาขา</th>
          <th className="rd-th text-right">ขายได้ ({days} วัน)</th>
          <th className="rd-th text-right">คงเหลือ</th>
          <th className="rd-th text-right">อัตราระบาย</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.branch_id} className="rd-tr">
            <td className="rd-td">{r.branch_name}</td>
            <td className="rd-td text-right font-medium">{r.sold}</td>
            <td className="rd-td text-right text-ink-muted">{r.on_hand}</td>
            <td className="rd-td text-right">
              {/* คำนวณไม่ได้ต้องแสดงว่าคำนวณไม่ได้ ไม่ใช่แสดง 0% ซึ่งอ่านว่า "ขายไม่ออกเลย" */}
              {r.sell_through == null ? (
                <span className="text-ink-muted text-xs">ไม่มีข้อมูล</span>
              ) : (
                `${Math.round(r.sell_through * 1000) / 10}%`
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
