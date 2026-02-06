<template>
  <a-layout class="admin-layout">
    <!-- 侧边栏 -->
    <a-layout-sider v-model:collapsed="collapsed" collapsible theme="dark" :width="220">
      <div class="logo">
        <span v-if="!collapsed">教练认证管理</span>
        <span v-else>认证</span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        theme="dark"
        mode="inline"
      >
        <!-- 所有用户可见 -->
        <a-menu-item key="dashboard" @click="$router.push('/dashboard')">
          <template #icon><DashboardOutlined /></template>
          <span>工作台</span>
        </a-menu-item>

        <!-- 教练"我的"子菜单 - 教练及以上可见 -->
        <a-sub-menu v-if="isCoach" key="coach-my">
          <template #icon><UserOutlined /></template>
          <template #title>我的</template>
          <a-menu-item key="coach-my-students" @click="$router.push('/coach/my/students')">我的学员</a-menu-item>
          <a-menu-item key="coach-my-performance" @click="$router.push('/coach/my/performance')">我的绩效</a-menu-item>
          <a-menu-item key="coach-my-certification" @click="$router.push('/coach/my/certification')">我的认证</a-menu-item>
          <a-menu-item key="coach-my-tools" @click="$router.push('/coach/my/tools')">我的工具箱</a-menu-item>
        </a-sub-menu>

        <!-- 教练内容分享 - 教练及以上可见 -->
        <a-menu-item v-if="isCoach" key="coach-content-sharing" @click="$router.push('/coach/content-sharing')">
          <template #icon><ShareAltOutlined /></template>
          <span>内容分享</span>
        </a-menu-item>

        <!-- 专家"我的"子菜单 - 专家及以上可见 -->
        <a-sub-menu v-if="isExpert" key="expert-my">
          <template #icon><SafetyCertificateOutlined /></template>
          <template #title>督导中心</template>
          <a-menu-item key="expert-my-supervision" @click="$router.push('/expert/my/supervision')">我的督导</a-menu-item>
          <a-menu-item key="expert-my-reviews" @click="$router.push('/expert/my/reviews')">我的审核</a-menu-item>
          <a-menu-item key="expert-my-research" @click="$router.push('/expert/my/research')">研究数据</a-menu-item>
        </a-sub-menu>

        <!-- 专家及以上可见 -->
        <a-sub-menu v-if="isExpert" key="course">
          <template #icon><VideoCameraOutlined /></template>
          <template #title>课程管理</template>
          <a-menu-item key="course-list" @click="$router.push('/course/list')">课程列表</a-menu-item>
          <a-menu-item v-if="isAdmin" key="course-create" @click="$router.push('/course/create')">创建课程</a-menu-item>
        </a-sub-menu>

        <!-- 内容管理 - 专家及以上可见 -->
        <a-sub-menu v-if="isExpert" key="content">
          <template #icon><FileSearchOutlined /></template>
          <template #title>内容管理</template>
          <a-menu-item key="content-review" @click="$router.push('/content/review')">内容审核</a-menu-item>
          <a-menu-item key="content-articles" @click="$router.push('/content/articles')">文章管理</a-menu-item>
          <a-menu-item key="content-cases" @click="$router.push('/content/cases')">案例分享</a-menu-item>
          <a-menu-item key="content-cards" @click="$router.push('/content/cards')">练习卡片</a-menu-item>
        </a-sub-menu>

        <!-- 专家及以上可见 -->
        <a-sub-menu v-if="isExpert" key="question">
          <template #icon><FileTextOutlined /></template>
          <template #title>题库管理</template>
          <a-menu-item key="question-bank" @click="$router.push('/question/bank')">题库列表</a-menu-item>
          <a-menu-item v-if="isAdmin" key="question-create" @click="$router.push('/question/create')">创建题目</a-menu-item>
        </a-sub-menu>

        <!-- 教练及以上可见 -->
        <a-sub-menu v-if="isCoach" key="exam">
          <template #icon><SolutionOutlined /></template>
          <template #title>考试管理</template>
          <a-menu-item key="exam-list" @click="$router.push('/exam/list')">考试列表</a-menu-item>
          <a-menu-item v-if="isExpert" key="exam-create" @click="$router.push('/exam/create')">创建考试</a-menu-item>
        </a-sub-menu>

        <!-- 专家及以上可见 -->
        <a-sub-menu v-if="isExpert" key="live">
          <template #icon><PlayCircleOutlined /></template>
          <template #title>直播管理</template>
          <a-menu-item key="live-list" @click="$router.push('/live/list')">直播列表</a-menu-item>
          <a-menu-item v-if="isAdmin" key="live-create" @click="$router.push('/live/create')">创建直播</a-menu-item>
        </a-sub-menu>

        <!-- 专家及以上可见 -->
        <a-sub-menu v-if="isExpert" key="coach">
          <template #icon><TeamOutlined /></template>
          <template #title>教练管理</template>
          <a-menu-item key="coach-list" @click="$router.push('/coach/list')">教练列表</a-menu-item>
          <a-menu-item key="coach-review" @click="$router.push('/coach/review')">晋级审核</a-menu-item>
        </a-sub-menu>

        <!-- 教练及以上可见 -->
        <a-menu-item v-if="isCoach" key="student" @click="$router.push('/student')">
          <template #icon><UserOutlined /></template>
          <span>学员管理</span>
        </a-menu-item>

        <!-- Prompt管理 - 专家及以上可见 -->
        <a-sub-menu v-if="isExpert" key="prompts">
          <template #icon><EditOutlined /></template>
          <template #title>Prompt管理</template>
          <a-menu-item key="prompts-list" @click="$router.push('/prompts/list')">Prompt列表</a-menu-item>
          <a-menu-item v-if="isAdmin" key="prompts-create" @click="$router.push('/prompts/create')">创建Prompt</a-menu-item>
        </a-sub-menu>

        <!-- 干预包管理 - 专家及以上可见 -->
        <a-menu-item v-if="isExpert" key="interventions" @click="$router.push('/interventions')">
          <template #icon><MedicineBoxOutlined /></template>
          <span>干预包管理</span>
        </a-menu-item>

        <!-- 管理员可见 - 用户管理 -->
        <a-menu-item v-if="isAdmin" key="admin-user-management" @click="$router.push('/admin/user-management')">
          <template #icon><UsergroupAddOutlined /></template>
          <span>用户管理</span>
        </a-menu-item>

        <!-- 管理员可见 - 分配管理 -->
        <a-menu-item v-if="isAdmin" key="admin-distribution" @click="$router.push('/admin/distribution')">
          <template #icon><ApartmentOutlined /></template>
          <span>分配管理</span>
        </a-menu-item>

        <!-- 管理员可见 -->
        <a-menu-item v-if="isAdmin" key="settings" @click="$router.push('/settings')">
          <template #icon><SettingOutlined /></template>
          <span>系统设置</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <!-- 主内容区 -->
    <a-layout>
      <!-- 顶部栏 -->
      <a-layout-header class="header">
        <div class="header-left">
          <a-breadcrumb>
            <a-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
              {{ item.title }}
            </a-breadcrumb-item>
          </a-breadcrumb>
        </div>
        <div class="header-right">
          <a-dropdown>
            <a class="user-dropdown">
              <a-avatar :size="32" style="background-color: #1890ff">
                <template #icon><UserOutlined /></template>
              </a-avatar>
              <span class="username">{{ username }}</span>
            </a>
            <template #overlay>
              <a-menu>
                <a-menu-item key="profile">个人设置</a-menu-item>
                <a-menu-divider />
                <a-menu-item key="logout" @click="handleLogout">退出登录</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <!-- 内容区 -->
      <a-layout-content class="content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  DashboardOutlined,
  VideoCameraOutlined,
  FileTextOutlined,
  FileSearchOutlined,
  SolutionOutlined,
  PlayCircleOutlined,
  TeamOutlined,
  UserOutlined,
  SettingOutlined,
  EditOutlined,
  MedicineBoxOutlined,
  ShareAltOutlined,
  SafetyCertificateOutlined,
  UsergroupAddOutlined,
  ApartmentOutlined
} from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()

