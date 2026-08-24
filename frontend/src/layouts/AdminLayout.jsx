import { NavLink, Outlet, useNavigate } from 'react-router-dom'

function logout(navigate) {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('branch_id')
  navigate('/login')
}

const linkClass = ({ isActive }) =>
  `px-3 py-2 rounded text-sm ${isActive ? 'bg-brand-600 text-white' : 'text-brand-900 hover:bg-brand-100'}`

export default function AdminLayout() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-brand-50">
      <header className="bg-white border-b border-brand-100 px-6 py-3 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-brand-900">Backoffice</span>
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
        <button onClick={() => logout(navigate)} className="text-sm text-gray-500 hover:text-red-600">
          ออกจากระบบ
        </button>
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
