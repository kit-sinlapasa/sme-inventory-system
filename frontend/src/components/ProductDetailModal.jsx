import { useEffect, useState } from 'react'
import client from '../api/client'

// รายละเอียดสินค้าแบบเต็ม — เปิดจากการคลิกแถวในตารางสต็อก
// ใช้ endpoint ที่มีอยู่แล้วทั้งหมด: /products/{id} (ข้อมูล+รูป FR-013),
// /stock?sku_id= (ยอดคงเหลือแยกสาขา FR-003), /items?sku_id= (S/N รายชิ้น FR-002)
// NFR-SEC-02 — ทั้ง 3 endpoint บังคับ scope ที่ server แล้ว พนักงานสาขาจะเห็นเฉพาะสาขาตัวเอง
// โดยอัตโนมัติ ไม่ต้องกรองซ้ำฝั่ง client (และกรองฝั่ง client อย่างเดียวก็ไม่ปลอดภัยอยู่แล้ว)
export default function ProductDetailModal({ skuId, onClose }) {
  const [product, setProduct] = useState(null)
  const [stockRows, setStockRows] = useState([])
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError('')
      try {
        const [productRes, stockRes, itemsRes] = await Promise.all([
          client.get(`/products/${skuId}`),
          client.get(`/stock?sku_id=${skuId}`),
          client.get(`/items?sku_id=${skuId}`),
        ])
        if (cancelled) return
        setProduct(productRes.data)
        setStockRows(stockRes.data)
        setItems(itemsRes.data)
      } catch (err) {
        if (!cancelled) setError('โหลดรายละเอียดสินค้าไม่สำเร็จ')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [skuId])

  // ปิดด้วย Esc ตามพฤติกรรม modal ที่ผู้ใช้คาดหวัง
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const inStock = items.filter((i) => i.status === 'InStock')
  const sold = items.filter((i) => i.status === 'Sold')

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 sm:p-8"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl rounded-xl bg-ink-surface border border-ink-border shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between border-b border-ink-border px-5 py-4">
          <div>
            <p className="text-xs text-ink-muted">{product?.category ?? '—'}</p>
            <h2 className="text-lg font-semibold text-ink-text">
              {product ? `${product.brand} ${product.model}` : 'กำลังโหลด...'}
            </h2>
          </div>
          <button
            onClick={onClose}
            aria-label="ปิด"
            className="rounded px-2 text-xl leading-none text-ink-muted hover:text-ink-text"
          >
            ×
          </button>
        </div>

        <div className="px-5 py-4 space-y-5">
          {loading && <p className="text-ink-muted text-sm">กำลังโหลด...</p>}
          {error && <p className="text-[#d03b3b] text-sm">{error}</p>}

          {product && !loading && (
            <>
              <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <Field label="หมวดหมู่" value={product.category} />
                <Field label="ยี่ห้อ" value={product.brand} />
                <Field label="รุ่น" value={product.model} />
                <Field label="ระยะประกัน" value={`${product.warranty_months} เดือน`} />
                <Field label="สเปก" value={product.spec || '—'} className="col-span-2" />
                <Field label="สถานะสินค้า" value={product.is_active ? 'ใช้งานอยู่' : 'ระงับแล้ว'} />
                <Field label="รหัสสินค้า (SKU)" value={`#${product.id}`} />
              </section>

              {product.images?.length > 0 && (
                <section>
                  <p className="text-sm font-medium text-ink-text mb-2">รูปสินค้า ({product.images.length}/5)</p>
                  <div className="flex flex-wrap gap-2">
                    {product.images.map((img) => (
                      <img
                        key={img.id}
                        src={img.image_url}
                        alt=""
                        className="h-24 w-24 rounded border border-ink-border object-cover"
                      />
                    ))}
                  </div>
                </section>
              )}

              <section>
                <p className="text-sm font-medium text-ink-text mb-2">ยอดคงเหลือแยกตามสาขา</p>
                {stockRows.length === 0 ? (
                  <p className="text-sm text-ink-muted">ไม่มีสต็อกคงเหลือ</p>
                ) : (
                  <table className="w-full text-sm">
                    <thead className="text-ink-muted">
                      <tr>
                        <th className="text-left py-1 font-medium">สาขา</th>
                        <th className="text-right py-1 font-medium">คงเหลือ</th>
                        <th className="text-right py-1 font-medium">จุดสั่งซื้อ</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stockRows.map((row) => {
                        const low = row.reorder_point != null && row.on_hand <= row.reorder_point
                        return (
                          <tr key={row.branch_id} className="border-t border-ink-border">
                            <td className="py-1.5 text-ink-text">{row.branch_name}</td>
                            <td className="py-1.5 text-right font-medium text-ink-text">
                              {row.on_hand}
                              {low && <span className="ml-2 text-[#d03b3b] text-xs">⚠ ใกล้หมด</span>}
                            </td>
                            <td className="py-1.5 text-right text-ink-muted">{row.reorder_point ?? '—'}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                )}
              </section>

              <section>
                <p className="text-sm font-medium text-ink-text mb-2">
                  หมายเลขซีเรียล (S/N) — พร้อมขาย {inStock.length} ชิ้น · ขายแล้ว {sold.length} ชิ้น
                </p>
                {items.length === 0 ? (
                  <p className="text-sm text-ink-muted">ยังไม่เคยรับสินค้ารุ่นนี้เข้าสต็อก</p>
                ) : (
                  <div className="max-h-56 overflow-y-auto rounded border border-ink-border">
                    <table className="w-full text-sm">
                      <thead className="sticky top-0 bg-ink-surface text-ink-muted">
                        <tr>
                          <th className="text-left px-3 py-1.5 font-medium">S/N</th>
                          <th className="text-left px-3 py-1.5 font-medium">สถานะ</th>
                          <th className="text-left px-3 py-1.5 font-medium">รับเข้าเมื่อ</th>
                        </tr>
                      </thead>
                      <tbody>
                        {items.map((item) => (
                          <tr key={item.id} className="border-t border-ink-border">
                            <td className="px-3 py-1.5 font-mono text-xs text-ink-text">{item.serial_number}</td>
                            <td className="px-3 py-1.5">
                              <span
                                className={`text-xs px-2 py-0.5 rounded ${
                                  item.status === 'InStock'
                                    ? 'bg-[#e8f5e9] text-[#0ca30c]'
                                    : 'bg-[#f0f0f0] text-ink-muted'
                                }`}
                              >
                                {item.status === 'InStock' ? 'พร้อมขาย' : 'ขายแล้ว'}
                              </span>
                            </td>
                            <td className="px-3 py-1.5 text-ink-muted whitespace-nowrap">
                              {new Date(item.received_at).toLocaleString('th-TH')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                {items.length >= 200 && (
                  <p className="mt-2 text-xs text-ink-muted">
                    แสดง 200 รายการล่าสุดเท่านั้น (จำกัดไว้กันดึงข้อมูลทั้งคลังพร้อมกัน)
                  </p>
                )}
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function Field({ label, value, className = '' }) {
  return (
    <div className={className}>
      <p className="text-xs text-ink-muted mb-0.5">{label}</p>
      <p className="text-sm text-ink-text">{value}</p>
    </div>
  )
}
