import { NavLink, Outlet, useNavigate } from 'react-router-dom'

function logout(navigate) {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('branch_id')
  navigate('/login')
}

const linkClass = ({ isActive }) =>
  `px-3 py-2 rounded text-sm ${isActive ? 'bg-brand-600 text-white' : 'text-brand-900 hover:bg-brand-100'}`

export default function BranchLayout() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-brand-50">
      <header className="bg-white border-b border-brand-100 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-brand-900">สาขา</span>
          <nav className="flex gap-1 ml-4">
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
