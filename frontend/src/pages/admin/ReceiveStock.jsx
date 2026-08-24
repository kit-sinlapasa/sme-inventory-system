import { useEffect, useState } from 'react'
import client from '../../api/client'

// FR-002, US-03 — รับสินค้าเข้าสต็อกเป็นรายชิ้นพร้อม S/N
export default function ReceiveStock() {
  const [products, setProducts] = useState([])
  const [branches, setBranches] = useState([])
  const [skuId, setSkuId] = useState('')
  const [branchId, setBranchId] = useState('')
  const [serial, setSerial] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    client.get('/products').then(({ data }) => setProducts(data))
    client.get('/branches').then(({ data }) => setBranches(data))
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setSubmitting(true)
    try {
      const { data } = await client.post('/items', {
        sku_id: Number(skuId),
        branch_id: Number(branchId),
        serial_number: serial,
      })
      setSuccess(`รับเข้าสต็อกสำเร็จ: S/N ${data.serial_number}`)
      setSerial('')
    } catch (err) {
      if (err.response?.status === 409) {
        setError('S/N นี้มีอยู่แล้วในระบบ')
      } else {
        setError('รับเข้าสต็อกไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-lg font-semibold text-brand-900 mb-4">รับสินค้าเข้าสต็อก</h1>
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
          <label className="block text-sm text-gray-600 mb-1">สาขาที่รับเข้า</label>
          <select
            className="w-full border border-brand-100 rounded px-3 py-2"
            value={branchId}
            onChange={(e) => setBranchId(e.target.value)}
            required
          >
            <option value="">-- เลือกสาขา --</option>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm text-gray-600 mb-1">หมายเลขซีเรียล (S/N)</label>
          <input
            className="w-full border border-brand-100 rounded px-3 py-2"
            value={serial}
            onChange={(e) => setSerial(e.target.value)}
            required
          />
        </div>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        {success && <p className="text-green-700 text-sm">{success}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-brand-600 text-white py-2 rounded hover:bg-brand-900 disabled:opacity-50"
        >
          {submitting ? 'กำลังบันทึก...' : 'รับเข้าสต็อก'}
        </button>
      </form>
    </div>
  )
}
