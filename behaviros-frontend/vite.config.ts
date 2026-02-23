import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  preview: {
    port: 5175,
    host: '0.0.0.0',
  },
  server: {
    port: 5175,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/baps': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/mp': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
