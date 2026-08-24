import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { AGING_RAMP, AXIS, BRANCH_DASH, SINGLE_SERIES, TOOLTIP_STYLE, makeBranchColorScale } from './palette'

/**
 * CR-013 — กราฟของ dashboard เชิงวิเคราะห์
 *
 * ทุกกราฟรับข้อมูลที่ "สรุปมาจาก backend แล้ว" ไม่ได้รับรายการดิบมา group เอง
 * เพราะ endpoint รายการมี limit — ถ้าคำนวณฝั่ง client กราฟจะถูกคิดจากข้อมูลที่ถูกตัดไป
 * โดยหน้าจอยังเรนเดอร์ออกมาปกติ จับด้วยตาไม่ได้ (ดูเหตุผลเต็มใน routers/reports.py)
 */

export function ChartCard({ title, hint, children, right }) {
  return (
    <div className="rd-card p-4">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <p className="text-sm font-medium text-ink-text">{title}</p>
          {hint && <p className="text-xs text-ink-muted mt-0.5">{hint}</p>}
        </div>
        {right}
      </div>
      {children}
    </div>
  )
}

function Empty({ text = 'ยังไม่มีข้อมูลในช่วงเวลานี้' }) {
  return <p className="text-ink-muted text-sm py-12 text-center">{text}</p>
}

const thDate = (iso) =>
  new Date(iso).toLocaleDateString('th-TH', { day: 'numeric', month: 'short' })

/**
 * กราฟ 1 — ยอดขายรายวัน หนึ่งเส้นต่อหนึ่งสาขา
 *
 * เลือกเส้นเพราะข้อมูลเป็น "การเปลี่ยนแปลงตามเวลา" ซึ่งลำดับของแกน x มีความหมาย
 * (แท่งจะสื่อว่าแต่ละวันเป็นหมวดที่ไม่เกี่ยวกัน) · ไม่ใช้แกน y สองแกนเด็ดขาด
 *
 * คลิกที่ legend เพื่อซ่อน/แสดงสาขา — สีของสาขาที่เหลือต้องไม่เปลี่ยน
 */
