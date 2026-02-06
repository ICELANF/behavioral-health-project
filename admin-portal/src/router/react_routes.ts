import type { RouteRecordRaw } from 'vue-router'

/**
 * React集成页面路由配置
 * 这些路由使用ReactWrapper组件桥接React和Vue
 */
export const reactRoutes: RouteRecordRaw[] = [
  // ============ React导航页面 ============
  {
    path: '/react',
    name: 'ReactNavigation',
    component: () => import('@/views/ReactNavigation.vue'),
    meta: {
      title: 'React页面导航',
      requiresAuth: false,
      description: 'React集成页面导航中心'
    }
  },

  // ============ React演示和测试页面 ============
  {
    path: '/react/demo',
    name: 'ReactDemo',
    component: () => import('@/views/react/DemoPage.vue'),
    meta: {
      title: 'React演示页',
      requiresAuth: false,
      description: '展示React组件集成效果，包含逻辑流、决策规则等'
    }
  },

  // ============ 专家工作区 ============
  {
    path: '/expert/workspace',
    name: 'ExpertWorkspace',
    component: () => import('@/views/react/ExpertWorkspace.vue'),
    meta: {
      title: '专家工作区',
      requiresAuth: true,
      role: 'expert',
      description: '专家专用工作台，包含审核、督导等功能'
    }
  },

  // ============ 成长之旅 ============
  {
    path: '/journey',
    name: 'JourneyPage',
    component: () => import('@/views/react/JourneyPage.vue'),
    meta: {
      title: '成长之旅',
      requiresAuth: false,
      description: '用户行为改变成长历程可视化'
    }
  },

  // ============ 决策追踪 ============
  {
    path: '/trace',
    name: 'TracePage',
    component: () => import('@/views/react/TracePage.vue'),
    meta: {
      title: '决策追踪',
      requiresAuth: true,
      description: '查看AI决策过程、逻辑链路和规则执行'
    }
  },
  {
    path: '/trace/:traceId',
    name: 'TraceDetail',
    component: () => import('@/views/react/TracePage.vue'),
    meta: {
      title: '决策详情',
      requiresAuth: true,
      description: '查看单个决策的详细追踪信息'
    }
  },

  // ============ 管理员进化页 ============
  {
    path: '/admin/evolution',
    name: 'AdminEvolution',
    component: () => import('@/views/react/AdminEvolution.vue'),
    meta: {
      title: '系统演进',
      requiresAuth: true,
      role: 'admin',
      description: '查看系统架构演进和技术栈变化'
    }
  }
]
