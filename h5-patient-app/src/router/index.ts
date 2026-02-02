import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { storage } from '@/utils/storage'
import { showToast } from 'vant'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginPage.vue'),
    meta: {
      title: '用户登录',
      requiresAuth: false
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterPage.vue'),
    meta: {
      title: '用户注册',
      requiresAuth: false
    }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomePage.vue'),
    meta: {
      title: '首页',
      requiresAuth: true
    }
  },
  {
    path: '/data-input',
    name: 'DataInput',
    component: () => import('@/views/DataInputPage.vue'),
    meta: {
      title: '数据录入',
      requiresAuth: true
    }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/HistoryPage.vue'),
    meta: {
      title: '评估历史',
      requiresAuth: true
    }
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('@/views/DataAnalysisPage.vue'),
    meta: {
      title: '数据分析',
      requiresAuth: true
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsPage.vue'),
    meta: {
      title: '个人设置',
      requiresAuth: true
    }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatPage.vue'),
    meta: {
      title: 'AI健康助手',
      requiresAuth: true
    }
  },
  {
    path: '/health-data',
    name: 'HealthData',
    component: () => import('@/views/HealthDataPage.vue'),
    meta: {
      title: '健康数据',
      requiresAuth: true
    }
  },
  {
    path: '/result/:id',
    name: 'Result',
    component: () => import('@/views/ResultPage.vue'),
    meta: {
      title: '评估结果',
      requiresAuth: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - ${import.meta.env.VITE_APP_TITLE || '行为健康平台'}`
  }

  // 检查是否需要认证
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  if (requiresAuth) {
    // 需要认证的路由，检查Token
    const token = storage.token.get()

    if (!token) {
      // 未登录，跳转到登录页
      showToast('请先登录')
      next({
        path: '/login',
        query: { redirect: to.fullPath } // 保存目标路由，登录后跳转
      })
    } else {
      next()
    }
  } else {
    // 不需要认证的路由
    const token = storage.token.get()

    // 如果已登录且访问登录/注册页，重定向到首页
    if (token && (to.path === '/login' || to.path === '/register')) {
      next('/')
    } else {
      next()
    }
  }
})

export default router