export function DailySalesChart({ data, branchNames, hidden, onToggleBranch }) {
  const colorOf = makeBranchColorScale(branchNames)
  const series = [...branchNames].sort((a, b) => a.localeCompare(b, 'th'))

  // แปลง [{day, branch_name, qty}] เป็นแถวละวัน คอลัมน์ละสาขา ตามที่ recharts ต้องการ
  const byDay = new Map()
  for (const row of data) {
    if (!byDay.has(row.day)) byDay.set(row.day, { day: row.day })
    byDay.get(row.day)[row.branch_name] = row.qty
  }
  const rows = [...byDay.values()].sort((a, b) => a.day.localeCompare(b.day))
  const visible = series.filter((name) => !hidden.includes(name))

  if (rows.length === 0) return <Empty />

  return (
    <>
      <ResponsiveContainer width="100%" height={240}>
        <ComposedChart data={rows} margin={{ left: -20, right: 12, top: 4 }}>
          {/* เติมพื้นใต้เส้นแบบไล่จางเฉพาะตอนเหลือเส้นเดียว — ถ้าหลายเส้นซ้อนกัน
              พื้นจะทับกันจนอ่านเส้นไหนไม่ออก · การไล่จางนี้เป็นการตกแต่งแนวตั้ง
              ไม่ได้เข้ารหัสค่าอะไร ต่างจากการไล่สีข้ามเซกเมนต์ในกราฟวงกลม */}
          {visible.length === 1 && (
            <defs>
              <linearGradient id="dailyFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={colorOf(visible[0])} stopOpacity={0.28} />
                <stop offset="100%" stopColor={colorOf(visible[0])} stopOpacity={0} />
              </linearGradient>
            </defs>
          )}
          <CartesianGrid stroke={AXIS.grid} vertical={false} />
          <XAxis
            dataKey="day"
            tickFormatter={thDate}
            tick={{ fontSize: 11, fill: AXIS.tick }}
            axisLine={{ stroke: AXIS.grid }}
            tickLine={false}
            minTickGap={24}
          />
          <YAxis
            tick={{ fontSize: 11, fill: AXIS.tick }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            labelFormatter={(d) => new Date(d).toLocaleDateString('th-TH', { dateStyle: 'medium' })}
            formatter={(v, name) => [`${v} ชิ้น`, name]}
          />
          {visible.length === 1 && (
            <Area
              type="monotone"
              dataKey={visible[0]}
              stroke="none"
              fill="url(#dailyFill)"
              connectNulls
              legendType="none"
              tooltipType="none"
            />
          )}
          {visible.map((name) => (
            <Line
              key={name}
              type="monotone"
              dataKey={name}
              stroke={colorOf(name)}
              strokeDasharray={BRANCH_DASH[series.indexOf(name)] ?? undefined}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              connectNulls
            />
          ))}
        </ComposedChart>
      </ResponsiveContainer>

      {/* legend ต้องมีเสมอเมื่อมีมากกว่า 1 เส้น — ตัวตนของเส้นจะพึ่งสีอย่างเดียวไม่ได้
          จึงแสดงทั้งสีและลายเส้นในปุ่ม legend เหมือนที่วาดจริงในกราฟ */}
      {series.length > 1 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {series.map((name) => {
            const off = hidden.includes(name)
            return (
              <button
                key={name}
                onClick={() => onToggleBranch(name)}
                title={off ? 'คลิกเพื่อแสดงสาขานี้' : 'คลิกเพื่อซ่อนสาขานี้'}
                className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-lg border transition ${
                  off
                    ? 'border-ink-border text-ink-muted opacity-50'
                    : 'border-ink-border text-ink-text hover:bg-ink-accentSoft'
                }`}
              >
                <svg width="18" height="8" aria-hidden="true">
                  <line
                    x1="0" y1="4" x2="18" y2="4"
                    stroke={colorOf(name)}
                    strokeWidth="2"
                    strokeDasharray={BRANCH_DASH[series.indexOf(name)] ?? undefined}
                  />
                </svg>
                {name}
              </button>
            )
          })}
        </div>
      )}
    </>
  )
}

/**
 * กราฟ 2 — สินค้าขายดี (แท่งแนวนอน สีเดียว)
 *
 * ชุดข้อมูลเดียว จึงต้องเป็นสีเดียว — ถ้าไล่สีให้แต่ละแท่ง สีจะกลายเป็นการเข้ารหัส
 * "อันดับ" ซ้ำกับความยาวแท่งที่สื่ออยู่แล้ว และจะสลับกันเองทุกครั้งที่ข้อมูลเปลี่ยน
 */
export function TopProductsChart({ data, onSelect }) {
  if (data.length === 0) return <Empty />
  const rows = data.map((r) => ({ ...r, label: `${r.brand} ${r.model}` }))
  return (
    <ResponsiveContainer width="100%" height={Math.max(rows.length * 32, 120)}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 40 }}>
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="label"
          width={180}
          tick={{ fontSize: 11, fill: AXIS.label }}
          axisLine={{ stroke: AXIS.grid }}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: '#eaf2fd' }}
          contentStyle={TOOLTIP_STYLE}
          formatter={(v) => [`${v} ชิ้น`, 'ขายได้']}
        />
        <Bar
          dataKey="qty"
          fill={SINGLE_SERIES}
          radius={[0, 4, 4, 0]}
          barSize={16}
          label={{ position: 'right', fontSize: 11, fill: AXIS.tick }}
          onClick={(bar) => onSelect?.(bar.sku_id)}
          className={onSelect ? 'cursor-pointer' : undefined}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

/**
 * กราฟ 3 — อายุของสินค้าที่ยังค้างสต็อก (ไล่เฉดเดียว อ่อน -> เข้ม)
 *
 * ถังอายุมีลำดับในตัว (ใหม่ -> เก่า) จึงต้องเป็น sequential ramp สีเดียว
 * ถ้าใช้สีคนละหมวดจะสื่อว่าถังทั้งสี่ไม่มีความสัมพันธ์กัน ซึ่งไม่จริง
 */
export function StockAgingChart({ data }) {
  const total = data.reduce((s, r) => s + r.qty, 0)
  if (total === 0) return <Empty text="ไม่มีสินค้าคงเหลือ" />
  const rows = data.map((r) => ({ ...r, label: `${r.bucket} วัน` }))
  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={rows} margin={{ left: -20, right: 8, top: 12 }}>
        <CartesianGrid stroke={AXIS.grid} vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: AXIS.label }}
          axisLine={{ stroke: AXIS.grid }}
          tickLine={false}
        />
        <YAxis tick={{ fontSize: 11, fill: AXIS.tick }} axisLine={false} tickLine={false} allowDecimals={false} />
        <Tooltip
          cursor={{ fill: '#eaf2fd' }}
          contentStyle={TOOLTIP_STYLE}
          formatter={(v) => [`${v} ชิ้น (${Math.round((v / total) * 100)}%)`, 'คงเหลือ']}
        />
        <Bar dataKey="qty" radius={[4, 4, 0, 0]} barSize={44} label={{ position: 'top', fontSize: 11, fill: AXIS.tick }}>
          {rows.map((row, i) => (
            <Cell key={row.bucket} fill={AGING_RAMP[i]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

/**
 * กราฟ 4 — อัตราการระบายสต็อกต่อสาขา (แทนกราฟ "สต็อกตามหมวดหมู่" ที่ถูกยกเลิก)
 *
 * ยอดขายดิบเทียบข้ามสาขาไม่ได้ สาขาใหญ่ชนะเสมออยู่แล้วโดยไม่ได้บอกอะไร
 * อัตราส่วน ขายได้/(ขายได้+คงเหลือ) เทียบกันได้จริงเพราะหารขนาดสาขาออกไปแล้ว
 */
export function SellThroughChart({ data, branchNames }) {
  const colorOf = makeBranchColorScale(branchNames)
  const rows = data
    .filter((r) => r.sell_through !== null) // สาขาที่ยังไม่มีของ = คำนวณไม่ได้ ไม่ใช่ 0%
    .map((r) => ({ ...r, pct: Math.round(r.sell_through * 1000) / 10 }))
  if (rows.length === 0) return <Empty text="ยังไม่มีสาขาที่มีข้อมูลพอจะคำนวณ" />
  return (
    <ResponsiveContainer width="100%" height={Math.max(rows.length * 44, 120)}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 48 }}>
        <XAxis type="number" domain={[0, 100]} hide />
        <YAxis
          type="category"
          dataKey="branch_name"
          width={110}
          tick={{ fontSize: 11, fill: AXIS.label }}
          axisLine={{ stroke: AXIS.grid }}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: '#eaf2fd' }}
          contentStyle={TOOLTIP_STYLE}
          formatter={(v, _n, p) => [`${v}% (ขาย ${p.payload.sold} · เหลือ ${p.payload.on_hand})`, 'อัตราระบาย']}
        />
        <Bar
          dataKey="pct"
          radius={[0, 4, 4, 0]}
          barSize={20}
          label={{ position: 'right', formatter: (v) => `${v}%`, fontSize: 11, fill: AXIS.tick }}
        >
          {rows.map((row) => (
            <Cell key={row.branch_id} fill={colorOf(row.branch_name)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

const WEEKDAY_TH = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์']

/**
 * กราฟ 5 — ยอดขายตามวันในสัปดาห์ (ใช้วางแผนกำลังคน)
 *
 * ชุดข้อมูลเดียว สีเดียว · วันหยุดสุดสัปดาห์ทำเป็นสีเข้มขึ้นเล็กน้อยไม่ได้
 * เพราะจะกลายเป็นการเข้ารหัสสองอย่างทับกัน — แยกด้วยชื่อวันบนแกนพอแล้ว
 */
export function WeekdaySalesChart({ data }) {
  const total = data.reduce((s, r) => s + r.qty, 0)
  if (total === 0) return <Empty />
  const rows = data.map((r) => ({ ...r, label: WEEKDAY_TH[r.weekday] }))
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={rows} margin={{ left: -20, right: 8, top: 12 }}>
        <CartesianGrid stroke={AXIS.grid} vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: AXIS.label }}
          axisLine={{ stroke: AXIS.grid }}
          tickLine={false}
          interval={0}
        />
        <YAxis tick={{ fontSize: 11, fill: AXIS.tick }} axisLine={false} tickLine={false} allowDecimals={false} />
        <Tooltip
          cursor={{ fill: '#eaf2fd' }}
          contentStyle={TOOLTIP_STYLE}
          formatter={(v) => [`${v} ชิ้น (${Math.round((v / total) * 100)}%)`, 'ขายได้']}
        />
        <Bar dataKey="qty" fill={SINGLE_SERIES} radius={[4, 4, 0, 0]} barSize={30} />
      </BarChart>
    </ResponsiveContainer>
  )
}
