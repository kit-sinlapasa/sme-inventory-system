import { Routes, Route } from 'react-router-dom'
import WarrantyCheck from './pages/public/WarrantyCheck'

// TODO สัปดาห์ 3+: เพิ่มหน้า branch/ และ admin/ พร้อม RouteGuard ตาม role
// import RouteGuard from './components/RouteGuard'
// import BranchDashboard from './pages/branch/Dashboard'
// import AdminDashboard from './pages/admin/Dashboard'

function App() {
  return (
    <Routes>
      {/* Public zone — ไม่ต้อง login (FR-006) */}
      <Route path="/" element={<WarrantyCheck />} />

      {/* Branch zone — ต้อง login role=BranchStaff (FR-008) */}
      {/* <Route path="/branch/*" element={
        <RouteGuard role="BranchStaff"><BranchDashboard /></RouteGuard>
      } /> */}

      {/* Admin zone — ต้อง login role=Admin */}
      {/* <Route path="/admin/*" element={
        <RouteGuard role="Admin"><AdminDashboard /></RouteGuard>
      } /> */}
    </Routes>
  )
}

export default App
