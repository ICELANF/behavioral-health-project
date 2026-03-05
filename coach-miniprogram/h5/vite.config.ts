import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // Treat uni-app custom elements as native
          isCustomElement: (tag) =>
            ['scroll-view', 'swiper', 'swiper-item', 'picker', 'navigator', 'rich-text', 'web-view'].includes(tag),
        },
      },
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@dcloudio/uni-app': resolve(__dirname, 'src/compat/uni.ts'),
    },
  },
  server: {
    port: 3010,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  css: {
    postcss: {
      plugins: [
        // rpx → vw conversion: 750rpx = 100vw, so 1rpx = 100/750 vw
        {
          postcssPlugin: 'rpx-to-vw',
          Declaration(decl) {
            if (decl.value.includes('rpx')) {
              decl.value = decl.value.replace(/(\d+(\.\d+)?)rpx/g, (_match, num) => {
                const vw = (parseFloat(num) / 750 * 100).toFixed(4)
                return `${vw}vw`
              })
            }
          },
        },
      ],
    },
  },
  build: {
    outDir: 'dist',
  },
})
