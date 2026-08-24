import { Navigate } from 'react-router-dom'

/**
 * ป้องกัน route ฝั่ง frontend ตาม role — ใช้ตอนสร้างหน้า branch/admin (สัปดาห์ 3+)
 *
 * ⚠️ นี่คือ UX convenience เท่านั้น (ซ่อนเมนู/redirect ให้ผู้ใช้ทั่วไปไม่หลง)
 * ไม่ใช่ security control จริง — การบังคับสิทธิ์จริงต้องอยู่ที่ server
 * (ดู backend/app/deps.py require_role) ตาม NFR-SEC-02 และ STRIDE-T mitigation
 */
export default function RouteGuard({ role, children }) {
  const token = localStorage.getItem('token')
  const userRole = localStorage.getItem('role')

  if (!token) {
    return <Navigate to="/login" replace />
  }
  if (role && userRole !== role) {
    return <Navigate to="/" replace />
  }
  return children
}
