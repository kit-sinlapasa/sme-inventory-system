import axios from 'axios'

// Local dev: ว่างไว้ ใช้ '/api' relative path ผ่าน Vite proxy (vite.config.js)
// Production (Render/Cloudflare Pages แยก origin จาก backend): ต้องตั้ง VITE_API_URL
// ตอน build เช่น https://sme-inventory-api.onrender.com/api — ไม่งั้นทุก request จะ 404
// เพราะ frontend กับ backend อยู่คนละ origin กัน
const client = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api' })

// แนบ JWT ให้ทุก request อัตโนมัติ (ถ้ามี token เก็บไว้)
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 401 → เคลียร์ token แล้วเด้งกลับหน้า login (ทำตอนสัปดาห์ 3 เมื่อมีหน้า branch/admin จริง)
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
    }
    return Promise.reject(error)
  },
)

export default client
