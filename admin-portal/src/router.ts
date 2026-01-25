import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('./views/Login.vue'),
    meta: { requiresAuth: false }
  },
  // ============ C 端患者路由 ============
  {
    path: '/client',
    name: 'ClientHome',
    component: () => import('./views/client/HomeView.vue'),
    meta: { title: '我的健康', requiresAuth: false }
  },
  {
    path: '/client/chat',
    name: 'ClientChat',
    component: () => import('./views/client/ChatView.vue'),
    meta: { title: 'AI 健康教练', requiresAuth: false }
  },
  // ============ 健康教练门户 ============
  {
    path: '/coach-portal',
    name: 'CoachPortal',
    component: () => import('./views/coach/CoachHome.vue'),
    meta: { title: '教练工作台', requiresAuth: true }
  },
  // ============ 督导专家门户 ============
  {
    path: '/expert-portal',
    name: 'ExpertPortal',
    component: () => import('./views/expert/ExpertHome.vue'),
    meta: { title: '督导工作台', requiresAuth: true }
  },
  // 考试会话页面 (独立全屏，不使用 AdminLayout)
  {
    path: '/exam/session/:id',
    name: 'ExamSession',
    component: () => import('./views/exam/ExamSession.vue'),
    meta: { title: '考试进行中', requiresAuth: true }
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