const collapsed = ref(false)
const selectedKeys = ref<string[]>(['dashboard'])
const openKeys = ref<string[]>([])

// 从 localStorage 读取用户信息
const username = ref(localStorage.getItem('admin_username') || '管理员')
const userRole = ref(localStorage.getItem('admin_role') || 'ADMIN')

// 权限判断（v18统一角色名称: GROWER/COACH/SUPERVISOR/PROMOTER/MASTER/ADMIN）
const roleLevel = computed(() => {
  const levels: Record<string, number> = {
    OBSERVER: 1, GROWER: 2, SHARER: 3, COACH: 4,
    PROMOTER: 5, SUPERVISOR: 5, MASTER: 6, ADMIN: 99,
    // 向后兼容旧角色名
    PATIENT: 2, EXPERT: 5, COACH_SENIOR: 4, COACH_INTERMEDIATE: 4, COACH_JUNIOR: 4,
  }
  return levels[userRole.value] || 0
})
const isAdmin = computed(() => roleLevel.value >= 99)
const isExpert = computed(() => roleLevel.value >= 5)
const isCoach = computed(() => roleLevel.value >= 4)

// 面包屑
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  return matched.map(item => ({
    path: item.path,
    title: item.meta?.title as string
  }))
})

// 监听路由变化，更新选中菜单
watch(() => route.path, (path) => {
  if (path.startsWith('/coach/my/')) {
    openKeys.value = ['coach-my']
    if (path.includes('students')) selectedKeys.value = ['coach-my-students']
    else if (path.includes('performance')) selectedKeys.value = ['coach-my-performance']
    else if (path.includes('certification')) selectedKeys.value = ['coach-my-certification']
    else if (path.includes('tools')) selectedKeys.value = ['coach-my-tools']
  } else if (path.startsWith('/coach/content-sharing')) {
    selectedKeys.value = ['coach-content-sharing']
  } else if (path.startsWith('/coach/student-assessment')) {
    openKeys.value = ['coach-my']
    selectedKeys.value = ['coach-my-students']
  } else if (path.startsWith('/expert/my/')) {
    openKeys.value = ['expert-my']
    if (path.includes('supervision')) selectedKeys.value = ['expert-my-supervision']
    else if (path.includes('reviews')) selectedKeys.value = ['expert-my-reviews']
    else if (path.includes('research')) selectedKeys.value = ['expert-my-research']
  } else if (path === '/admin/user-management') {
    selectedKeys.value = ['admin-user-management']
  } else if (path === '/admin/distribution') {
    selectedKeys.value = ['admin-distribution']
  } else if (path.startsWith('/course')) {
    openKeys.value = ['course']
    selectedKeys.value = path.includes('create') ? ['course-create'] : ['course-list']
  } else if (path.startsWith('/content')) {
    openKeys.value = ['content']
    if (path.includes('review')) selectedKeys.value = ['content-review']
    else if (path.includes('articles')) selectedKeys.value = ['content-articles']
    else if (path.includes('cases')) selectedKeys.value = ['content-cases']
    else if (path.includes('cards')) selectedKeys.value = ['content-cards']
    else selectedKeys.value = ['content-review']
  } else if (path.startsWith('/question')) {
    openKeys.value = ['question']
    selectedKeys.value = path.includes('create') ? ['question-create'] : ['question-bank']
  } else if (path.startsWith('/exam')) {
    openKeys.value = ['exam']
    selectedKeys.value = path.includes('create') ? ['exam-create'] : ['exam-list']
  } else if (path.startsWith('/live')) {
    openKeys.value = ['live']
    selectedKeys.value = path.includes('create') ? ['live-create'] : ['live-list']
  } else if (path.startsWith('/coach')) {
    openKeys.value = ['coach']
    selectedKeys.value = path.includes('review') ? ['coach-review'] : ['coach-list']
  } else if (path === '/student') {
    selectedKeys.value = ['student']
  } else if (path.startsWith('/prompts')) {
    openKeys.value = ['prompts']
    selectedKeys.value = path.includes('create') ? ['prompts-create'] : ['prompts-list']
  } else if (path === '/interventions') {
    selectedKeys.value = ['interventions']
  } else if (path === '/settings') {
    selectedKeys.value = ['settings']
  } else {
    selectedKeys.value = ['dashboard']
  }
}, { immediate: true })

const handleLogout = () => {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_refresh_token')
  localStorage.removeItem('admin_username')
  localStorage.removeItem('admin_role')
  localStorage.removeItem('admin_level')
  message.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  background: rgba(255, 255, 255, 0.1);
}

.header {
  background: #fff;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin-left: 8px;
  color: #333;
}

.content {
  margin: 24px;
  padding: 24px;
  background: #fff;
  min-height: calc(100vh - 64px - 48px);
  border-radius: 4px;
}
</style>
