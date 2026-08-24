import { useEffect, useState } from 'react'
import client from '../../api/client'

// FR-011, NFR-MAINT-01 — ค้นย้อนหลังว่าใครทำอะไร เมื่อไหร่
export default function AuditLog() {
  const [logs, setLogs] = useState([])
  const [entityType, setEntityType] = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    const params = entityType ? `?entity_type=${entityType}` : ''
    const { data } = await client.get(`/audit-log${params}`)
    setLogs(data)
    setLoading(false)
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entityType])

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold text-brand-900">Audit Log</h1>
        <select
          className="border border-brand-100 rounded px-3 py-1.5 text-sm"
          value={entityType}
          onChange={(e) => setEntityType(e.target.value)}
        >
          <option value="">ทุกประเภท</option>
          <option value="Product">Product</option>
          <option value="Item">Item</option>
          <option value="Sale">Sale</option>
          <option value="PurchaseRequest">PurchaseRequest</option>
          <option value="BranchSKU">BranchSKU</option>
        </select>
      </div>

      {loading ? (
        <p className="text-gray-500">กำลังโหลด...</p>
      ) : logs.length === 0 ? (
        <p className="text-gray-500 text-sm">ไม่มีข้อมูล</p>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-100 text-brand-900">
              <tr>
                <th className="text-left px-4 py-2">เวลา</th>
                <th className="text-left px-4 py-2">Action</th>
                <th className="text-left px-4 py-2">Entity</th>
                <th className="text-left px-4 py-2">ผู้ทำรายการ</th>
                <th className="text-left px-4 py-2">รายละเอียด</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-t border-brand-50">
                  <td className="px-4 py-2 whitespace-nowrap text-gray-500">
                    {new Date(log.occurred_at).toLocaleString('th-TH')}
                  </td>
                  <td className="px-4 py-2 font-medium">{log.action}</td>
                  <td className="px-4 py-2">
                    {log.entity_type} #{log.entity_id}
                  </td>
                  <td className="px-4 py-2">User #{log.actor_user_id}</td>
                  <td className="px-4 py-2 text-xs text-gray-500 max-w-xs truncate" title={JSON.stringify(log.after_value)}>
                    {JSON.stringify(log.after_value)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
