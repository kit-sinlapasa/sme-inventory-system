import { Routes, Route } from 'react-router-dom'

import RouteGuard from './components/RouteGuard'
import WarrantyCheck from './pages/public/WarrantyCheck'
import Login from './pages/Login'

import BranchLayout from './layouts/BranchLayout'
import BranchDashboard from './pages/branch/Dashboard'
import RecordSale from './pages/branch/RecordSale'
import BranchRequests from './pages/branch/Requests'

import AdminLayout from './layouts/AdminLayout'
import AdminDashboard from './pages/admin/Dashboard'
import Products from './pages/admin/Products'
import ReceiveStock from './pages/admin/ReceiveStock'
import PurchaseRequests from './pages/admin/PurchaseRequests'
import AuditLog from './pages/admin/AuditLog'

function App() {
  return (
    <Routes>
      {/* Public zone — ไม่ต้อง login (FR-006) */}
      <Route path="/" element={<WarrantyCheck />} />
      <Route path="/login" element={<Login />} />

      {/* Branch zone — ต้อง login role=BranchStaff (FR-008) */}
      <Route
        path="/branch"
        element={
          <RouteGuard role="BranchStaff">
            <BranchLayout />
          </RouteGuard>
        }
      >
        <Route index element={<BranchDashboard />} />
        <Route path="sell" element={<RecordSale />} />
        <Route path="requests" element={<BranchRequests />} />
      </Route>

      {/* Admin zone — ต้อง login role=Admin */}
      <Route
        path="/admin"
        element={
          <RouteGuard role="Admin">
            <AdminLayout />
          </RouteGuard>
        }
      >
        <Route index element={<AdminDashboard />} />
        <Route path="products" element={<Products />} />
        <Route path="receive" element={<ReceiveStock />} />
        <Route path="requests" element={<PurchaseRequests />} />
        <Route path="audit-log" element={<AuditLog />} />
      </Route>
    </Routes>
  )
}

export default App
