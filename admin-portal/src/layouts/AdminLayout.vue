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

        <!-- 专家及以上可见 -->
        <a-sub-menu v-if="isExpert" key="course">
          <template #icon><VideoCameraOutlined /></template>
          <template #title>课程管理</template>
          <a-menu-item key="course-list" @click="$router.push('/course/list')">课程列表</a-menu-item>
          <a-menu-item v-if="isAdmin" key="course-create" @click="$router.push('/course/create')">创建课程</a-menu-item>
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
  SolutionOutlined,
  PlayCircleOutlined,
  TeamOutlined,
  UserOutlined,
  SettingOutlined,
  EditOutlined,
  MedicineBoxOutlined
} from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()

const collapsed = ref(false)
const selectedKeys = ref<string[]>(['dashboard'])
const openKeys = ref<string[]>([])

// 从 localStorage 读取用户信息
const username = ref(localStorage.getItem('admin_username') || '管理员')
const userRole = ref(localStorage.getItem('admin_role') || 'ADMIN')

// 权限判断
const isAdmin = computed(() => userRole.value === 'ADMIN')
const isExpert = computed(() => ['ADMIN', 'EXPERT'].includes(userRole.value))
const isCoach = computed(() => ['ADMIN', 'EXPERT', 'COACH_SENIOR', 'COACH_INTERMEDIATE', 'COACH_JUNIOR'].includes(userRole.value))

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
  if (path.startsWith('/course')) {
    openKeys.value = ['course']
    selectedKeys.value = path.includes('create') ? ['course-create'] : ['course-list']
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
