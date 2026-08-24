import { useEffect, useState } from 'react'
import client from '../../api/client'

const STATUS_LABEL = { Pending: 'รอดำเนินการ', Approved: 'อนุมัติแล้ว', Rejected: 'ปฏิเสธ' }
const STATUS_COLOR = {
  Pending: 'bg-yellow-100 text-yellow-800',
  Approved: 'bg-green-100 text-green-800',
  Rejected: 'bg-red-100 text-red-800',
}

// คำขอที่ยังไม่ถูกตัดสินใจจะไม่มี decided_at — แสดง "—" แทน Invalid Date
function formatDateTime(value) {
  return value ? new Date(value).toLocaleString('th-TH') : '—'
}

// FR-010, US-07 — Admin ตรวจสอบและอนุมัติ/ปฏิเสธคำขอสั่งซื้อ
export default function PurchaseRequests() {
  const [requests, setRequests] = useState([])
  const [products, setProducts] = useState([])
  const [branches, setBranches] = useState([])
  const [filter, setFilter] = useState('Pending')
  const [error, setError] = useState('')
  const [rejectingId, setRejectingId] = useState(null)
  const [rejectReason, setRejectReason] = useState('')

  async function load() {
    const url = filter ? `/purchase-requests?status=${filter}` : '/purchase-requests'
    const [reqRes, prodRes, branchRes] = await Promise.all([
      client.get(url),
      client.get('/products'),
      client.get('/branches'),
    ])
    setRequests(reqRes.data)
    setProducts(prodRes.data)
    setBranches(branchRes.data)
  }

  function branchLabel(branch_id) {
    const b = branches.find((b) => b.id === branch_id)
    return b ? b.name : `สาขา #${branch_id}`
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter])

  function productLabel(sku_id) {
    const p = products.find((p) => p.id === sku_id)
    return p ? `${p.category} — ${p.brand} ${p.model}` : `SKU #${sku_id}`
  }

  async function handleApprove(id) {
    setError('')
    try {
      await client.post(`/purchase-requests/${id}/approve`)
      await load()
    } catch (err) {
      setError('อนุมัติไม่สำเร็จ — คำขอนี้อาจถูกตัดสินใจไปแล้ว')
    }
  }

  async function handleReject(id) {
    if (!rejectReason.trim()) return
    setError('')
    try {
      await client.post(`/purchase-requests/${id}/reject`, { reason: rejectReason })
      setRejectingId(null)
      setRejectReason('')
      await load()
    } catch (err) {
      setError('ปฏิเสธไม่สำเร็จ — คำขอนี้อาจถูกตัดสินใจไปแล้ว')
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold text-brand-900">คำขอสั่งซื้อ</h1>
        <select
          className="border border-brand-100 rounded px-3 py-1.5 text-sm"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="Pending">รอดำเนินการ</option>
          <option value="Approved">อนุมัติแล้ว</option>
          <option value="Rejected">ปฏิเสธ</option>
          <option value="">ทั้งหมด</option>
        </select>
      </div>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {requests.length === 0 ? (
        <p className="text-gray-500 text-sm">ไม่มีคำขอในสถานะนี้</p>
      ) : (
        <div className="space-y-3">
          {requests.map((r) => (
            <div key={r.id} className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-brand-900">{productLabel(r.sku_id)}</p>
                  <p className="text-sm text-gray-500">
                    จำนวน {r.quantity} · {branchLabel(r.branch_id)}
                  </p>
                  <p className="text-sm text-gray-500">
                    ขอเมื่อ {formatDateTime(r.requested_at)}
                    {r.decided_at && ` · ตัดสินใจเมื่อ ${formatDateTime(r.decided_at)}`}
                  </p>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${STATUS_COLOR[r.status]}`}>
                  {STATUS_LABEL[r.status] ?? r.status}
                </span>
              </div>

              {r.status === 'Pending' && (
                <div className="mt-3 pt-3 border-t border-brand-50">
                  {rejectingId === r.id ? (
                    <div className="flex gap-2">
                      <input
                        className="flex-1 border border-brand-100 rounded px-3 py-1.5 text-sm"
                        placeholder="เหตุผลที่ปฏิเสธ (บังคับกรอก)"
                        value={rejectReason}
                        onChange={(e) => setRejectReason(e.target.value)}
                        autoFocus
                      />
                      <button
                        onClick={() => handleReject(r.id)}
                        disabled={!rejectReason.trim()}
                        className="bg-red-600 text-white px-3 py-1.5 rounded text-sm disabled:opacity-50"
                      >
                        ยืนยันปฏิเสธ
                      </button>
                      <button
                        onClick={() => {
                          setRejectingId(null)
                          setRejectReason('')
                        }}
                        className="text-gray-500 text-sm px-2"
                      >
                        ยกเลิก
                      </button>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleApprove(r.id)}
                        className="bg-brand-600 text-white px-3 py-1.5 rounded text-sm hover:bg-brand-900"
                      >
                        อนุมัติ
                      </button>
                      <button
                        onClick={() => setRejectingId(r.id)}
                        className="border border-red-200 text-red-600 px-3 py-1.5 rounded text-sm hover:bg-red-50"
                      >
                        ปฏิเสธ
                      </button>
                    </div>
                  )}
                </div>
              )}
              {r.status === 'Rejected' && r.reject_reason && (
                <p className="mt-2 text-sm text-red-600">เหตุผล: {r.reject_reason}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
