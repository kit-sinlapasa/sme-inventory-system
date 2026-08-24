import { NavLink, Outlet, useNavigate } from 'react-router-dom'

function logout(navigate) {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('branch_id')
  navigate('/login')
}

// CR-010 — nav สไตล์ Render: พื้นขาว เส้นขอบบาง เมนู active เป็นพื้นม่วงอ่อน + ตัวหนังสือม่วง
// (Render ใช้ lavender highlight แบบนี้กับเมนูที่เลือกอยู่ ไม่ใช่พื้นทึบสีเข้ม)
const linkClass = ({ isActive }) =>
  `px-3 py-1.5 rounded-lg text-sm transition ${
    isActive ? 'bg-ink-accentSoft text-ink-accent font-medium' : 'text-ink-muted hover:text-ink-text'
  }`

export default function AdminLayout() {
  const navigate = useNavigate()

  return (
    <div className="rd-page">
      <header className="bg-ink-surface border-b border-ink-border px-6 py-3 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-ink-text">Backoffice</span>
          <nav className="flex gap-1 ml-4 flex-wrap">
            <NavLink to="/admin" end className={linkClass}>
              สต็อกรวม
            </NavLink>
            <NavLink to="/admin/products" className={linkClass}>
              สินค้า
            </NavLink>
            <NavLink to="/admin/receive" className={linkClass}>
              รับสต็อก
            </NavLink>
            <NavLink to="/admin/requests" className={linkClass}>
              คำขอสั่งซื้อ
            </NavLink>
            <NavLink to="/admin/audit-log" className={linkClass}>
              Audit Log
            </NavLink>
          </nav>
        </div>
        <button onClick={() => logout(navigate)} className="text-sm text-ink-muted hover:text-[#d03b3b]">
          ออกจากระบบ
        </button>
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
