import { createRouter, createWebHistory } from 'vue-router'
import storage from '@/utils/storage'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue')
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/Chat.vue')
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: () => import('@/views/Tasks.vue')
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/Dashboard.vue')
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/Profile.vue')
    },
    {
      path: '/health-records',
      name: 'health-records',
      component: () => import('@/views/HealthRecords.vue')
    },
    {
      path: '/history-reports',
      name: 'history-reports',
      component: () => import('@/views/HistoryReports.vue')
    },
    {
      path: '/data-sync',
      name: 'data-sync',
      component: () => import('@/views/DataSync.vue')
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('@/views/Notifications.vue')
    },
    {
      path: '/account-settings',
      name: 'account-settings',
      component: () => import('@/views/AccountSettings.vue')
    },
    {
      path: '/privacy-policy',
      name: 'privacy-policy',
      component: () => import('@/views/PrivacyPolicy.vue')
    },
    {
      path: '/about-us',
      name: 'about-us',
      component: () => import('@/views/AboutUs.vue')
    },
    {
      path: '/behavior-assessment',
      name: 'behavior-assessment',
      component: () => import('@/views/BehaviorAssessment.vue')
    },
    {
      path: '/my-stage',
      name: 'my-stage',
      component: () => import('@/views/MyStage.vue')
    },
    {
      path: '/my-plan',
      name: 'my-plan',
      component: () => import('@/views/MyPlan.vue')
    },
    {
      path: '/food-recognition',
      name: 'food-recognition',
      component: () => import('@/views/FoodRecognition.vue'),
      meta: { title: '食物识别' }
    },
    {
      path: '/challenges',
      name: 'challenges',
      component: () => import('@/views/ChallengeList.vue')
    },
    {
      path: '/challenge-day/:id',
      name: 'challenge-day',
      component: () => import('@/views/ChallengeDay.vue')
    },
    {
      path: '/expert-hub',
      name: 'expert-hub',
      component: () => import('@/views/ExpertHub.vue'),
      meta: { title: '专家工作室', public: true }
    },
    {
      path: '/studio/:tenantId',
      name: 'expert-studio',
      component: () => import('@/views/ExpertStudio.vue'),
      meta: { title: '工作室', public: true }
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ]
})

// 路由守卫 - 未登录跳转登录页
router.beforeEach((to, _from, next) => {
  const token = storage.getToken()
  if (!to.meta?.public && !token) {
    next({ name: 'login' })
  } else if (to.name === 'login' && token) {
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
