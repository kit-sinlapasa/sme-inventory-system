/**
 * CR-013 — ชิ้นส่วนที่ไม่ใช่กราฟของ dashboard: KPI, ตัวเลือกช่วงเวลา, ตารางสรุป
 *
 * ที่แยกออกมาเป็นตาราง ไม่ทำเป็นกราฟ เพราะแต่ละแถวมีมากกว่า 4 ค่าที่ต้องอ่านพร้อมกัน
 * (คงเหลือ, จุดสั่งซื้อ, ความเร็วขาย, จะหมดในกี่วัน) — เกินกว่าที่กราฟจะสื่อได้ครบ
 */
import { HERO_GRADIENT, TILE_ICON_BG } from './palette'

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
 * ไอคอนประจำการ์ด — ช่วยแยกการ์ดด้วยรูปทรง ไม่ใช่แค่ข้อความ
 * ใช้ currentColor เพื่อให้เปลี่ยนสีตามพื้นการ์ดได้ (ขาวบน gradient / ฟ้าบนพื้นอ่อน)
 */
const ICONS = {
  sales: 'M3 17l6-6 4 4 7-7M21 8v5h-5', // เส้นแนวโน้มขึ้น
  stock: 'M3 7l9-4 9 4-9 4-9-4zm0 5l9 4 9-4M3 17l9 4 9-4', // กล่องซ้อน
  alert: 'M12 3l9 16H3l9-16zm0 6v4m0 3v.5', // สามเหลี่ยมเตือน
  clock: 'M12 21a9 9 0 100-18 9 9 0 000 18zm0-14v5l3 2', // นาฬิกา
}

function TileIcon({ name, className }) {
  const d = ICONS[name]
  if (!d) return null
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
         strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <path d={d} />
    </svg>
  )
}

/**
 * KPI tile — ตัวเลขเดียวไม่ต้องมีกราฟ (dataviz: "sometimes the answer is not a chart")
 * delta แสดงเฉพาะเมื่อมีข้อมูลช่วงก่อนหน้าให้เทียบจริง ไม่แต่งตัวเลขเทรนด์ขึ้นมาเอง
 *
 * `hero` = การ์ดใบเด่นพื้น gradient (ดู HERO_GRADIENT ใน palette.js)
 * ใส่ใบเดียวต่อหน้าเท่านั้น — ถ้าทุกใบเด่นก็เท่ากับไม่มีใบไหนเด่น
 *
 * ข้อบังคับเรื่องตัวหนังสือบนพื้น gradient (วัดมาแล้ว ไม่ใช่ความรู้สึก):
 * ต้องเป็น **ขาวทึบ 100%** ทุกบรรทัด ขาวโปร่งแสง 90% เหลือ contrast 4.34:1 ซึ่งตก AA
 * จึงลดน้ำหนักด้วยขนาด/ความหนาแทน opacity · ป้าย delta ก็ใช้พื้นขาวทึบ + ตัวสีสถานะ
 * ไม่ใช่พื้นขาวจาง + ตัวขาว (แบบหลังวัดได้ 3.78:1 ตก AA เพราะพื้นจางไปกลืนกับตัวหนังสือ)
 */
export function KpiTile({ label, value, sub, delta, tone, invertDelta, hero, icon }) {
  const toneClass =
    tone === 'critical' ? 'text-[#d03b3b]' : tone === 'warning' ? 'text-[#a3690f]' : 'text-ink-text'

  let deltaNode = null
  if (delta != null && Number.isFinite(delta)) {
    // invertDelta = ตัวเลขที่ "เพิ่มขึ้นแล้วแย่ลง" เช่นของค้างสต็อก
    const good = invertDelta ? delta < 0 : delta > 0
    const hex = delta === 0 ? '#5f5f5f' : good ? '#0a7d0a' : '#d03b3b'
    // ทิศทางสื่อด้วยลูกศรด้วย ไม่ได้พึ่งสีอย่างเดียว (คนตาบอดสี/พิมพ์ขาวดำยังอ่านได้)
    const arrow = delta === 0 ? '→' : delta > 0 ? '▲' : '▼'
    deltaNode = hero ? (
      <span
        className="text-xs font-medium rounded-full bg-white px-2 py-0.5 whitespace-nowrap"
        style={{ color: hex }}
      >
        {arrow} {Math.abs(delta)}%
      </span>
    ) : (
      <span className="text-xs whitespace-nowrap" style={{ color: hex }}>
        {arrow} {Math.abs(delta)}%
      </span>
    )
  }

  if (hero) {
    return (
      <div className="rounded-xl p-4 relative overflow-hidden" style={{ background: HERO_GRADIENT }}>
        {icon && (
          <span className="absolute top-3 right-3 rounded-lg bg-white/25 p-1.5 text-white">
            <TileIcon name={icon} className="w-4 h-4" />
          </span>
        )}
        {/* ทุกบรรทัดเป็นขาวทึบ — แยกลำดับความสำคัญด้วยขนาดและความหนาแทนความโปร่งใส */}
        <p className="text-xs text-white font-medium mb-1 pr-10">{label}</p>
        <div className="flex items-baseline gap-2 flex-wrap">
          <p className="text-3xl font-semibold text-white">{value}</p>
          {deltaNode}
        </div>
        {sub && <p className="text-xs text-white mt-1">{sub}</p>}
      </div>
    )
  }

  return (
    <div className="rd-card p-4 relative">
      {icon && (
        <span
          className="absolute top-3 right-3 rounded-lg p-1.5 text-ink-accent"
          style={{ background: TILE_ICON_BG }}
        >
          <TileIcon name={icon} className="w-4 h-4" />
        </span>
      )}
      <p className="text-xs text-ink-muted mb-1 pr-10">{label}</p>
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
