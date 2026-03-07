import { createRouter, createWebHistory } from 'vue-router'
import storage from '@/utils/storage'

// ═══ 全局角色→首页映射 (8角色, 每个角色独立首页) ═══
const ROLE_HOME_MAP: Record<string, string> = {
  observer:   '/home/observer',
  grower:     '/home/today',
  sharer:     '/home/sharer',
  coach:      '/home/coach',
  promoter:   '/home/pro',
  supervisor: '/home/pro',
  master:     '/home/master',
  admin:      '/home/admin',
}

/** 根据当前登录用户角色获取首页路径 */
function getRoleHomePath(): string {
  const authUser = storage.getAuthUser()
  const role = (authUser?.role || 'observer').toLowerCase()
  return ROLE_HOME_MAP[role] || '/home/observer'
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/portal',
      name: 'portal',
      component: () => import('@/views/Portal.vue'),
      meta: { title: '行为健康数字平台', public: true }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { public: true }
    },
    // ═══ 首页: 未登录→门户, 已登录→按角色名分流到各自首页 ═══
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue'),
      beforeEnter: (_to, _from, next) => {
        const token = storage.getToken()
        if (!token) { next({ path: '/portal', replace: true }); return }
        next({ path: getRoleHomePath(), replace: true })
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
      meta: { title: '开始你的健康旅程', public: true },
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
      path: '/home/coach',
      name: 'coach-home',
      component: () => import('@/views/home/CoachHome.vue'),
      meta: { title: '教练工作台' },
    },
    {
      path: '/home/pro',
      name: 'pro-home',
      component: () => import('@/views/home/ProHome.vue'),
      meta: { title: '专业工作台' },
    },
    {
      path: '/home/master',
      name: 'master-home',
      component: () => import('@/views/home/MasterHome.vue'),
      meta: { title: '大师工作台' },
    },
    {
      path: '/home/admin',
      name: 'admin-home',
      component: () => import('@/views/home/AdminHome.vue'),
      meta: { title: '管理员首页' },
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/Chat.vue'),
      meta: { title: 'AI 健康向导', public: true }
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
      path: '/settings/notifications',
      name: 'notification-settings',
      component: () => import('@/views/settings/NotificationSettings.vue'),
      meta: { title: '通知设置' }
    },
    {
      path: '/privacy-policy',
      name: 'privacy-policy',
      component: () => import('@/views/PrivacyPolicy.vue'),
      meta: { title: '隐私政策', public: true }
    },
    {
      path: '/about-us',
      name: 'about-us',
      component: () => import('@/views/AboutUs.vue'),
      meta: { title: '关于我们', public: true }
    },
    {
      path: '/behavior-assessment',
      name: 'behavior-assessment',
      component: () => import('@/views/BehaviorAssessment.vue'),
      meta: { title: '行为状态评估', public: true }
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
      meta: { title: '学习中心', public: true }
    },
    {
      path: '/content/:type/:id',
      name: 'content-detail',
      component: () => import('@/views/ContentDetail.vue'),
      meta: { title: '内容详情', public: true }
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
      path: '/reflection',
      name: 'reflection',
      component: () => import('@/views/Reflection.vue'),
      meta: { title: '成长感悟' }
    },
    {
      path: '/case-stories',
      name: 'case-stories',
      component: () => import('@/views/CaseStories.vue'),
      meta: { title: '成长案例' }
    },
    {
      path: '/medical',
      name: 'medical',
      component: () => import('@/views/MedicalRecord.vue'),
      meta: { title: '理性就医' }
    },
    {
      path: '/trajectory',
      name: 'trajectory',
      component: () => import('@/views/TrajectoryView.vue'),
      meta: { title: '我的行为轨迹' }
    },
    {
      path: '/become-sharer',
      name: 'become-sharer',
      component: () => import('@/views/BecomeSharer.vue'),
      meta: { title: '成为分享者' }
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
    // ── 行为处方详情 ──
    {
      path: '/rx/:id',
      name: 'rx-detail',
      component: () => import('@/views/RxPrescriptionDetail.vue'),
      meta: { title: '行为处方详情' }
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
    // ── 归心 Phase 1 (动机→画像→处方) ──
    {
      path: '/v3/motivation-quiz',
      name: 'motivation-quiz',
      component: () => import('@/views/v3/MotivationQuiz.vue'),
      meta: { title: '动机与人格评估' }
    },
    {
      path: '/v3/profile-card',
      name: 'profile-card',
      component: () => import('@/views/v3/ProfileCard.vue'),
      meta: { title: '我的行为画像' }
    },
    {
      path: '/v3/prescription-card',
      name: 'prescription-card',
      component: () => import('@/views/v3/PrescriptionCard.vue'),
      meta: { title: '行为处方' }
    },
    // ── VisionGuard 视力行为保护 ──
    {
      path: '/vision/daily',
      name: 'vision-daily',
      component: () => import('@/views/vision/VisionDailyLog.vue'),
      meta: { title: '视力行为打卡' }
    },
    {
      path: '/vision/guardian',
      name: 'vision-guardian',
      component: () => import('@/views/vision/VisionGuardianView.vue'),
      meta: { title: '孩子视力报告' }
    },
    {
      path: '/vision/profile',
      name: 'vision-profile',
      component: () => import('@/views/vision/VisionProfile.vue'),
      meta: { title: '视力档案' }
    },
    {
      path: '/vision/exam',
      name: 'vision-exam',
      component: () => import('@/views/vision/VisionExamRecord.vue'),
      meta: { title: '视力检查记录' }
    },
    // ── 微信授权回调 ──
    {
      path: '/wechat/callback',
      name: 'wechat-callback',
      component: () => import('@/views/WechatCallback.vue'),
      meta: { title: '微信登录', public: true }
    },
    // ── Staff Login (独立页，不嵌套在 StaffLayout 内) ──
    {
      path: '/staff/login',
      component: () => import('@/views/staff/StaffLogin.vue'),
      meta: { public: true }
    },
    // ── Staff Web (PC 后台网页版) ──
    {
      path: '/staff',
      component: () => import('@/layouts/StaffLayout.vue'),
      meta: { requiresStaff: true },
      children: [
        {
          path: '',
          redirect: () => {
            const authUser = storage.getAuthUser()
            const r = ((authUser?.role) || 'coach').toLowerCase()
            const roleMap: Record<string, string> = {
              coach: '/staff/coach/dashboard',
              promoter: '/staff/supervisor/dashboard',
              supervisor: '/staff/supervisor/dashboard',
              master: '/staff/master/dashboard',
              admin: '/staff/admin/overview',
            }
            return roleMap[r] || '/staff/coach/dashboard'
          }
        },
        // Coach
        { path: 'coach/dashboard',     component: () => import('@/views/staff/coach/Dashboard.vue') },
        { path: 'coach/students',      component: () => import('@/views/staff/coach/Students.vue') },
        { path: 'coach/assessment',    component: () => import('@/views/staff/coach/Assessment.vue') },
        { path: 'coach/flywheel',      component: () => import('@/views/staff/coach/Flywheel.vue') },
        { path: 'coach/push-queue',    component: () => import('@/views/staff/coach/PushQueue.vue') },
        { path: 'coach/health-review', component: () => import('@/views/staff/coach/HealthReview.vue') },
        { path: 'coach/risk',          component: () => import('@/views/staff/coach/Risk.vue') },
        { path: 'coach/analytics',     component: () => import('@/views/staff/coach/Analytics.vue') },
        { path: 'coach/promotion',     component: () => import('@/views/staff/coach/Promotion.vue') },
        // Supervisor
        { path: 'supervisor/dashboard',    component: () => import('@/views/staff/supervisor/Dashboard.vue') },
        { path: 'supervisor/coaches',      component: () => import('@/views/staff/supervisor/Coaches.vue') },
        { path: 'supervisor/review-queue', component: () => import('@/views/staff/supervisor/ReviewQueue.vue') },
        { path: 'supervisor/promotion',    component: () => import('@/views/staff/supervisor/Promotion.vue') },
        // Master
        { path: 'master/dashboard',       component: () => import('@/views/staff/master/Dashboard.vue') },
        { path: 'master/critical-review', component: () => import('@/views/staff/master/CriticalReview.vue') },
        { path: 'master/knowledge',       component: () => import('@/views/staff/master/Knowledge.vue') },
        { path: 'master/promotion',       component: () => import('@/views/staff/master/Promotion.vue') },
        // Admin
        { path: 'admin/overview',   component: () => import('@/views/staff/admin/Overview.vue') },
        { path: 'admin/users',      component: () => import('@/views/staff/admin/Users.vue') },
        { path: 'admin/content',    component: () => import('@/views/staff/admin/Content.vue') },
        { path: 'admin/coaches',    component: () => import('@/views/staff/admin/Coaches.vue') },
        { path: 'admin/promotions', component: () => import('@/views/staff/admin/Promotions.vue') },
        { path: 'admin/reports',    component: () => import('@/views/staff/admin/Reports.vue') },
        { path: 'admin/config',     component: () => import('@/views/staff/admin/Config.vue') },
        { path: 'admin/logs',       component: () => import('@/views/staff/admin/Logs.vue') },
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ]
})

// ═══ 全局修补 router.back() — 历史栈为空时直接跳角色首页，防止卡死 ═══
const _originalBack = router.back.bind(router)
router.back = () => {
  // window.history.state.back 是 Vue Router 写入的前一页路径，为 null 表示无历史
  const prevPath = window.history.state?.back as string | null
  if (prevPath) {
    _originalBack()
  } else {
    // 无历史（直接打开、刷新）→ 跳角色首页
    router.replace(getRoleHomePath())
  }
}

// 路由守卫 - 未登录访问需认证页面 → 跳转门户页
const STAFF_ROLES = new Set(['coach', 'promoter', 'supervisor', 'master', 'admin'])

router.beforeEach((to, _from, next) => {
  const token = storage.getToken()

  // Staff routes: 需要登录 + staff角色
  if (to.matched.some(r => r.meta?.requiresStaff)) {
    if (!token) { next({ path: '/staff/login', replace: true }); return }
    const authUser = storage.getAuthUser()
    const role = ((authUser?.role) || '').toLowerCase()
    if (!STAFF_ROLES.has(role)) { next({ path: '/portal', replace: true }); return }
    next(); return
  }

  if (!to.meta?.public && !token) {
    next({ path: '/portal', replace: true })
  } else {
    next()
  }
})

export { getRoleHomePath, ROLE_HOME_MAP }
export default router
