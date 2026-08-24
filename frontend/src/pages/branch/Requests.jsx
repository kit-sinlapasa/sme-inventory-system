import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import client from '../../api/client'
import SortableHeader, { compareValues } from '../../components/SortableHeader'

const STATUS_LABEL = { Pending: 'รอดำเนินการ', Approved: 'อนุมัติแล้ว', Rejected: 'ปฏิเสธ' }

// คำขอที่ยังไม่ถูกตัดสินใจจะไม่มี decided_at — แสดง "—" แทนที่จะโชว์ Invalid Date
function formatDateTime(value) {
  return value ? new Date(value).toLocaleString('th-TH') : '—'
}

const STATUS_COLOR = {
  Pending: 'rd-badge-pending',
  Approved: 'rd-badge-approved',
  Rejected: 'rd-badge-rejected',
}

// FR-009, US-06 — สาขาสร้างคำขอสั่งซื้อ + ดูสถานะคำขอของตัวเอง
export default function Requests() {
  // CR-013 — มาจากปุ่ม "ขอสั่งซื้อ" ในตารางของใกล้หมดบนหน้าภาพรวม
  // เลือกส่งผ่าน router state ไม่ใช่ query string เพราะเป็นค่าตั้งต้นของฟอร์มชั่วคราว
  // ไม่ใช่สถานะของหน้าที่ควร bookmark หรือแชร์ลิงก์ได้
  const location = useLocation()
  const prefillSkuId = location.state?.prefillSkuId

  const [products, setProducts] = useState([])
  const [requests, setRequests] = useState([])
  const [skuId, setSkuId] = useState('')
  const [quantity, setQuantity] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('requested_at')
  const [sortDir, setSortDir] = useState('desc') // ค่าเริ่มต้น: คำขอล่าสุดอยู่บนสุด

  async function loadAll() {
    const [productsRes, requestsRes] = await Promise.all([client.get('/products'), client.get('/purchase-requests')])
    setProducts(productsRes.data)
    setRequests(requestsRes.data)
  }

  useEffect(() => {
    loadAll()
  }, [])

  useEffect(() => {
    if (prefillSkuId != null) setSkuId(String(prefillSkuId))
  }, [prefillSkuId])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await client.post('/purchase-requests', { sku_id: Number(skuId), quantity: Number(quantity) })
      setSkuId('')
      setQuantity('')
      await loadAll()
    } catch (err) {
      setError('ส่งคำขอไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    } finally {
      setSubmitting(false)
    }
  }

  function productLabel(sku_id) {
    const p = products.find((p) => p.id === sku_id)
    return p ? `${p.category} — ${p.brand} ${p.model}` : `SKU #${sku_id}`
  }

  // ค่าที่ใช้เรียง — ดึงจากคอลัมน์ที่ผู้ใช้เห็นจริง (สินค้าเรียงตามชื่อที่แสดง ไม่ใช่ sku_id
  // ที่ผู้ใช้ไม่เห็น, สถานะเรียงตามภาษาไทยที่แสดงจริง)
  const SORT_COLUMNS = {
    product: { label: 'สินค้า', getValue: (r) => productLabel(r.sku_id) },
    quantity: { label: 'จำนวน', getValue: (r) => r.quantity, align: 'right' },
    requested_at: { label: 'วันที่ขอ', getValue: (r) => new Date(r.requested_at).getTime() },
    status: { label: 'สถานะ', getValue: (r) => STATUS_LABEL[r.status] ?? r.status },
    decided_at: {
      label: 'วันที่ตัดสินใจ',
      getValue: (r) => (r.decided_at ? new Date(r.decided_at).getTime() : null),
    },
    reject_reason: { label: 'เหตุผล (ถ้าปฏิเสธ)', getValue: (r) => r.reject_reason },
  }

  const q = search.trim().toLowerCase()
  const visibleRequests = requests
    .filter((r) => {
      if (!q) return true
      return (
        productLabel(r.sku_id).toLowerCase().includes(q) ||
        (STATUS_LABEL[r.status] ?? r.status).toLowerCase().includes(q) ||
        (r.reject_reason ?? '').toLowerCase().includes(q) ||
        String(r.quantity).includes(q)
      )
    })
    .sort((a, b) =>
      compareValues(SORT_COLUMNS[sortKey].getValue(a), SORT_COLUMNS[sortKey].getValue(b), sortDir),
    )

  function toggleSort(key) {
    if (key === sortKey) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="rd-title mb-4">สร้างคำขอสั่งซื้อ</h1>
        <form onSubmit={handleSubmit} className="rd-card p-6 space-y-3">
          <div>
            <label className="rd-label">สินค้า</label>
            <select
              className="rd-input"
              value={skuId}
              onChange={(e) => setSkuId(e.target.value)}
              required
            >
              <option value="">-- เลือกสินค้า --</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.category} — {p.brand} {p.model}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="rd-label">จำนวน</label>
            <input
              type="number"
              min="1"
              className="rd-input"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-[#d03b3b] text-sm">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="rd-btn"
          >
            {submitting ? 'กำลังส่ง...' : 'ส่งคำขอ'}
          </button>
        </form>
      </div>

      <div>
        <h2 className="rd-title mb-4">คำขอของสาขา</h2>
        {requests.length === 0 ? (
          <p className="text-ink-muted text-sm">ยังไม่มีคำขอ</p>
        ) : (
          <>
            <div className="flex items-center justify-between mb-3">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="ค้นหาสินค้า / สถานะ / เหตุผล / จำนวน..."
                className="rd-input max-w-sm"
              />
              <p className="text-xs text-ink-muted ml-3 whitespace-nowrap">
                {visibleRequests.length} / {requests.length} รายการ
              </p>
            </div>
            <div className="rd-card overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-ink-muted">
                  <tr>
                    {Object.entries(SORT_COLUMNS).map(([key, col]) => (
                      <SortableHeader
                        key={key}
                        label={col.label}
                        active={sortKey === key}
                        dir={sortDir}
                        align={col.align}
                        onClick={() => toggleSort(key)}
                      />
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {visibleRequests.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-ink-muted">
                        ไม่พบคำขอที่ตรงกับ "{search}"
                      </td>
                    </tr>
                  ) : (
                    visibleRequests.map((r) => (
                      <tr key={r.id} className="rd-tr">
                        <td className="px-4 py-2">{productLabel(r.sku_id)}</td>
                        <td className="px-4 py-2 text-right">{r.quantity}</td>
                        <td className="px-4 py-2 text-ink-muted whitespace-nowrap">
                          {formatDateTime(r.requested_at)}
                        </td>
                        <td className="px-4 py-2">
                          <span className={`rd-badge ${STATUS_COLOR[r.status]}`}>
                            {STATUS_LABEL[r.status] ?? r.status}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-ink-muted whitespace-nowrap">
                          {formatDateTime(r.decided_at)}
                        </td>
                        <td className="px-4 py-2 text-ink-muted">{r.reject_reason ?? '—'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
