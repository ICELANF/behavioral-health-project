/**
 * router-patch.ts
 * 将此路由条目添加到 h5/src/router/index.ts 的路由数组中
 * 放在 /home 路由的同级
 */
import CoachRecruit from '@/views/coach-recruit/CoachRecruit.vue'

// 插入到 routes 数组：
export const coachRecruitRoute = {
  path: '/coach-recruit',
  name: 'CoachRecruit',
  component: CoachRecruit,
  meta: { title: '成为健康教练', requiresAuth: true },
}
