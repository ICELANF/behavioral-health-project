import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    react({
      include: [
        /src\/components\/react\/.*\.[tj]sx?$/,
        /src\/contexts\/.*\.[tj]sx?$/,
        /src\/hooks\/.*\.[tj]sx?$/,
      ],
    }),
  ],
  server: {
    port: 5182,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@react': resolve(__dirname, 'src/components/react'),
    },
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-dom/client', 'framer-motion', 'lucide-react'],
  },
})
