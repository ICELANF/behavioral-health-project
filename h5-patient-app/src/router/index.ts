import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

/**
 * Patient App (:5176) 已合并入 H5 主线 (:5173)
 * 所有路由重定向到 H5 等价页面
 * 日期: 2026-02-17 (P0-2 路由合并)
 * 移除时间: 2026-04-01
 */

// Patient App → H5 路径映射
const H5_BASE = (import.meta.env.VITE_H5_URL as string) || 'http://localhost:5173'
const REDIRECT_MAP: Record<string, string> = {
  '/':            '/',
  '/login':       '/login',
  '/register':    '/register',
  '/data-input':  '/health-records',
  '/history':     '/history-reports',
  '/analysis':    '/dashboard',
  '/settings':    '/account-settings',
  '/chat':        '/chat',
  '/health-data': '/dashboard',
}

function redirectToH5(h5Path: string) {
  window.location.href = `${H5_BASE}${h5Path}`
}

const routes: RouteRecordRaw[] = [
  // 保留一个空壳页面用于显示迁移提示（可选）
  {
    path: '/:pathMatch(.*)*',
    name: 'Deprecated',
    component: {
      template: `
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;font-family:system-ui;padding:24px;text-align:center">
          <h2 style="margin-bottom:16px">页面已迁移</h2>
          <p style="color:#666;margin-bottom:24px">该功能已整合到H5主端，正在为您跳转...</p>
          <a :href="targetUrl" style="color:#1890ff;text-decoration:underline">点击此处手动跳转</a>
        </div>
      `,
      computed: {
        targetUrl() {
          const path = (this as any).$route.path
          const mapped = REDIRECT_MAP[path] || '/'
          return `${H5_BASE}${mapped}`
        }
      },
      mounted() {
        const path = (this as any).$route.path
        // /result/:id → /v3/assessment/:id
        if (path.startsWith('/result/')) {
          const id = path.replace('/result/', '')
          redirectToH5(`/v3/assessment/${id}`)
          return
        }
        const mapped = REDIRECT_MAP[path] || '/'
        redirectToH5(mapped)
      }
    },
    meta: { title: '页面已迁移', requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to, _from, next) => {
  document.title = '行为健康平台 — 页面已迁移'
  next()
})

export default router
