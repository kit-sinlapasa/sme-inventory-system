import { NavLink, Outlet, useNavigate } from 'react-router-dom'

function logout(navigate) {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('branch_id')
  localStorage.removeItem('branch_name')
  localStorage.removeItem('username')
  navigate('/login')
}

// CR-010 — ใช้ nav สไตล์เดียวกับ AdminLayout เพื่อให้ทั้งระบบหน้าตาตรงกัน
const linkClass = ({ isActive }) =>
  `px-3 py-1.5 rounded-lg text-sm transition ${
    isActive ? 'bg-ink-accentSoft text-ink-accent font-medium' : 'text-ink-muted hover:text-ink-text'
  }`

export default function BranchLayout() {
  const navigate = useNavigate()
  // แสดงชื่อสาขาที่กำลังทำงานอยู่ — สำคัญเพราะทุก action (ขาย/ขอสั่งซื้อ) ผูกกับสาขานี้เสมอ
  // ถ้ามีหลายสาขาแล้วไม่บอก ผู้ใช้จะไม่รู้ว่ากำลังบันทึกเข้าสาขาไหน
  const branchName = localStorage.getItem('branch_name') || 'สาขา'
  const username = localStorage.getItem('username') || ''

  return (
    <div className="rd-page">
      <header className="bg-ink-surface border-b border-ink-border px-6 py-3 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-ink-text">{branchName}</span>
          <nav className="flex gap-1 ml-4 flex-wrap">
            <NavLink to="/branch" end className={linkClass}>
              สต็อก
            </NavLink>
            <NavLink to="/branch/sell" className={linkClass}>
              บันทึกขาย
            </NavLink>
            <NavLink to="/branch/requests" className={linkClass}>
              คำขอสั่งซื้อ
            </NavLink>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-ink-muted">
            {username} · <span className="text-ink-text">{branchName}</span>
          </span>
          <button onClick={() => logout(navigate)} className="text-sm text-ink-muted hover:text-[#d03b3b]">
            ออกจากระบบ
          </button>
        </div>
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
