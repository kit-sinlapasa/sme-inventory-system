import { useEffect, useState } from 'react'
import client from '../../api/client'

const STATUS_LABEL = { Pending: 'รอดำเนินการ', Approved: 'อนุมัติแล้ว', Rejected: 'ปฏิเสธ' }
const STATUS_COLOR = {
  Pending: 'rd-badge-pending',
  Approved: 'rd-badge-approved',
  Rejected: 'rd-badge-rejected',
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
        <h1 className="rd-title">คำขอสั่งซื้อ</h1>
        <select
          className="rd-input text-sm w-auto"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="Pending">รอดำเนินการ</option>
          <option value="Approved">อนุมัติแล้ว</option>
          <option value="Rejected">ปฏิเสธ</option>
          <option value="">ทั้งหมด</option>
        </select>
      </div>

      {error && <p className="text-[#d03b3b] text-sm mb-4">{error}</p>}

      {requests.length === 0 ? (
        <p className="text-ink-muted text-sm">ไม่มีคำขอในสถานะนี้</p>
      ) : (
        <div className="space-y-3">
          {requests.map((r) => (
            <div key={r.id} className="rd-card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-ink-text">{productLabel(r.sku_id)}</p>
                  <p className="text-sm text-ink-muted">
                    จำนวน {r.quantity} · {branchLabel(r.branch_id)}
                  </p>
                  <p className="text-sm text-ink-muted">
                    ขอเมื่อ {formatDateTime(r.requested_at)}
                    {r.decided_at && ` · ตัดสินใจเมื่อ ${formatDateTime(r.decided_at)}`}
                  </p>
                </div>
                <span className={`rd-badge ${STATUS_COLOR[r.status]}`}>
                  {STATUS_LABEL[r.status] ?? r.status}
                </span>
              </div>

              {r.status === 'Pending' && (
                <div className="mt-3 pt-3 rd-tr">
                  {rejectingId === r.id ? (
                    <div className="flex gap-2">
                      <input
                        className="rd-input text-sm"
                        placeholder="เหตุผลที่ปฏิเสธ (บังคับกรอก)"
                        value={rejectReason}
                        onChange={(e) => setRejectReason(e.target.value)}
                        autoFocus
                      />
                      <button
                        onClick={() => handleReject(r.id)}
                        disabled={!rejectReason.trim()}
                        className="rd-btn-danger disabled:opacity-50"
                      >
                        ยืนยันปฏิเสธ
                      </button>
                      <button
                        onClick={() => {
                          setRejectingId(null)
                          setRejectReason('')
                        }}
                        className="text-ink-muted text-sm px-2"
                      >
                        ยกเลิก
                      </button>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleApprove(r.id)}
                        className="rd-btn"
                      >
                        อนุมัติ
                      </button>
                      <button
                        onClick={() => setRejectingId(r.id)}
                        className="rd-btn-danger"
                      >
                        ปฏิเสธ
                      </button>
                    </div>
                  )}
                </div>
              )}
              {r.status === 'Rejected' && r.reject_reason && (
                <p className="mt-2 text-sm text-[#d03b3b]">เหตุผล: {r.reject_reason}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
