/**
 * BehaviorOS V4.0 — 主路由
 * 角色分流 + 权限守卫 + 模块化路由注册
 */

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { UserRole, ROLE_LEVEL } from '@/types'

// =====================================================================
// 路由定义
// =====================================================================

const routes: RouteRecordRaw[] = [
  // ----- 公开页面 -----
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { public: true, title: '注册' },
  },

  // ----- 主布局（需登录）-----
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      // 首页 — 根据角色自动分流
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/HomeView.vue'),
        meta: { title: '首页' },
      },

      // ----- 用户端页面 -----
      {
        path: 'journey',
        name: 'Journey',
        component: () => import('@/views/JourneyView.vue'),
        meta: { title: '我的旅程' },
      },
      {
        path: 'assessment',
        name: 'Assessment',
        component: () => import('@/modules/assessment/views/AssessmentView.vue'),
        meta: { title: '健康评估' },
      },
      {
        path: 'agent',
        name: 'AgentChat',
        component: () => import('@/modules/agent/views/AgentChatView.vue'),
        meta: { title: 'AI助手' },
      },
      {
        path: 'actions',
        name: 'Actions',
        component: () => import('@/modules/behavior/views/ActionsView.vue'),
        meta: { title: '今日行动' },
      },
      {
        path: 'challenges',
        name: 'Challenges',
        component: () => import('@/views/ChallengesView.vue'),
        meta: { title: '挑战打卡' },
      },
      {
        path: 'learning',
        name: 'Learning',
        component: () => import('@/views/LearningView.vue'),
        meta: { title: '学习成长' },
      },
      {
        path: 'health-data',
        name: 'HealthData',
        component: () => import('@/views/HealthDataView.vue'),
        meta: { title: '健康数据' },
      },
      {
        path: 'points',
        name: 'Points',
        component: () => import('@/views/PointsView.vue'),
        meta: { title: '我的积分' },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/ProfileView.vue'),
        meta: { title: '个人设置' },
      },

      // ----- 教练端页面 (coach+) -----
      {
        path: 'coach',
        name: 'CoachDashboard',
        component: () => import('@/modules/coach/views/CoachDashboardView.vue'),
        meta: { title: '教练工作台', minRole: UserRole.COACH },
      },
      {
        path: 'coach/clients',
        name: 'CoachClients',
        component: () => import('@/modules/coach/views/ClientsView.vue'),
        meta: { title: '我的学员', minRole: UserRole.COACH },
      },

      // ----- Rx 模块 (coach+) — 对接已有 Rx UI -----
      {
        path: 'rx',
        redirect: '/rx/dashboard',
        meta: { minRole: UserRole.COACH },
        children: [
          {
            path: 'dashboard',
            name: 'RxDashboard',
            component: () => import('@/modules/rx/views/RxDashboard.vue'),
            meta: { title: '行为处方', minRole: UserRole.COACH },
          },
        ],
      },

      // ----- 管理端页面 (admin) -----
      {
        path: 'admin',
        name: 'AdminDashboard',
        component: () => import('@/modules/admin/views/AdminDashboardView.vue'),
        meta: { title: '管理后台', minRole: UserRole.ADMIN },
      },
    ],
  },

  // ----- 404 -----
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { public: true, title: '页面未找到' },
  },
]

// =====================================================================
// 创建路由
// =====================================================================

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// =====================================================================
// 全局守卫
// =====================================================================

router.beforeEach(async (to, _from, next) => {
  // 设置页面标题
  document.title = `${to.meta.title || ''} - 行健平台`.replace(/^ - /, '')

  // 公开页面直接放行
  if (to.meta.public) return next()

  // 动态导入 auth store (避免循环依赖)
  const { useAuthStore } = await import('@/stores/auth')
  const auth = useAuthStore()

  // 初始化 (首次加载时验证 token)
  await auth.initialize()

  // 未登录 → 跳转登录
  if (to.meta.requiresAuth !== false && !auth.isLoggedIn) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }

  // 角色权限检查
  if (to.meta.minRole) {
    const minLevel = ROLE_LEVEL[to.meta.minRole as UserRole] || 0
    if (auth.roleLevel < minLevel) {
      return next({ name: 'Home' })
    }
  }

  next()
})

export default router

// =====================================================================
// 路由元类型扩展
// =====================================================================

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean
    requiresAuth?: boolean
    title?: string
    minRole?: UserRole
    keepAlive?: boolean
    icon?: string
  }
}
