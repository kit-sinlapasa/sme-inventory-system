import { useEffect, useState } from 'react'
import client from '../../api/client'

const STATUS_LABEL = { Pending: 'รอดำเนินการ', Approved: 'อนุมัติแล้ว', Rejected: 'ปฏิเสธ' }
const STATUS_COLOR = {
  Pending: 'bg-yellow-100 text-yellow-800',
  Approved: 'bg-green-100 text-green-800',
  Rejected: 'bg-red-100 text-red-800',
}

// FR-009, US-06 — สาขาสร้างคำขอสั่งซื้อ + ดูสถานะคำขอของตัวเอง
export default function Requests() {
  const [products, setProducts] = useState([])
  const [requests, setRequests] = useState([])
  const [skuId, setSkuId] = useState('')
  const [quantity, setQuantity] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function loadAll() {
    const [productsRes, requestsRes] = await Promise.all([client.get('/products'), client.get('/purchase-requests')])
    setProducts(productsRes.data)
    setRequests(requestsRes.data)
  }

  useEffect(() => {
    loadAll()
  }, [])

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

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-brand-900 mb-4">สร้างคำขอสั่งซื้อ</h1>
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-3">
          <div>
            <label className="block text-sm text-gray-600 mb-1">สินค้า</label>
            <select
              className="w-full border border-brand-100 rounded px-3 py-2"
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
            <label className="block text-sm text-gray-600 mb-1">จำนวน</label>
            <input
              type="number"
              min="1"
              className="w-full border border-brand-100 rounded px-3 py-2"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="bg-brand-600 text-white px-4 py-2 rounded hover:bg-brand-900 disabled:opacity-50"
          >
            {submitting ? 'กำลังส่ง...' : 'ส่งคำขอ'}
          </button>
        </form>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-brand-900 mb-4">คำขอของสาขา</h2>
        {requests.length === 0 ? (
          <p className="text-gray-500 text-sm">ยังไม่มีคำขอ</p>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-brand-100 text-brand-900">
                <tr>
                  <th className="text-left px-4 py-2">สินค้า</th>
                  <th className="text-right px-4 py-2">จำนวน</th>
                  <th className="text-left px-4 py-2">สถานะ</th>
                  <th className="text-left px-4 py-2">เหตุผล (ถ้าปฏิเสธ)</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((r) => (
                  <tr key={r.id} className="border-t border-brand-50">
                    <td className="px-4 py-2">{productLabel(r.sku_id)}</td>
                    <td className="px-4 py-2 text-right">{r.quantity}</td>
                    <td className="px-4 py-2">
                      <span className={`text-xs px-2 py-1 rounded ${STATUS_COLOR[r.status]}`}>
                        {STATUS_LABEL[r.status] ?? r.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-gray-500">{r.reject_reason ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
