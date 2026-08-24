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
      },
    },
  },
  plugins: [],
}
