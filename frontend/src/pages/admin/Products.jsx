import { Fragment, useEffect, useState } from 'react'
import client from '../../api/client'
import SortableHeader, { compareValues } from '../../components/SortableHeader'

const CATEGORIES = ['RAM', 'Mainboard', 'CPU', 'GPU', 'Storage', 'PSU']
const EMPTY_FORM = { category: 'RAM', brand: '', model: '', spec: '', warranty_months: 12 }

const SORT_COLUMNS = {
  category: { label: 'หมวดหมู่', getValue: (p) => p.category },
  model: { label: 'ยี่ห้อ / รุ่น', getValue: (p) => `${p.brand} ${p.model}` },
  warranty_months: { label: 'ประกัน (เดือน)', getValue: (p) => p.warranty_months, align: 'right' },
  is_active: { label: 'สถานะ', getValue: (p) => (p.is_active ? 0 : 1) },
}

// FR-001, US-02 — Admin (สำนักงานใหญ่) จัดการสินค้าได้เต็มรูปแบบ: เพิ่ม / แก้ไข / ระงับ / กู้คืน
// หมายเหตุเรื่อง "ลบ": ระบบไม่มีการลบถาวรโดยตั้งใจ เพราะ Item รายชิ้น (S/N) และประวัติการขาย
// อ้างอิง product นี้ผ่าน FK อยู่ — ลบทิ้งจะทำให้ประวัติการรับประกันของลูกค้าหายไปด้วย
// "ระงับ" จึงทำหน้าที่แทนการลบ (soft delete) และตอนนี้กู้คืนได้แล้วถ้ากดพลาด
export default function Products() {
  const [products, setProducts] = useState([])
  const [showInactive, setShowInactive] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const [imageUrlInput, setImageUrlInput] = useState('')
  const [imageError, setImageError] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState(EMPTY_FORM)
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('category')
  const [sortDir, setSortDir] = useState('asc')

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
      setForm(EMPTY_FORM)
      await load()
    } catch (err) {
      setError('เพิ่มสินค้าไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    } finally {
      setSubmitting(false)
    }
  }

  function startEdit(p) {
    setEditingId(p.id)
    setEditForm({
      category: p.category,
      brand: p.brand,
      model: p.model,
      spec: p.spec ?? '',
      warranty_months: p.warranty_months,
    })
    setExpandedId(null)
  }

  async function handleSaveEdit(id) {
    setError('')
    try {
      await client.put(`/products/${id}`, {
        ...editForm,
        warranty_months: Number(editForm.warranty_months),
      })
      setEditingId(null)
      await load()
    } catch (err) {
      setError('บันทึกการแก้ไขไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    }
  }

  async function handleSuspend(p) {
    const ok = confirm(
      `ระงับ "${p.brand} ${p.model}" ?\n\n` +
        'สินค้าจะไม่แสดงในรายการปกติและเลือกไม่ได้ตอนรับสต็อก/สร้างคำขอสั่งซื้อ\n' +
        'แต่ประวัติการขายและการรับประกันของลูกค้ายังอยู่ครบ\n\n' +
        'กดดูได้ที่ช่อง "แสดงที่ถูกระงับด้วย" และกู้คืนภายหลังได้',
    )
    if (!ok) return
    await client.delete(`/products/${p.id}`)
    await load()
  }

  async function handleRestore(id) {
    await client.post(`/products/${id}/restore`)
    await load()
  }

  function toggleImages(id) {
    setImageError('')
    setImageUrlInput('')
    setEditingId(null)
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

  const q = search.trim().toLowerCase()
  const visibleProducts = products
    .filter((p) => {
      if (!q) return true
      return (
        p.category.toLowerCase().includes(q) ||
        p.brand.toLowerCase().includes(q) ||
        p.model.toLowerCase().includes(q) ||
        (p.spec ?? '').toLowerCase().includes(q)
      )
    })
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
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="rd-title mb-4">เพิ่มสินค้าใหม่</h1>
        <form onSubmit={handleSubmit} className="rd-card p-6 grid grid-cols-2 gap-3">
          <div>
            <label className="rd-label">หมวดหมู่</label>
            <select
              className="rd-input"
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
            <label className="rd-label">ระยะประกัน (เดือน)</label>
            <input
              type="number"
              min="1"
              className="rd-input"
              value={form.warranty_months}
              onChange={(e) => setForm({ ...form, warranty_months: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="rd-label">ยี่ห้อ</label>
            <input
              className="rd-input"
              value={form.brand}
              onChange={(e) => setForm({ ...form, brand: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="rd-label">รุ่น</label>
            <input
              className="rd-input"
              value={form.model}
              onChange={(e) => setForm({ ...form, model: e.target.value })}
              required
            />
          </div>
          <div className="col-span-2">
            <label className="rd-label">สเปก (ถ้ามี)</label>
            <input
              className="rd-input"
              value={form.spec}
              onChange={(e) => setForm({ ...form, spec: e.target.value })}
            />
          </div>
          {error && <p className="text-[#d03b3b] text-sm col-span-2">{error}</p>}
          <button type="submit" disabled={submitting} className="rd-btn col-span-2">
            {submitting ? 'กำลังเพิ่ม...' : 'เพิ่มสินค้า'}
          </button>
        </form>
      </div>

      <div>
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <h2 className="rd-title">รายการสินค้า</h2>
          <label className="text-sm text-ink-muted flex items-center gap-2">
            <input type="checkbox" checked={showInactive} onChange={(e) => setShowInactive(e.target.checked)} />
            แสดงที่ถูกระงับด้วย
          </label>
        </div>

        <div className="flex items-center justify-between mb-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="ค้นหาหมวดหมู่ / ยี่ห้อ / รุ่น / สเปก..."
            className="rd-input max-w-sm"
          />
          <p className="text-xs text-ink-muted ml-3 whitespace-nowrap">
            {visibleProducts.length} / {products.length} รายการ
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
                    align={col.align}
                    onClick={() => toggleSort(key)}
                  />
                ))}
                <th className="rd-th">รูปภาพ</th>
                <th className="rd-th text-right">จัดการ</th>
              </tr>
            </thead>
            <tbody>
              {visibleProducts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-ink-muted">
                    {search ? `ไม่พบสินค้าที่ตรงกับ "${search}"` : 'ยังไม่มีสินค้า'}
                  </td>
                </tr>
              ) : (
                visibleProducts.map((p) => (
                  <Fragment key={p.id}>
                    <tr className={`rd-tr ${!p.is_active ? 'bg-[#fafafa]' : ''}`}>
                      <td className="rd-td text-ink-muted">{p.category}</td>
                      <td className="rd-td">
                        {p.brand} {p.model}
                        {p.spec && <span className="block text-xs text-ink-muted">{p.spec}</span>}
                      </td>
                      <td className="rd-td text-right">{p.warranty_months}</td>
                      <td className="rd-td">
                        <span className={`rd-badge ${p.is_active ? 'rd-badge-approved' : 'rd-badge-muted'}`}>
                          {p.is_active ? 'ใช้งาน' : 'ระงับแล้ว'}
                        </span>
                      </td>
                      <td className="rd-td">
                        <button onClick={() => toggleImages(p.id)} className="rd-link text-xs">
                          {(p.images || []).length}/5 รูป
                        </button>
                      </td>
                      <td className="rd-td text-right whitespace-nowrap">
                        <button onClick={() => startEdit(p)} className="rd-link text-xs mr-3">
                          แก้ไข
                        </button>
                        {p.is_active ? (
                          <button
                            onClick={() => handleSuspend(p)}
                            className="text-[#d03b3b] text-xs hover:underline"
                          >
                            ระงับ
                          </button>
                        ) : (
                          <button
                            onClick={() => handleRestore(p.id)}
                            className="text-[#0a7d0a] text-xs hover:underline"
                          >
                            กู้คืน
                          </button>
                        )}
                      </td>
                    </tr>

                    {editingId === p.id && (
                      <tr className="rd-tr bg-ink-accentSoft/40">
                        <td colSpan={6} className="px-4 py-4">
                          <p className="text-sm font-medium text-ink-text mb-3">
                            แก้ไข: {p.brand} {p.model}
                          </p>
                          <div className="grid grid-cols-2 gap-3 max-w-2xl">
                            <div>
                              <label className="rd-label">หมวดหมู่</label>
                              <select
                                className="rd-input"
                                value={editForm.category}
                                onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                              >
                                {CATEGORIES.map((c) => (
                                  <option key={c} value={c}>
                                    {c}
                                  </option>
                                ))}
                              </select>
                            </div>
                            <div>
                              <label className="rd-label">ระยะประกัน (เดือน)</label>
                              <input
                                type="number"
                                min="1"
                                className="rd-input"
                                value={editForm.warranty_months}
                                onChange={(e) =>
                                  setEditForm({ ...editForm, warranty_months: e.target.value })
                                }
                              />
                            </div>
                            <div>
                              <label className="rd-label">ยี่ห้อ</label>
                              <input
                                className="rd-input"
                                value={editForm.brand}
                                onChange={(e) => setEditForm({ ...editForm, brand: e.target.value })}
                              />
                            </div>
                            <div>
                              <label className="rd-label">รุ่น</label>
                              <input
                                className="rd-input"
                                value={editForm.model}
                                onChange={(e) => setEditForm({ ...editForm, model: e.target.value })}
                              />
                            </div>
                            <div className="col-span-2">
                              <label className="rd-label">สเปก</label>
                              <input
                                className="rd-input"
                                value={editForm.spec}
                                onChange={(e) => setEditForm({ ...editForm, spec: e.target.value })}
                              />
                            </div>
                            <div className="col-span-2 flex gap-2">
                              <button onClick={() => handleSaveEdit(p.id)} className="rd-btn">
                                บันทึก
                              </button>
                              <button onClick={() => setEditingId(null)} className="rd-btn-secondary">
                                ยกเลิก
                              </button>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}

                    {expandedId === p.id && (
                      <tr className="rd-tr bg-ink-accentSoft/40">
                        <td colSpan={6} className="px-4 py-3">
                          <div className="flex flex-wrap gap-3 mb-3">
                            {(p.images || []).map((img) => (
                              <div key={img.id} className="relative">
                                <img
                                  src={img.image_url}
                                  alt=""
                                  className="w-20 h-20 object-cover rounded border border-ink-border"
                                />
                                <button
                                  onClick={() => handleDeleteImage(p.id, img.id)}
                                  className="absolute -top-2 -right-2 bg-[#d03b3b] text-white rounded-full w-5 h-5 text-xs leading-5"
                                  title="ลบรูปนี้"
                                >
                                  ×
                                </button>
                              </div>
                            ))}
                            {(p.images || []).length === 0 && (
                              <p className="text-sm text-ink-muted">ยังไม่มีรูปภาพ</p>
                            )}
                          </div>
                          {(p.images || []).length < 5 && (
                            <div className="flex gap-2 items-center">
                              <input
                                className="rd-input max-w-md"
                                placeholder="https://example.com/image.jpg"
                                value={imageUrlInput}
                                onChange={(e) => setImageUrlInput(e.target.value)}
                              />
                              <button
                                onClick={() => handleAddImage(p.id)}
                                disabled={!imageUrlInput}
                                className="rd-btn"
                              >
                                เพิ่มรูป
                              </button>
                            </div>
                          )}
                          {imageError && <p className="text-[#d03b3b] text-xs mt-2">{imageError}</p>}
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
