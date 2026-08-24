/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // NFR-USE-01 — โทนขาว-ฟ้าสะอาดตา
        brand: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          600: '#0284c7',
          900: '#0c4a6e',
        },
        // CR-010 (แก้ไข 2026-08-24) — ธีมหน้า Dashboard เท่านั้น อิงสีจริงจาก
        // dashboard.render.com (ตรวจด้วย getComputedStyle จริง ไม่ใช่เดา) ซึ่งเป็นธีม
        // "สว่าง" ไม่ใช่ธีมมืดอย่างที่ตั้งใจไว้รอบแรกจากภาพตัวอย่างที่ไม่เกี่ยวกับ Render จริง
        ink: {
          bg: '#f9f9f7', // page plane
          surface: '#fcfcfb', // card surface (เกือบขาวแต่ไม่ใช่ขาวจ๋า ตาม Render)
          border: '#e5e7eb', // ตรงกับ rgb(229,231,235) ที่ Render ใช้จริง
          text: '#0b0b0b',
          muted: '#6b6b6b',
          accent: '#7a3ff1', // สีม่วงหลักของ Render (ตรวจจาก element จริง)
          accentSoft: '#f4f0ff', // lavender highlight ของ active state
        },
      },
    },
  },
  plugins: [],
}
