import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // dev เท่านั้น — production ต้องตั้ง reverse proxy หรือ VITE_API_URL จริง
      '/api': 'http://localhost:8000',
    },
  },
})
