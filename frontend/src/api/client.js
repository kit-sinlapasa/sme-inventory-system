import axios from 'axios'

const client = axios.create({ baseURL: '/api' })

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
