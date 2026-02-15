/**
 * BehaviorOS — 行为处方路由配置
 * ====================================
 * 增量路由, 合并到主路由
 *
 * 使用方式 (在主 router/index.ts 中):
 *   import { rxRoutes } from './rx-routes'
 *   routes.push(...rxRoutes)
 */

import type { RouteRecordRaw } from 'vue-router'

export const rxRoutes: RouteRecordRaw[] = [
  {
    path: '/rx',
    name: 'RxModule',
    redirect: '/rx/dashboard',
    meta: {
      requiresAuth: true,
      requiredRole: 'coach', // coach 及以上角色
      title: '行为处方',
    },
    children: [
      {
        path: 'dashboard',
        name: 'RxDashboard',
        component: () => import('../views/RxDashboard.vue'),
        meta: {
          title: '处方仪表盘',
          icon: 'MedicineBoxOutlined',
          keepAlive: true,
        },
      },
      {
        path: 'compute/:userId?',
        name: 'RxCompute',
        component: () => import('../views/RxDashboard.vue'),
        meta: {
          title: '计算处方',
          icon: 'ThunderboltOutlined',
        },
        props: true,
      },
      {
        path: 'history/:userId',
        name: 'RxHistory',
        component: () => import('../views/RxDashboard.vue'),
        meta: {
          title: '处方历史',
          icon: 'HistoryOutlined',
        },
        props: true,
      },
      {
        path: 'detail/:rxId',
        name: 'RxDetail',
        component: () => import('../views/RxDashboard.vue'),
        meta: {
          title: '处方详情',
          icon: 'FileTextOutlined',
        },
        props: true,
      },
      {
        path: 'agents',
        name: 'RxAgents',
        component: () => import('../views/RxDashboard.vue'),
        meta: {
          title: 'Agent 集群',
          icon: 'RobotOutlined',
        },
      },
      {
        path: 'strategies',
        name: 'RxStrategies',
        component: () => import('../views/RxDashboard.vue'),
        meta: {
          title: '策略模板库',
          icon: 'AppstoreOutlined',
        },
      },
    ],
  },
]

/**
 * 路由守卫: 检查角色权限
 * 在主路由 beforeEach 中调用
 */
export function checkRxPermission(
  to: any,
  userRole: string
): boolean {
  const requiredRole = to.meta?.requiredRole
  if (!requiredRole) return true

  const roleLevel: Record<string, number> = {
    observer: 0,
    sharer: 1,
    coach: 2,
    expert: 3,
    admin: 4,
    superadmin: 5,
  }

  return (roleLevel[userRole] || 0) >= (roleLevel[requiredRole] || 0)
}

/**
 * 菜单配置 (用于侧边栏渲染)
 */
export const rxMenuConfig = {
  key: 'rx',
  label: '行为处方',
  icon: 'MedicineBoxOutlined',
  children: [
    { key: 'rx-dashboard', label: '处方仪表盘', path: '/rx/dashboard' },
    { key: 'rx-agents', label: 'Agent 集群', path: '/rx/agents' },
    { key: 'rx-strategies', label: '策略模板库', path: '/rx/strategies' },
  ],
}

export default rxRoutes
