import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { portalRoutes } from './router/portal_routes'
import { reactRoutes } from './router/react_routes'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('./views/Login.vue'),
    meta: { requiresAuth: false }
  },
  // ============ Landing 官网页面 ============
  {
    path: '/landing',
    name: 'Landing',
    component: () => import('./views/LandingPage.vue'),
    meta: { requiresAuth: false, layout: 'blank' }
  },
  // ============ 公共门户路由 ============
  ...portalRoutes,
  // ============ React集成页面路由 ============
  ...reactRoutes,
  // ============ C 端患者路由 ============
  {
    path: '/client',
    name: 'ClientHome',
    component: () => import('./views/client/HomeView.vue'),
    meta: { title: '我的健康', requiresAuth: false }
  },
  {
    path: '/client/home-v2',
    name: 'ClientHomeOptimized',
    component: () => import('./views/client/HomeViewOptimized.vue'),
    meta: { title: '我的健康（优化版）', requiresAuth: false }
  },
  {
    path: '/client/data-input',
    name: 'ClientDataInput',
    component: () => import('./views/client/DataInputOptimized.vue'),
    meta: { title: '记录数据', requiresAuth: false }
  },
  {
    path: '/client/chat',
    name: 'ClientChat',
    component: () => import('./views/client/ChatView.vue'),
    meta: { title: 'AI 健康教练', requiresAuth: false }
  },
  {
    path: '/client/chat-v2',
    name: 'ClientChatOptimized',
    component: () => import('./views/client/ChatViewOptimized.vue'),
    meta: { title: 'AI 健康助手（优化版）', requiresAuth: false }
  },
  {
    path: '/client/progress',
    name: 'ClientProgress',
    component: () => import('./views/client/ProgressDashboard.vue'),
    meta: { title: '我的进展', requiresAuth: false }
  },
  // Patient "我的" 模块
  {
    path: '/client/my/profile',
    name: 'ClientMyProfile',
    component: () => import('./views/client/my/MyProfile.vue'),
    meta: { title: '个人健康档案', requiresAuth: false }
  },
  {
    path: '/client/my/devices',
    name: 'ClientMyDevices',
    component: () => import('./views/client/my/MyDevices.vue'),
    meta: { title: '穿戴设备管理', requiresAuth: false }
  },
  {
    path: '/client/my/assessments',
    name: 'ClientMyAssessments',
    component: () => import('./views/client/my/MyAssessments.vue'),
    meta: { title: '测评记录', requiresAuth: false }
  },
  {
    path: '/client/my/trajectory',
    name: 'ClientMyTrajectory',
    component: () => import('./views/client/my/MyTrajectory.vue'),
    meta: { title: '行为轨迹', requiresAuth: false }
  },
  // Patient 设备仪表盘 & 测评
  {
    path: '/client/device-dashboard',
    name: 'ClientDeviceDashboard',
    component: () => import('./views/client/DeviceDashboard.vue'),
    meta: { title: '设备数据仪表盘', requiresAuth: false }
  },
  {
    path: '/client/assessment/list',
    name: 'ClientAssessmentList',
    component: () => import('./views/client/assessment/AssessmentList.vue'),
    meta: { title: '测评中心', requiresAuth: false }
  },
  {
    path: '/client/assessment/take/:id',
    name: 'ClientAssessmentTake',
    component: () => import('./views/client/assessment/TakeAssessment.vue'),
    meta: { title: '进行测评', requiresAuth: false }
  },
  {
    path: '/client/assessment/result/:id',
    name: 'ClientAssessmentResult',
    component: () => import('./views/client/assessment/AssessmentResult.vue'),
    meta: { title: '测评结果', requiresAuth: false }
  },
  // Patient 学习进度
  {
    path: '/client/learning-progress',
    name: 'ClientLearningProgress',
    component: () => import('./views/client/LearningProgress.vue'),
    meta: { title: '学习进度', requiresAuth: false }
  },
  // ============ 健康教练门户 ============
  {
    path: '/coach-portal',
    name: 'CoachPortal',
    component: () => import('./views/coach/CoachHome.vue'),
    meta: { title: '教练工作台', requiresAuth: true }
  },
  {
    path: '/coach-portal/students',
    name: 'CoachPortalStudents',
    component: () => import('./views/coach/CoachStudentList.vue'),
    meta: { title: '待跟进学员', requiresAuth: true }
  },
  {
    path: '/coach-portal/ai-review',
    name: 'CoachPortalAiReview',
    component: () => import('./views/coach/CoachAiReview.vue'),
    meta: { title: 'AI建议审核', requiresAuth: true }
  },
  // ============ 督导专家门户 ============
  {
    path: '/expert-portal',
    name: 'ExpertPortal',
    component: () => import('./views/expert/ExpertHome.vue'),
    meta: { title: '督导工作台', requiresAuth: true }
  },
  // ============ 专家审核工作台 (全屏) ============
  {
    path: '/expert-workbench',
    name: 'ExpertWorkbench',
    component: () => import('./views/expert/ExpertWorkbench.vue'),
    meta: { title: '专家审核工作台', requiresAuth: true }
  },
  // 考试会话页面 (独立全屏，不使用 AdminLayout)
  {
    path: '/exam/session/:id',
    name: 'ExamSession',
    component: () => import('./views/exam/ExamSession.vue'),
    meta: { title: '考试进行中', requiresAuth: true }
  },
  // 组件库展示页面
  {
    path: '/component-showcase',
    name: 'ComponentShowcase',
    component: () => import('./views/ComponentShowcase.vue'),
    meta: { title: '组件库展示', requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('./layouts/AdminLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('./views/dashboard/Index.vue'),
        meta: { title: '工作台', icon: 'dashboard' }
      },
      // 课程管理
      {
        path: 'course',
        name: 'Course',
        redirect: '/course/list',
        meta: { title: '课程管理', icon: 'video-camera' },
        children: [
          {
            path: 'list',
            name: 'CourseList',
            component: () => import('./views/course/List.vue'),
            meta: { title: '课程列表' }
          },
          {
            path: 'create',
            name: 'CourseCreate',
            component: () => import('./views/course/Edit.vue'),
            meta: { title: '创建课程' }
          },
          {
            path: 'edit/:id',
            name: 'CourseEdit',
            component: () => import('./views/course/Edit.vue'),
            meta: { title: '编辑课程' }
          },
          {
            path: 'chapters/:courseId',
            name: 'CourseChapters',
            component: () => import('./views/course/Chapters.vue'),
            meta: { title: '章节管理' }
          }
        ]
      },
      // 内容管理（多来源统一管理）
      {
        path: 'content',
        name: 'Content',
        redirect: '/content/review',
        meta: { title: '内容管理', icon: 'file-search' },
        children: [
          {
            path: 'review',
            name: 'ContentReview',
            component: () => import('./views/content/ReviewQueue.vue'),
            meta: { title: '内容审核' }
          },
          {
            path: 'articles',
            name: 'ContentArticles',
            component: () => import('./views/content/ArticleList.vue'),
            meta: { title: '文章管理' }
          },
          {
            path: 'cases',
            name: 'ContentCases',
            component: () => import('./views/content/CaseList.vue'),
            meta: { title: '案例分享' }
          },
          {
            path: 'cards',
            name: 'ContentCards',
            component: () => import('./views/content/CardList.vue'),
            meta: { title: '练习卡片' }
          },
          {
            path: 'video/:videoId/quiz',
            name: 'VideoQuizCreate',
            component: () => import('./views/content/VideoQuizEditor.vue'),
            meta: { title: '创建视频测试' }
          },
          {
            path: 'video/:videoId/quiz/:quizId',
            name: 'VideoQuizEdit',
            component: () => import('./views/content/VideoQuizEditor.vue'),
            meta: { title: '编辑视频测试' }
          }
        ]
      },
      // 题库管理
      {
        path: 'question',
        name: 'Question',
        redirect: '/question/bank',
        meta: { title: '题库管理', icon: 'file-text' },
        children: [
          {
            path: 'bank',
            name: 'QuestionBank',
            component: () => import('./views/exam/QuestionBank.vue'),
            meta: { title: '题库列表' }
          },
          {
            path: 'create',
            name: 'QuestionCreate',
            component: () => import('./views/exam/QuestionEdit.vue'),
            meta: { title: '创建题目' }
          },
          {
            path: 'edit/:id',
            name: 'QuestionEdit',
            component: () => import('./views/exam/QuestionEdit.vue'),
            meta: { title: '编辑题目' }
          }
        ]
      },
      // 考试管理
      {
        path: 'exam',
        name: 'Exam',
        redirect: '/exam/list',
        meta: { title: '考试管理', icon: 'solution' },
        children: [
          {
            path: 'list',
            name: 'ExamList',
            component: () => import('./views/exam/ExamList.vue'),
            meta: { title: '考试列表' }
          },
          {
            path: 'create',
            name: 'ExamCreate',
            component: () => import('./views/exam/ExamEdit.vue'),
            meta: { title: '创建考试' }
          },
          {
            path: 'edit/:id',
            name: 'ExamEdit',
            component: () => import('./views/exam/ExamEdit.vue'),
            meta: { title: '编辑考试' }
          },
          {
            path: 'results/:examId',
            name: 'ExamResults',
            component: () => import('./views/exam/Results.vue'),
            meta: { title: '成绩管理' }
          },
          {
            path: 'proctor-review',
            name: 'ProctorReview',
            component: () => import('./views/exam/ProctorReview.vue'),
            meta: { title: '监考审核' }
          }
        ]
      },
      // 直播管理
      {
        path: 'live',
        name: 'Live',
        redirect: '/live/list',
        meta: { title: '直播管理', icon: 'play-circle' },
        children: [
          {
            path: 'list',
            name: 'LiveList',
            component: () => import('./views/live/List.vue'),
            meta: { title: '直播列表' }
          },
          {
            path: 'create',
            name: 'LiveCreate',
            component: () => import('./views/live/Edit.vue'),
            meta: { title: '创建直播' }
          },
          {
            path: 'edit/:id',
            name: 'LiveEdit',
            component: () => import('./views/live/Edit.vue'),
            meta: { title: '编辑直播' }
          }
        ]
      },
      // 教练管理
      {
        path: 'coach',
        name: 'Coach',
        redirect: '/coach/list',
        meta: { title: '教练管理', icon: 'team' },
        children: [
          {
            path: 'list',
            name: 'CoachList',
            component: () => import('./views/coach/List.vue'),
            meta: { title: '教练列表' }
          },
          {
            path: 'detail/:id',
            name: 'CoachDetail',
            component: () => import('./views/coach/Detail.vue'),
            meta: { title: '教练详情' }
          },
          {
            path: 'review',
            name: 'CoachReview',
            component: () => import('./views/coach/Review.vue'),
            meta: { title: '晋级审核' }
          }
        ]
      },
      // 学员管理
      {
        path: 'student',
        name: 'Student',
        component: () => import('./views/coach/StudentList.vue'),
        meta: { title: '学员管理', icon: 'user' }
      },
      // Prompt 模板管理
      {
        path: 'prompts',
        name: 'Prompts',
        redirect: '/prompts/list',
        meta: { title: 'Prompt管理', icon: 'file-text' },
        children: [
          {
            path: 'list',
            name: 'PromptList',
            component: () => import('./views/admin/prompts/Index.vue'),
            meta: { title: 'Prompt列表' }
          },
          {
            path: 'create',
            name: 'PromptCreate',
            component: () => import('./views/admin/prompts/Edit.vue'),
            meta: { title: '创建Prompt' }
          },
          {
            path: 'edit/:id',
            name: 'PromptEdit',
            component: () => import('./views/admin/prompts/Edit.vue'),
            meta: { title: '编辑Prompt' }
          }
        ]
      },
      // 干预包管理
      {
        path: 'interventions',
        name: 'Interventions',
        component: () => import('./views/admin/interventions/Index.vue'),
        meta: { title: '干预包管理', icon: 'medicine-box' }
      },
      // ============ Coach "我的" 模块 ============
      {
        path: 'coach/my/students',
        name: 'CoachMyStudents',
        component: () => import('./views/coach/my/MyStudents.vue'),
        meta: { title: '我的学员' }
      },
      {
        path: 'coach/my/performance',
        name: 'CoachMyPerformance',
        component: () => import('./views/coach/my/MyPerformance.vue'),
        meta: { title: '我的绩效' }
      },
      {
        path: 'coach/my/certification',
        name: 'CoachMyCertification',
        component: () => import('./views/coach/my/MyCertification.vue'),
        meta: { title: '我的认证' }
      },
      {
        path: 'coach/my/tools',
        name: 'CoachMyTools',
        component: () => import('./views/coach/my/MyTools.vue'),
        meta: { title: '我的工具箱' }
      },
      {
        path: 'coach/my/analytics',
        name: 'CoachMyAnalytics',
        component: () => import('./views/coach/my/CoachAnalytics.vue'),
        meta: { title: '数据分析' }
      },
      // Coach 内容分享
      {
        path: 'coach/content-sharing',
        name: 'CoachContentSharing',
        component: () => import('./views/coach/ContentSharing.vue'),
        meta: { title: '内容分享' }
      },
      // Coach 学员测评交互
      {
        path: 'coach/student-assessment/:id',
        name: 'CoachStudentAssessment',
        component: () => import('./views/coach/StudentAssessment.vue'),
        meta: { title: '学员测评交互' }
      },
      // Coach 学员行为画像
      {
        path: 'coach/student-profile/:id',
        name: 'CoachStudentBehavioralProfile',
        component: () => import('./views/coach/StudentBehavioralProfile.vue'),
        meta: { title: '学员行为画像' }
      },
      // Coach 学员消息
      {
        path: 'coach/messages',
        name: 'CoachStudentMessages',
        component: () => import('./views/coach/StudentMessages.vue'),
        meta: { title: '学员消息' }
      },
      // Coach 学员健康数据
      {
        path: 'coach/student-health/:id',
        name: 'CoachStudentHealthData',
        component: () => import('./views/coach/StudentHealthData.vue'),
        meta: { title: '学员健康数据' }
      },
      // 挑战/打卡活动管理
      {
        path: 'admin/challenges',
        name: 'ChallengeManagement',
        component: () => import('./views/admin/ChallengeManagement.vue'),
        meta: { title: '挑战活动管理' }
      },
      // ============ Expert 管理面板 ============
      {
        path: 'expert/dashboard/:tenantId',
        name: 'ExpertDashboard',
        component: () => import('./views/admin/ExpertDashboard.vue'),
        meta: { title: '专家工作室管理' }
      },
      {
        path: 'expert/content-studio/:tenantId',
        name: 'ExpertContentStudio',
        component: () => import('./views/admin/ExpertContentStudio.vue'),
        meta: { title: '内容工作室' }
      },
      // ============ Expert "我的" 模块 ============
      {
        path: 'expert/my/supervision',
        name: 'ExpertMySupervision',
        component: () => import('./views/expert/my/MySupervision.vue'),
        meta: { title: '我的督导' }
      },
      {
        path: 'expert/my/reviews',
        name: 'ExpertMyReviews',
        component: () => import('./views/expert/my/MyReviews.vue'),
        meta: { title: '我的审核' }
      },
      {
        path: 'expert/my/research',
        name: 'ExpertMyResearch',
        component: () => import('./views/expert/my/MyResearch.vue'),
        meta: { title: '研究数据' }
      },
      // ============ Admin 模块 ============
      {
        path: 'admin/user-management',
        name: 'AdminUserManagement',
        component: () => import('./views/admin/my/UserManagement.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'admin/distribution',
        name: 'AdminDistribution',
        component: () => import('./views/admin/Distribution.vue'),
        meta: { title: '分配管理' }
      },
      {
        path: 'admin/analytics',
        name: 'AdminAnalytics',
        component: () => import('./views/admin/AdminAnalytics.vue'),
        meta: { title: '数据分析' }
      },
      // 批量知识灌注
      {
        path: 'admin/batch-ingestion',
        name: 'AdminBatchIngestion',
        component: () => import('./views/admin/BatchIngestion.vue'),
        meta: { title: '批量知识灌注' }
      },
      // 内容管理
      {
        path: 'admin/content-manage',
        name: 'AdminContentManage',
        component: () => import('./views/admin/ContentManage.vue'),
        meta: { title: '内容管理' }
      },
      // 用户活动报告
      {
        path: 'admin/activity-report',
        name: 'AdminActivityReport',
        component: () => import('./views/admin/UserActivityReport.vue'),
        meta: { title: '用户活动报告' }
      },
      // ============ 学分晋级体系 ============
      {
        path: 'admin/credit-system',
        name: 'CreditSystem',
        redirect: '/admin/credit-system/dashboard',
        meta: { title: '学分晋级', icon: 'trophy' },
        children: [
          {
            path: 'dashboard',
            name: 'CreditDashboard',
            component: () => import('./views/admin/CreditDashboard.vue'),
            meta: { title: '学分概览' }
          },
          {
            path: 'modules',
            name: 'CourseModuleManage',
            component: () => import('./views/admin/CourseModuleManage.vue'),
            meta: { title: '课程模块管理' }
          },
          {
            path: 'companions',
            name: 'CompanionManage',
            component: () => import('./views/admin/CompanionManage.vue'),
            meta: { title: '同道者关系' }
          },
          {
            path: 'promotion-review',
            name: 'PromotionReview',
            component: () => import('./views/admin/PromotionReview.vue'),
            meta: { title: '晋级审核' }
          }
        ]
      },
      // ============ 安全管理 (V005) ============
      {
        path: 'safety',
        name: 'SafetyManagement',
        redirect: '/safety/dashboard',
        meta: { title: '安全管理', icon: 'safety-certificate', requiresAdmin: true },
        children: [
          {
            path: 'dashboard',
            name: 'SafetyDashboard',
            component: () => import('./views/safety/SafetyDashboard.vue'),
            meta: { title: '安全仪表盘', requiresAdmin: true }
          },
          {
            path: 'review',
            name: 'SafetyReviewQueue',
            component: () => import('./views/safety/SafetyReviewQueue.vue'),
            meta: { title: '安全审核队列', requiresAdmin: true }
          }
        ]
      },
      // 系统设置
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('./views/Settings.vue'),
        meta: { title: '系统设置', icon: 'setting' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('admin_token')
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
