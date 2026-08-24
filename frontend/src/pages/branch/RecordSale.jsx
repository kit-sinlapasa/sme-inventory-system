import { useState } from 'react'
import client from '../../api/client'

// FR-004, FR-005, NFR-REL-01 (ADR-002) — บันทึกขาย
// Flow: กรอก S/N → resolve เป็น item_id ผ่าน GET /api/items/by-serial → ยืนยัน → POST /api/sales
export default function RecordSale() {
  const [serial, setSerial] = useState('')
  const [item, setItem] = useState(null)
  const [buyerName, setBuyerName] = useState('')
  const [buyerPhone, setBuyerPhone] = useState('')
  const [lookupError, setLookupError] = useState('')
  const [saleResult, setSaleResult] = useState(null)
  const [saleError, setSaleError] = useState('')
  const [loading, setLoading] = useState(false)

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

  return (
    <div className="max-w-md mx-auto">
      <h1 className="rd-title mb-4">บันทึกการขาย</h1>

      {!item && (
        <form onSubmit={handleLookup} className="rd-card p-6 space-y-3">
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
        <form onSubmit={handleConfirmSale} className="rd-card p-6 space-y-3">
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
        <div className="mt-4 rd-card p-4 text-sm border-[#0a7d0a]/30 bg-[#e8f5e9]">
          <p className="text-[#0a7d0a] font-medium">บันทึกการขายสำเร็จ</p>
          <p>
            วันหมดประกัน: {new Date(saleResult.warranty_expires_at).toLocaleDateString('th-TH')}
          </p>
        </div>
      )}
    </div>
  )
}
