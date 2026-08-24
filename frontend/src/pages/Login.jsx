import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

// FR-007 — Backoffice login พร้อมกำหนดสิทธิ์ตาม role
export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await client.post('/auth/login', { username, password })
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('role', data.role)
      if (data.branch_id != null) {
        localStorage.setItem('branch_id', String(data.branch_id))
      } else {
        localStorage.removeItem('branch_id')
      }
      navigate(data.role === 'Admin' ? '/admin' : '/branch')
    } catch (err) {
      setError('Username หรือ Password ไม่ถูกต้อง')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-brand-50 flex items-center justify-center p-6">
      <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-sm">
        <h1 className="text-xl font-semibold text-brand-900 mb-6">เข้าสู่ระบบ Backoffice</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">Username</label>
            <input
              className="w-full border border-brand-100 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-600"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Password</label>
            <input
              type="password"
              className="w-full border border-brand-100 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-600"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 text-white py-2 rounded hover:bg-brand-900 transition disabled:opacity-50"
          >
            {loading ? 'กำลังเข้าสู่ระบบ...' : 'เข้าสู่ระบบ'}
          </button>
        </form>
        <a href="/" className="block text-center text-sm text-brand-600 mt-4 hover:underline">
          ← กลับหน้าเช็คประกันสาธารณะ
        </a>
      </div>
    </main>
  )
}
