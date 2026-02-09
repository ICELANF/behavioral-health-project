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
      path: '/learn',
      name: 'learn',
      component: () => import('@/views/LearnCenter.vue'),
      meta: { title: '学习中心' }
    },
    {
      path: '/content/:type/:id',
      name: 'content-detail',
      component: () => import('@/views/ContentDetail.vue'),
      meta: { title: '内容详情' }
    },
    {
      path: '/my-learning',
      name: 'my-learning',
      component: () => import('@/views/MyLearning.vue'),
      meta: { title: '我的学习' }
    },
    {
      path: '/coach-directory',
      name: 'coach-directory',
      component: () => import('@/views/CoachDirectory.vue'),
      meta: { title: '教练目录', public: true }
    },
    {
      path: '/contribute',
      name: 'contribute',
      component: () => import('@/views/Contribute.vue'),
      meta: { title: '知识投稿' }
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
      path: '/my-credits',
      name: 'my-credits',
      component: () => import('@/views/MyCredits.vue'),
      meta: { title: '我的学分' }
    },
    {
      path: '/my-companions',
      name: 'my-companions',
      component: () => import('@/views/MyCompanions.vue'),
      meta: { title: '我的同道者' }
    },
    {
      path: '/promotion-progress',
      name: 'promotion-progress',
      component: () => import('@/views/PromotionProgress.vue'),
      meta: { title: '晋级进度' }
    },
    {
      path: '/journey',
      name: 'journey',
      component: () => import('@/views/journey/JourneyView.vue'),
      meta: { title: '健康成长伙伴' }
    },
    {
      path: '/programs',
      name: 'programs',
      component: () => import('@/views/MyPrograms.vue'),
      meta: { title: '智能监测方案' }
    },
    {
      path: '/program/:id/today',
      name: 'program-today',
      component: () => import('@/views/ProgramToday.vue'),
      meta: { title: '今日方案' }
    },
    {
      path: '/program/:id/timeline',
      name: 'program-timeline',
      component: () => import('@/views/ProgramTimeline.vue'),
      meta: { title: '行为轨迹' }
    },
    {
      path: '/program/:id/progress',
      name: 'program-progress',
      component: () => import('@/views/ProgramProgress.vue'),
      meta: { title: '行为特征' }
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
