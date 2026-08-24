import { Fragment, useEffect, useState } from 'react'
import client from '../../api/client'

const CATEGORIES = ['RAM', 'Mainboard', 'CPU', 'GPU', 'Storage', 'PSU']

// FR-001, US-02 — เพิ่มสินค้าใหม่ + ระงับ (soft-delete)
export default function Products() {
  const [products, setProducts] = useState([])
  const [showInactive, setShowInactive] = useState(false)
  const [form, setForm] = useState({ category: 'RAM', brand: '', model: '', spec: '', warranty_months: 12 })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const [imageUrlInput, setImageUrlInput] = useState('')
  const [imageError, setImageError] = useState('')

  async function load() {
    const { data } = await client.get(`/products${showInactive ? '?include_inactive=true' : ''}`)
    setProducts(data)
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showInactive])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await client.post('/products', { ...form, warranty_months: Number(form.warranty_months) })
      setForm({ category: 'RAM', brand: '', model: '', spec: '', warranty_months: 12 })
      await load()
    } catch (err) {
      setError('เพิ่มสินค้าไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleSuspend(id) {
    if (!confirm('ยืนยันระงับสินค้านี้? (ยังดูประวัติได้ แค่ไม่แสดงในรายการปกติ)')) return
    await client.delete(`/products/${id}`)
    await load()
  }

  function toggleImages(id) {
    setImageError('')
    setImageUrlInput('')
    setExpandedId(expandedId === id ? null : id)
  }

  // FR-013 (CR-007) — เพิ่มรูปสินค้าสูงสุด 5 รูปต่อ SKU (URL เท่านั้น — ไม่มี file upload)
  async function handleAddImage(productId) {
    setImageError('')
    try {
      await client.post(`/products/${productId}/images`, { image_url: imageUrlInput })
      setImageUrlInput('')
      await load()
    } catch (err) {
      const detail = err?.response?.data?.detail
      if (err?.response?.status === 409) {
        setImageError(detail || 'สินค้านี้มีรูปครบ 5 รูปแล้ว')
      } else if (err?.response?.status === 422) {
        setImageError('URL ไม่ถูกต้อง กรุณาตรวจสอบ')
      } else {
        setImageError('เพิ่มรูปไม่สำเร็จ')
      }
    }
  }

  async function handleDeleteImage(productId, imageId) {
    await client.delete(`/products/${productId}/images/${imageId}`)
    await load()
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-brand-900 mb-4">เพิ่มสินค้าใหม่</h1>
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm text-gray-600 mb-1">หมวดหมู่</label>
            <select
              className="w-full border border-brand-100 rounded px-3 py-2"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">ระยะประกัน (เดือน)</label>
            <input
              type="number"
              min="1"
              className="w-full border border-brand-100 rounded px-3 py-2"
              value={form.warranty_months}
              onChange={(e) => setForm({ ...form, warranty_months: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">ยี่ห้อ</label>
            <input
              className="w-full border border-brand-100 rounded px-3 py-2"
              value={form.brand}
              onChange={(e) => setForm({ ...form, brand: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">รุ่น</label>
            <input
              className="w-full border border-brand-100 rounded px-3 py-2"
              value={form.model}
              onChange={(e) => setForm({ ...form, model: e.target.value })}
              required
            />
          </div>
          <div className="col-span-2">
            <label className="block text-sm text-gray-600 mb-1">สเปก (ถ้ามี)</label>
            <input
              className="w-full border border-brand-100 rounded px-3 py-2"
              value={form.spec}
              onChange={(e) => setForm({ ...form, spec: e.target.value })}
            />
          </div>
          {error && <p className="text-red-600 text-sm col-span-2">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="col-span-2 bg-brand-600 text-white py-2 rounded hover:bg-brand-900 disabled:opacity-50"
          >
            {submitting ? 'กำลังเพิ่ม...' : 'เพิ่มสินค้า'}
          </button>
        </form>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-brand-900">รายการสินค้า</h2>
          <label className="text-sm text-gray-600 flex items-center gap-2">
            <input type="checkbox" checked={showInactive} onChange={(e) => setShowInactive(e.target.checked)} />
            แสดงที่ถูกระงับด้วย
          </label>
        </div>
        <div className="bg-white rounded-lg shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-100 text-brand-900">
              <tr>
                <th className="text-left px-4 py-2">หมวดหมู่</th>
                <th className="text-left px-4 py-2">ยี่ห้อ / รุ่น</th>
                <th className="text-right px-4 py-2">ประกัน (เดือน)</th>
                <th className="text-left px-4 py-2">สถานะ</th>
                <th className="text-left px-4 py-2">รูปภาพ</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <Fragment key={p.id}>
                  <tr className={`border-t border-brand-50 ${!p.is_active ? 'opacity-50' : ''}`}>
                    <td className="px-4 py-2">{p.category}</td>
                    <td className="px-4 py-2">
                      {p.brand} {p.model}
                    </td>
                    <td className="px-4 py-2 text-right">{p.warranty_months}</td>
                    <td className="px-4 py-2">{p.is_active ? 'ใช้งาน' : 'ระงับแล้ว'}</td>
                    <td className="px-4 py-2">
                      <button onClick={() => toggleImages(p.id)} className="text-brand-600 text-xs hover:underline">
                        {(p.images || []).length}/5 รูป
                      </button>
                    </td>
                    <td className="px-4 py-2 text-right">
                      {p.is_active && (
                        <button onClick={() => handleSuspend(p.id)} className="text-red-600 text-xs hover:underline">
                          ระงับ
                        </button>
                      )}
                    </td>
                  </tr>
                  {expandedId === p.id && (
                    <tr className="border-t border-brand-50 bg-brand-50/40">
                      <td colSpan={6} className="px-4 py-3">
                        <div className="flex flex-wrap gap-3 mb-3">
                          {(p.images || []).map((img) => (
                            <div key={img.id} className="relative">
                              <img
                                src={img.image_url}
                                alt=""
                                className="w-20 h-20 object-cover rounded border border-brand-100"
                              />
                              <button
                                onClick={() => handleDeleteImage(p.id, img.id)}
                                className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-5 h-5 text-xs leading-5"
                                title="ลบรูปนี้"
                              >
                                ×
                              </button>
                            </div>
                          ))}
                          {(p.images || []).length === 0 && (
                            <p className="text-sm text-gray-400">ยังไม่มีรูปภาพ</p>
                          )}
                        </div>
                        {(p.images || []).length < 5 && (
                          <div className="flex gap-2 items-center">
                            <input
                              className="border border-brand-100 rounded px-3 py-1.5 text-sm flex-1 max-w-md"
                              placeholder="https://example.com/image.jpg"
                              value={imageUrlInput}
                              onChange={(e) => setImageUrlInput(e.target.value)}
                            />
                            <button
                              onClick={() => handleAddImage(p.id)}
                              disabled={!imageUrlInput}
                              className="bg-brand-600 text-white px-3 py-1.5 rounded text-sm hover:bg-brand-900 disabled:opacity-50"
                            >
                              เพิ่มรูป
                            </button>
                          </div>
                        )}
                        {imageError && <p className="text-red-600 text-xs mt-2">{imageError}</p>}
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
