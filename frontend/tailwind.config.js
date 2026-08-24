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
        // CR-010 — ธีมมืดเฉพาะหน้า Dashboard เท่านั้น (ดูเหตุผลใน docs/01-Requirements-Package.md)
        ink: {
          bg: '#0d0f17',
          surface: '#161925',
          surface2: '#1e2233',
          border: '#2a2f42',
          text: '#f4f5f9',
          muted: '#9297ab',
        },
      },
    },
  },
  plugins: [],
}
