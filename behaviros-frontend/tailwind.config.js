/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef8f4',
          100: '#d5ede3',
          200: '#addbc9',
          300: '#78c2a7',
          400: '#4aa883',
          500: '#2d8e69',
          600: '#207254',
          700: '#1b5c45',
          800: '#184938',
          900: '#153d2f',
        },
        warm: {
          50: '#fdf8f3',
          100: '#faeee0',
          200: '#f4d9bc',
          300: '#edc08e',
          400: '#e5a05e',
          500: '#df863c',
          600: '#d07031',
          700: '#ad5829',
          800: '#8b4727',
          900: '#713c23',
        },
      },
      fontFamily: {
        display: ['"Noto Serif SC"', 'serif'],
        body: ['"Noto Sans SC"', '"PingFang SC"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
    },
  },
  plugins: [],
  // Ant Design Vue compatibility: don't purge ant classes
  safelist: [{ pattern: /^ant-/ }],
}
