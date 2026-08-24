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
      localStorage.setItem('username', data.username)
      if (data.branch_id != null) {
        localStorage.setItem('branch_id', String(data.branch_id))
        localStorage.setItem('branch_name', data.branch_name ?? '')
      } else {
        localStorage.removeItem('branch_id')
        localStorage.removeItem('branch_name')
      }
      navigate(data.role === 'Admin' ? '/admin' : '/branch')
    } catch (err) {
      setError('Username หรือ Password ไม่ถูกต้อง')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="rd-page flex items-center justify-center p-6">
      <div className="rd-card p-8 w-full max-w-sm">
        <h1 className="rd-title text-xl mb-6">เข้าสู่ระบบ Backoffice</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="rd-label">Username</label>
            <input
              className="rd-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div>
            <label className="rd-label">Password</label>
            <input
              type="password"
              className="rd-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-[#d03b3b] text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="rd-btn w-full"
          >
            {loading ? 'กำลังเข้าสู่ระบบ...' : 'เข้าสู่ระบบ'}
          </button>
        </form>
        <a href="/" className="block text-center rd-link text-sm mt-4">
          ← กลับหน้าเช็คประกันสาธารณะ
        </a>
      </div>
    </main>
  )
}
