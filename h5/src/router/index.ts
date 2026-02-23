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
    // ═══ 飞轮首页: 按角色分流 (2026-02-22 三分支: Observer/Grower/Sharer+) ═══
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue'),
      beforeEnter: (_to, _from, next) => {
        const token = storage.getToken()
        if (!token) { next({ name: 'login' }); return }
        // 尝试从localStorage读取角色等级 (登录后由auth store写入)
        const roleLevel = parseInt(localStorage.getItem('bhp_role_level') || '0', 10)
        if (roleLevel <= 1) {
          next({ path: '/home/observer', replace: true })
        } else if (roleLevel === 3) {
          next({ path: '/home/sharer', replace: true })   // Sharer专属
        } else {
          next({ path: '/home/today', replace: true })     // Grower(2) + Coach(4)+
        }
      }
    },
    {
      path: '/onboarding',
      name: 'onboarding',
      component: () => import('@/views/onboarding/OnboardingGuide.vue'),
      meta: { title: '欢迎' }
    },
    {
      path: '/onboarding/grower',
      name: 'grower-onboarding',
      component: () => import('@/views/onboarding/GrowerOnboarding.vue'),
      meta: { title: '完善健康档案' }
    },
    {
      path: '/onboarding/sharer',
      name: 'sharer-onboarding',
      component: () => import('@/views/onboarding/SharerOnboarding.vue'),
      meta: { title: '欢迎成为分享者' }
    },
    {
      path: '/home/observer',
      name: 'observer-home',
      component: () => import('@/views/home/ObserverHome.vue'),
      meta: { title: '开始你的健康旅程' },
      beforeEnter: (_to, _from, next) => {
        if (!localStorage.getItem('bhp_onboarding_done')) {
          next({ path: '/onboarding', replace: true })
        } else {
          next()
        }
      }
    },
    {
      path: '/home/today',
      name: 'grower-today',
      component: () => import('@/views/home/GrowerTodayHome.vue'),
      meta: { title: '今日行动' },
      beforeEnter: (_to, _from, next) => {
        if (!localStorage.getItem('bhp_grower_onboarding_done')) {
          next({ path: '/onboarding/grower', replace: true })
        } else {
          next()
        }
      }
    },
    {
      path: '/home/sharer',
      name: 'sharer-home',
      component: () => import('@/views/home/SharerHome.vue'),
      meta: { title: '分享者首页' },
      beforeEnter: (_to, _from, next) => {
        if (!localStorage.getItem('bhp_sharer_onboarding_done')) {
          next({ path: '/onboarding/sharer', replace: true })
        } else {
          next()
        }
      }
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
      path: '/weekly-report',
      name: 'weekly-report',
      component: () => import('@/views/WeeklyReport.vue'),
      meta: { title: '行为周报' }
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
      path: '/expert-register',
      name: 'expert-register',
      component: () => import('@/views/ExpertRegister.vue'),
      meta: { title: '申请入驻', public: true }
    },
    {
      path: '/expert-application-status',
      name: 'expert-application-status',
      component: () => import('@/views/ExpertApplicationStatus.vue'),
      meta: { title: '申请状态' }
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
    // ── v3 渐进式评估 + AI Coach + 知识库 ──
    {
      path: '/v3/assessment',
      name: 'v3-assessment',
      component: () => import('@/views/v3/Assessment.vue'),
      meta: { title: '渐进式评估' }
    },
    {
      path: '/v3/assessment/:batchId',
      name: 'v3-assessment-batch',
      component: () => import('@/views/v3/AssessmentBatch.vue'),
      props: true,
      meta: { title: '评估批次' }
    },
    {
      path: '/v3/coach',
      name: 'v3-coach',
      component: () => import('@/views/v3/Coach.vue'),
      meta: { title: 'AI 健康教练' }
    },
    {
      path: '/v3/knowledge',
      name: 'v3-knowledge',
      component: () => import('@/views/v3/Knowledge.vue'),
      meta: { title: '知识库', public: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/v3/Register.vue'),
      meta: { public: true }
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
