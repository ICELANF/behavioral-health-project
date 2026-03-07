import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory('/agent/'),
  routes: [
    { path: '/login', component: () => import('@/views/Login.vue') },
    // Onboarding (MVEP 10-minute flow)
    { path: '/onboarding', component: () => import('@/views/onboarding/Setup.vue') },
    // Main workstation
    { path: '/', component: () => import('@/views/Dashboard.vue') },
    // Knowledge management
    { path: '/knowledge', component: () => import('@/views/knowledge/List.vue') },
    { path: '/knowledge/upload', component: () => import('@/views/knowledge/Upload.vue') },
    { path: '/knowledge/pending', component: () => import('@/views/knowledge/Pending.vue') },
    { path: '/knowledge/rules', component: () => import('@/views/knowledge/Rules.vue') },
    { path: '/knowledge/health', component: () => import('@/views/knowledge/Health.vue') },
    // Prescription
    { path: '/rx/templates', component: () => import('@/views/rx/Templates.vue') },
    { path: '/rx/trigger/:seekerId', component: () => import('@/views/rx/Trigger.vue') },
    // Seekers (服务对象管理)
    { path: '/seekers', component: () => import('@/views/seekers/List.vue') },
    { path: '/seekers/:id', component: () => import('@/views/seekers/Detail.vue') },
    // FAQ (常见问题库)
    { path: '/faq', component: () => import('@/views/faq/List.vue') },
    // Chat & interventions
    { path: '/chat', component: () => import('@/views/chat/Sessions.vue') },
    { path: '/chat/:id', component: () => import('@/views/chat/Detail.vue') },
    // Med Circle
    { path: '/med-circle', component: () => import('@/views/med-circle/Feed.vue') },
    // Profile & config
    { path: '/profile', component: () => import('@/views/Profile.vue') },
    { path: '/config', component: () => import('@/views/Config.vue') },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  if (!token && to.path !== '/login') return '/login'
})

export default router
