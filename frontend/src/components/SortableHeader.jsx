// หัวตารางที่คลิกเรียงลำดับได้ — ไม่ผูกสีตายตัว ใช้ opacity บอกสถานะ active แทน
// ทำให้อ่านออกบนทุกพื้นหลังไม่ว่าตารางจะอยู่ในการ์ดหรือพื้นหน้าเพจ
export default function SortableHeader({ label, active, dir, align = 'left', onClick }) {
  return (
    <th
      onClick={onClick}
      className={`px-4 py-3 font-medium cursor-pointer select-none ${
        align === 'right' ? 'text-right' : 'text-left'
      }`}
    >
      <span
        className={
          align === 'right'
            ? 'inline-flex flex-row-reverse items-center gap-1'
            : 'inline-flex items-center gap-1'
        }
      >
        {label}
        <span className={`text-[10px] ${active ? 'opacity-100' : 'opacity-25'}`}>
          {active && dir === 'desc' ? '▼' : '▲'}
        </span>
      </span>
    </th>
  )
}

// ตัวช่วยเรียงลำดับที่ใช้ร่วมกัน — รองรับทั้ง string (localeCompare สำหรับภาษาไทย)
// และตัวเลข/วันที่ ค่า null/undefined ถูกดันไปท้ายเสมอไม่ว่าจะเรียงขึ้นหรือลง
// (ไม่งั้นแถวที่ยังไม่มีข้อมูล เช่น "วันที่ตัดสินใจ" ของคำขอที่ยังไม่ตัดสิน จะไปแทรกกลางตาราง)
export function compareValues(a, b, dir) {
  const nullA = a === null || a === undefined || a === ''
  const nullB = b === null || b === undefined || b === ''
  if (nullA && nullB) return 0
  if (nullA) return 1
  if (nullB) return -1

  const cmp = typeof a === 'string' && typeof b === 'string' ? a.localeCompare(b, 'th') : a - b
  return dir === 'asc' ? cmp : -cmp
}
