/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // CR-010 (ขยายขอบเขต 2026-08-24) — ธีมของ**ทั้งระบบ** อิงสีจริงจาก
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
