/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  corePlugins: {
    preflight: false, // Avoid breaking Ant Design Vue styles
  },
  theme: {
    extend: {},
  },
  plugins: [],
}
