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
      <h1 className="text-lg font-semibold text-brand-900 mb-4">บันทึกการขาย</h1>

      {!item && (
        <form onSubmit={handleLookup} className="bg-white rounded-lg shadow p-6 space-y-3">
          <label className="block text-sm text-gray-600">หมายเลขซีเรียล (S/N)</label>
          <input
            className="w-full border border-brand-100 rounded px-3 py-2"
            value={serial}
            onChange={(e) => setSerial(e.target.value)}
            required
            autoFocus
          />
          {lookupError && <p className="text-red-600 text-sm">{lookupError}</p>}
          <button className="w-full bg-brand-600 text-white py-2 rounded hover:bg-brand-900" type="submit">
            ค้นหา
          </button>
        </form>
      )}

      {item && (
        <form onSubmit={handleConfirmSale} className="bg-white rounded-lg shadow p-6 space-y-3">
          <div className="bg-brand-100 rounded p-3 text-sm">
            <p>
              <span className="font-medium">S/N:</span> {item.serial_number}
            </p>
            <p className="text-brand-600">พร้อมขาย (In Stock)</p>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">ชื่อผู้ซื้อ</label>
            <input
              className="w-full border border-brand-100 rounded px-3 py-2"
              value={buyerName}
              onChange={(e) => setBuyerName(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">เบอร์โทรผู้ซื้อ</label>
            <input
              className="w-full border border-brand-100 rounded px-3 py-2"
              value={buyerPhone}
              onChange={(e) => setBuyerPhone(e.target.value)}
              required
            />
          </div>
          {saleError && <p className="text-red-600 text-sm">{saleError}</p>}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setItem(null)}
              className="flex-1 border border-brand-100 text-brand-900 py-2 rounded"
            >
              ยกเลิก
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-brand-600 text-white py-2 rounded hover:bg-brand-900 disabled:opacity-50"
            >
              {loading ? 'กำลังบันทึก...' : 'ยืนยันการขาย'}
            </button>
          </div>
        </form>
      )}

      {saleResult && (
        <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4 text-sm">
          <p className="text-green-700 font-medium">บันทึกการขายสำเร็จ</p>
          <p>
            วันหมดประกัน: {new Date(saleResult.warranty_expires_at).toLocaleDateString('th-TH')}
          </p>
        </div>
      )}
    </div>
  )
}
