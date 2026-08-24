import { useEffect, useState } from 'react'
import client from '../../api/client'
import SortableHeader, { compareValues } from '../../components/SortableHeader'

const SORT_COLUMNS = {
  serial_number: { label: 'S/N', getValue: (i) => i.serial_number },
  product: { label: 'สินค้า', getValue: (i) => i._label },
  status: { label: 'สถานะ', getValue: (i) => (i.status === 'InStock' ? 0 : 1) },
  received_at: { label: 'รับเข้าเมื่อ', getValue: (i) => new Date(i.received_at).getTime() },
}

// FR-004, FR-005, NFR-REL-01 (ADR-002) — บันทึกขาย
// Flow: กรอก S/N → resolve เป็น item_id ผ่าน GET /api/items/by-serial → ยืนยัน → POST /api/sales
// ตาราง S/N ด้านล่าง: ให้พนักงานเห็นว่าของชิ้นไหนขายไปแล้ว/ยังพร้อมขาย โดยไม่ต้องเดาหรือ
// พิมพ์ S/N ไปลองทีละตัว — server บังคับ scope สาขาให้แล้ว (NFR-SEC-02) จึงเห็นเฉพาะของสาขาตัวเอง
export default function RecordSale() {
  const [serial, setSerial] = useState('')
  const [item, setItem] = useState(null)
  const [buyerName, setBuyerName] = useState('')
  const [buyerPhone, setBuyerPhone] = useState('')
  const [lookupError, setLookupError] = useState('')
  const [saleResult, setSaleResult] = useState(null)
  const [saleError, setSaleError] = useState('')
  const [loading, setLoading] = useState(false)

  const [items, setItems] = useState([])
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('InStock')
  const [sortKey, setSortKey] = useState('received_at')
  const [sortDir, setSortDir] = useState('desc')

  async function loadItems() {
    const [itemsRes, productsRes] = await Promise.all([
      client.get('/items'),
      client.get('/products'),
    ])
    const byId = Object.fromEntries(productsRes.data.map((p) => [p.id, p]))
    setItems(
      itemsRes.data.map((i) => {
        const p = byId[i.sku_id]
        return { ...i, _label: p ? `${p.category} — ${p.brand} ${p.model}` : `SKU #${i.sku_id}` }
      }),
    )
  }

  useEffect(() => {
    loadItems()
  }, [])

  async function handleLookup(e) {
    e.preventDefault()
    setLookupError('')
    setSaleResult(null)
    setSaleError('')
    setItem(null)
    try {
      const { data } = await client.get(`/items/by-serial/${encodeURIComponent(serial)}`)
      if (data.status !== 'InStock') {
        setLookupError(`สินค้านี้ไม่พร้อมขาย (สถานะ: ${data.status})`)
        return
      }
      setItem(data)
    } catch (err) {
      setLookupError('ไม่พบสินค้าที่มี S/N นี้ในสาขาของคุณ')
    }
  }

  // เลือกจากตารางแทนการพิมพ์ S/N — ข้อมูลชิ้นนั้นมีอยู่ในตารางแล้ว ไม่ต้องยิง lookup ซ้ำ
  // (ยังคง endpoint lookup ไว้สำหรับกรณีสแกนบาร์โค้ด/พิมพ์เองที่ของอาจไม่อยู่ใน 200 แถวแรก)
  function selectFromTable(row) {
    if (row.status !== 'InStock') return // ขายไปแล้ว กดไม่ได้
    setLookupError('')
    setSaleError('')
    setSaleResult(null)
    setSerial(row.serial_number)
    setItem(row)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function handleConfirmSale(e) {
    e.preventDefault()
    setLoading(true)
    setSaleError('')
    try {
      const { data } = await client.post(
        '/sales',
        { item_id: item.id, buyer_name: buyerName, buyer_phone: buyerPhone },
        { headers: { 'Idempotency-Key': crypto.randomUUID() } },
      )
      setSaleResult(data)
      setItem(null)
      setSerial('')
      setBuyerName('')
      setBuyerPhone('')
      await loadItems() // ให้ตารางด้านล่างสะท้อนสถานะใหม่ทันทีหลังขาย
    } catch (err) {
      if (err.response?.status === 409) {
        setSaleError('สินค้านี้ถูกขายไปแล้ว (อาจมีคนอื่นขายไปก่อนหน้านี้)')
      } else {
        setSaleError('บันทึกการขายไม่สำเร็จ')
      }
    } finally {
      setLoading(false)
    }
  }

  const inStockCount = items.filter((i) => i.status === 'InStock').length
  const soldCount = items.filter((i) => i.status === 'Sold').length

  const q = search.trim().toLowerCase()
  const visibleItems = items
    .filter((i) => (statusFilter ? i.status === statusFilter : true))
    .filter((i) => !q || i.serial_number.toLowerCase().includes(q) || i._label.toLowerCase().includes(q))
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

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="rd-title mb-4">บันทึกการขาย</h1>

      {!item && (
        <form onSubmit={handleLookup} className="rd-card p-6 space-y-3 max-w-md">
          <label className="rd-label">หมายเลขซีเรียล (S/N)</label>
          <input
            className="rd-input"
            value={serial}
            onChange={(e) => setSerial(e.target.value)}
            required
            autoFocus
          />
          {lookupError && <p className="text-[#d03b3b] text-sm">{lookupError}</p>}
          <button className="rd-btn w-full" type="submit">
            ค้นหา
          </button>
        </form>
      )}

      {item && (
        <form onSubmit={handleConfirmSale} className="rd-card p-6 space-y-3 max-w-md">
          <div className="bg-ink-accentSoft rounded-lg p-3 text-sm">
            <p>
              <span className="font-medium">S/N:</span> {item.serial_number}
            </p>
            <p className="text-ink-accent">พร้อมขาย (In Stock)</p>
          </div>
          <div>
            <label className="rd-label">ชื่อผู้ซื้อ</label>
            <input
              className="rd-input"
              value={buyerName}
              onChange={(e) => setBuyerName(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="rd-label">เบอร์โทรผู้ซื้อ</label>
            <input
              className="rd-input"
              value={buyerPhone}
              onChange={(e) => setBuyerPhone(e.target.value)}
              required
            />
          </div>
          {saleError && <p className="text-[#d03b3b] text-sm">{saleError}</p>}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setItem(null)}
              className="rd-btn-secondary flex-1"
            >
              ยกเลิก
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rd-btn flex-1"
            >
              {loading ? 'กำลังบันทึก...' : 'ยืนยันการขาย'}
            </button>
          </div>
        </form>
      )}

      {saleResult && (
        <div className="mt-4 rd-card p-4 text-sm border-[#0a7d0a]/30 bg-[#e8f5e9] max-w-md">
          <p className="text-[#0a7d0a] font-medium">บันทึกการขายสำเร็จ</p>
          <p>
            วันหมดประกัน: {new Date(saleResult.warranty_expires_at).toLocaleDateString('th-TH')}
          </p>
        </div>
      )}

      <div className="mt-8">
        <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
          <div>
            <h2 className="rd-title">
              หมายเลขซีเรียล (S/N) ในสาขา
              <span className="ml-2 text-sm font-normal text-ink-muted">
                พร้อมขาย {inStockCount} ชิ้น · ขายแล้ว {soldCount} ชิ้น
              </span>
            </h2>
            <p className="text-xs text-ink-muted mt-1">คลิกแถวที่พร้อมขายเพื่อบันทึกการขายได้เลย</p>
          </div>
        </div>

        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="ค้นหา S/N / สินค้า..."
            className="rd-input max-w-xs"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rd-input w-auto"
          >
            <option value="InStock">พร้อมขาย</option>
            <option value="Sold">ขายแล้ว</option>
            <option value="">ทั้งหมด</option>
          </select>
          <p className="text-xs text-ink-muted ml-auto whitespace-nowrap">
            {visibleItems.length} / {items.length} รายการ
          </p>
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
                    onClick={() => toggleSort(key)}
                  />
                ))}
              </tr>
            </thead>
            <tbody>
              {visibleItems.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-ink-muted">
                    {items.length === 0 ? 'ยังไม่มีสินค้าในสาขา' : 'ไม่พบรายการที่ตรงกับเงื่อนไข'}
                  </td>
                </tr>
              ) : (
                visibleItems.map((i) => {
                  const sellable = i.status === 'InStock'
                  return (
                    <tr
                      key={i.id}
                      onClick={() => selectFromTable(i)}
                      title={sellable ? 'คลิกเพื่อบันทึกขายชิ้นนี้' : 'ขายไปแล้ว'}
                      className={`rd-tr ${sellable ? 'cursor-pointer hover:bg-ink-accentSoft' : 'opacity-60'}`}
                    >
                      <td
                        className={`rd-td font-mono text-xs ${
                          sellable ? 'text-ink-accent underline decoration-dotted underline-offset-2' : ''
                        }`}
                      >
                        {i.serial_number}
                      </td>
                      <td className="rd-td text-ink-muted">{i._label}</td>
                      <td className="rd-td">
                        <span className={`rd-badge ${sellable ? 'rd-badge-approved' : 'rd-badge-muted'}`}>
                          {sellable ? 'พร้อมขาย' : 'ขายแล้ว'}
                        </span>
                      </td>
                      <td className="rd-td text-ink-muted whitespace-nowrap">
                        {new Date(i.received_at).toLocaleString('th-TH')}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
        {items.length >= 200 && (
          <p className="mt-2 text-xs text-ink-muted">
            แสดง 200 รายการล่าสุดเท่านั้น (จำกัดไว้กันดึงข้อมูลทั้งคลังพร้อมกัน) — ใช้ช่องค้นหาด้านบนเพื่อหา S/N ที่ต้องการ
          </p>
        )}
      </div>
    </div>
  )
}
