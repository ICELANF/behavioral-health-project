import type { RouteRecordRaw } from 'vue-router'

export const portalRoutes: RouteRecordRaw[] = [
  {
    path: '/portal/public',
    name: 'PublicPortal',
    component: () => import('@/views/portals/PublicPortal.vue'),
    meta: { accessContext: 'public', sourceUI: 'UI-1', title: '行为健康科普入口', requiresAuth: false }
  },
  {
    path: '/portal/medical',
    name: 'MedicalAssistant',
    component: () => import('@/views/portals/MedicalAssistant.vue'),
    meta: { accessContext: 'medical', sourceUI: 'UI-3', title: '基层医护处方助手', requiresAuth: true }
  }
]
