/**
 * Vue Router — generated from miniprogram pages.json
 * Path mapping: /pages/xxx/yyy → /xxx/yyy
 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // === Main pages ===
  { path: '/', redirect: '/home' },
  { path: '/auth/login', component: () => import('../views/auth/login.vue'), meta: { title: '登录', public: true } },
  { path: '/auth/register', component: () => import('../views/auth/register.vue'), meta: { title: '注册', public: true } },
  { path: '/home', component: () => import('../views/home/index.vue'), meta: { title: '行健平台' } },
  { path: '/notifications', component: () => import('../views/notifications/index.vue'), meta: { title: '消息中心' } },
  { path: '/profile', component: () => import('../views/profile/index.vue'), meta: { title: '个人中心' } },

  // === Learning ===
  { path: '/learning', component: () => import('../views/learning/index.vue'), meta: { title: '学习中心' } },
  { path: '/learning/catalog', component: () => import('../views/learning/catalog.vue'), meta: { title: '课程目录' } },
  { path: '/learning/content-detail', component: () => import('../views/learning/content-detail.vue'), meta: { title: '内容详情' } },
  { path: '/learning/video-player', component: () => import('../views/learning/video-player.vue'), meta: { title: '视频学习' } },
  { path: '/learning/audio-player', component: () => import('../views/learning/audio-player.vue'), meta: { title: '音频播放' } },
  { path: '/learning/course-detail', component: () => import('../views/learning/course-detail.vue'), meta: { title: '课程详情' } },
  { path: '/learning/course-chapter', component: () => import('../views/learning/course-chapter.vue'), meta: { title: '章节学习' } },
  { path: '/learning/quiz', component: () => import('../views/learning/quiz.vue'), meta: { title: '随堂测验' } },
  { path: '/learning/quiz-result', component: () => import('../views/learning/quiz-result.vue'), meta: { title: '测验结果' } },
  { path: '/learning/my-learning', component: () => import('../views/learning/my-learning.vue'), meta: { title: '我的学习' } },
  { path: '/learning/credits', component: () => import('../views/learning/credits.vue'), meta: { title: '我的学分' } },

  // === Exam ===
  { path: '/exam', component: () => import('../views/exam/index.vue'), meta: { title: '认证考试' } },
  { path: '/exam/intro', component: () => import('../views/exam/intro.vue'), meta: { title: '考试说明' } },
  { path: '/exam/session', component: () => import('../views/exam/session.vue'), meta: { title: '考试作答' } },
  { path: '/exam/result', component: () => import('../views/exam/result.vue'), meta: { title: '考试结果' } },
  { path: '/exam/history', component: () => import('../views/exam/history.vue'), meta: { title: '考试记录' } },

  // === Journey ===
  { path: '/journey/overview', component: () => import('../views/journey/overview.vue'), meta: { title: '成长路径' } },
  { path: '/journey/progress', component: () => import('../views/journey/progress.vue'), meta: { title: '我的进度' } },
  { path: '/journey/promotion', component: () => import('../views/journey/promotion.vue'), meta: { title: '申请晋级' } },
  { path: '/journey/history', component: () => import('../views/journey/history.vue'), meta: { title: '申请记录' } },

  // === Companions ===
  { path: '/companions', component: () => import('../views/companions/index.vue'), meta: { title: '我的同道者' } },
  { path: '/companions/invite', component: () => import('../views/companions/invite.vue'), meta: { title: '邀请同道者' } },
  { path: '/companions/detail', component: () => import('../views/companions/detail.vue'), meta: { title: '同道者详情' } },
  { path: '/companions/invitations', component: () => import('../views/companions/invitations.vue'), meta: { title: '收到的邀请' } },
  { path: '/companions/message', component: () => import('../views/companions/message.vue'), meta: { title: '发消息' } },

  // === Assessment ===
  { path: '/assessment/pending', component: () => import('../views/assessment/pending.vue'), meta: { title: '待完成评估' } },
  { path: '/assessment/do', component: () => import('../views/assessment/do.vue'), meta: { title: '评估作答' } },
  { path: '/assessment/result', component: () => import('../views/assessment/result.vue'), meta: { title: '评估结果' } },

  // === Coach ===
  { path: '/coach/dashboard', component: () => import('../views/coach/dashboard/index.vue'), meta: { title: '教练工作台' } },
  { path: '/coach/students', component: () => import('../views/coach/students/index.vue'), meta: { title: '我的学员' } },
  { path: '/coach/students/detail', component: () => import('../views/coach/students/detail.vue'), meta: { title: '学员详情' } },
  { path: '/coach/push-queue', component: () => import('../views/coach/push-queue/index.vue'), meta: { title: '推送审批' } },
  { path: '/coach/assessment', component: () => import('../views/coach/assessment/index.vue'), meta: { title: '评估管理' } },
  { path: '/coach/assessment/review', component: () => import('../views/coach/assessment/review.vue'), meta: { title: '评估审核' } },
  { path: '/coach/analytics', component: () => import('../views/coach/analytics/index.vue'), meta: { title: '数据分析' } },
  { path: '/coach/live', component: () => import('../views/coach/live/index.vue'), meta: { title: '直播中心' } },
  { path: '/coach/flywheel', component: () => import('../views/coach/flywheel/index.vue'), meta: { title: 'AI飞轮' } },
  { path: '/coach/messages', component: () => import('../views/coach/messages/index.vue'), meta: { title: '消息' } },
  { path: '/coach/risk', component: () => import('../views/coach/risk/index.vue'), meta: { title: '风险管理' } },
  { path: '/coach/health-review', component: () => import('../views/coach/health-review/index.vue'), meta: { title: '健康数据审核' } },
  { path: '/coach/promotion', component: () => import('../views/coach/promotion/index.vue'), meta: { title: '晋级申请审核' } },
  { path: '/coach/contributions', component: () => import('../views/coach/contributions/index.vue'), meta: { title: '内容投稿审核' } },

  // === Profile Extra ===
  { path: '/profile-extra/certification', component: () => import('../views/profile-extra/certification.vue'), meta: { title: '我的认证' } },
  { path: '/profile-extra/performance', component: () => import('../views/profile-extra/performance.vue'), meta: { title: '我的绩效' } },
  { path: '/profile-extra/settings', component: () => import('../views/profile-extra/settings.vue'), meta: { title: '账号设置' } },
  { path: '/profile-extra/leaderboard', component: () => import('../views/profile-extra/leaderboard.vue'), meta: { title: '积分排行榜' } },

  // === Health ===
  { path: '/health', component: () => import('../views/health/index.vue'), meta: { title: '健康数据' } },
  { path: '/health/blood-glucose', component: () => import('../views/health/blood-glucose.vue'), meta: { title: '血糖记录' } },
  { path: '/health/weight', component: () => import('../views/health/weight.vue'), meta: { title: '体重体成分' } },
  { path: '/health/exercise', component: () => import('../views/health/exercise.vue'), meta: { title: '运动记录' } },
  { path: '/health/device-bind', component: () => import('../views/health/device-bind.vue'), meta: { title: '设备管理' } },

  // === Food ===
  { path: '/food/scan', component: () => import('../views/food/scan.vue'), meta: { title: '饮食记录' } },
  { path: '/food/diary', component: () => import('../views/food/diary.vue'), meta: { title: '饮食日记' } },

  // === Sharer ===
  { path: '/sharer/mentees', component: () => import('../views/sharer/mentees.vue'), meta: { title: '我的学员' } },
  { path: '/sharer/share-content', component: () => import('../views/sharer/share-content.vue'), meta: { title: '内容分享' } },

  // === Supervisor ===
  { path: '/supervisor/dashboard', component: () => import('../views/supervisor/dashboard.vue'), meta: { title: '督导工作台' } },
  { path: '/supervisor/coaches', component: () => import('../views/supervisor/coaches.vue'), meta: { title: '教练管理' } },
  { path: '/supervisor/review-queue', component: () => import('../views/supervisor/review-queue.vue'), meta: { title: '健康数据审核' } },
  { path: '/supervisor/promotion', component: () => import('../views/supervisor/promotion/index.vue'), meta: { title: '晋级复核' } },

  // === Master ===
  { path: '/master/dashboard', component: () => import('../views/master/dashboard.vue'), meta: { title: '行为健康大师工作台' } },
  { path: '/master/critical-review', component: () => import('../views/master/critical-review.vue'), meta: { title: '危急病例' } },
  { path: '/master/knowledge', component: () => import('../views/master/knowledge.vue'), meta: { title: '知识库管理' } },
  { path: '/master/promotion', component: () => import('../views/master/promotion/index.vue'), meta: { title: '晋级终审' } },

  // === Standalone ===
  { path: '/reflection', component: () => import('../views/reflection/index.vue'), meta: { title: '成长感悟' } },
  { path: '/case-stories', component: () => import('../views/case-stories/index.vue'), meta: { title: '健康之路' } },
  { path: '/case-stories/publish', component: () => import('../views/case-stories/publish.vue'), meta: { title: '分享健康之路' } },
  { path: '/medical', component: () => import('../views/medical/index.vue'), meta: { title: '理性就医' } },
  { path: '/trajectory', component: () => import('../views/trajectory/index.vue'), meta: { title: '行为轨迹' } },
  { path: '/become-sharer', component: () => import('../views/become-sharer/index.vue'), meta: { title: '成为分享者' } },

  // Catch-all
  { path: '/:pathMatch(.*)*', redirect: '/home' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Auth guard
router.beforeEach((to, _from, next) => {
  // Set page title
  if (to.meta?.title) document.title = to.meta.title as string

  // Auth check
  if (to.meta?.public) return next()
  const token = localStorage.getItem('access_token')
  if (!token) return next('/auth/login')
  next()
})

export default router
