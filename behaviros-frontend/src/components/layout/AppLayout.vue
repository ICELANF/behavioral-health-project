<!--
  AppLayout.vue — 主布局
  侧边栏导航 + 顶栏 + 内容区
  根据角色动态渲染菜单
-->

<template>
  <a-layout class="app-layout">
    <!-- 侧边栏 -->
    <a-layout-sider
      v-model:collapsed="appStore.sidebarCollapsed"
      :trigger="null"
      collapsible
      :width="240"
      :collapsed-width="64"
      class="app-sider"
    >
      <!-- Logo -->
      <div class="sider-logo" @click="$router.push('/')">
        <div class="logo-icon">行</div>
        <transition name="fade">
          <span v-if="!appStore.sidebarCollapsed" class="logo-text">行健平台</span>
        </transition>
      </div>

      <!-- 导航菜单 -->
      <a-menu
        v-model:selectedKeys="selectedKeys"
        mode="inline"
        :items="menuItems"
        @click="onMenuClick"
      />

      <!-- 底部折叠按钮 -->
      <div class="sider-footer">
        <a-button type="text" block @click="appStore.toggleSidebar">
          <template #icon>
            <menu-fold-outlined v-if="!appStore.sidebarCollapsed" />
            <menu-unfold-outlined v-else />
          </template>
        </a-button>
      </div>
    </a-layout-sider>

    <!-- 右侧内容 -->
    <a-layout>
      <!-- 顶栏 -->
      <a-layout-header class="app-header">
        <div class="header-left">
          <a-breadcrumb>
            <a-breadcrumb-item>
              <router-link to="/">首页</router-link>
            </a-breadcrumb-item>
            <a-breadcrumb-item v-if="$route.meta.title">
              {{ $route.meta.title }}
            </a-breadcrumb-item>
          </a-breadcrumb>
        </div>

        <div class="header-right">
          <!-- 旅程阶段标签 -->
          <a-tag v-if="authStore.user?.journey_stage" :color="stageColor">
            {{ stageLabel }}
          </a-tag>

          <!-- 用户头像 + 下拉 -->
          <a-dropdown>
            <div class="user-avatar-wrap">
              <a-avatar :size="36" class="user-avatar">
                {{ authStore.displayName.charAt(0) }}
              </a-avatar>
              <span class="user-name">{{ authStore.displayName }}</span>
            </div>
            <template #overlay>
              <a-menu>
                <a-menu-item key="profile" @click="$router.push('/profile')">
                  <user-outlined /> 个人设置
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="logout" @click="handleLogout" danger>
                  <logout-outlined /> 退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <!-- 页面内容 -->
      <a-layout-content class="app-content">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <keep-alive :include="cachedViews">
              <component :is="Component" />
            </keep-alive>
          </transition>
        </router-view>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { UserRole, STAGE_LABELS, STAGE_COLORS, type JourneyStage } from '@/types'
import {
  HomeOutlined, CompassOutlined, FormOutlined, RobotOutlined,
  ThunderboltOutlined, TrophyOutlined, ReadOutlined, HeartOutlined,
  StarOutlined, UserOutlined, LogoutOutlined, TeamOutlined,
  MedicineBoxOutlined, SettingOutlined, MenuFoldOutlined, MenuUnfoldOutlined,
} from '@ant-design/icons-vue'
import type { ItemType } from 'ant-design-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

const selectedKeys = ref<string[]>([])
const cachedViews = ref<string[]>([])

// 根据路由更新选中菜单
watch(() => route.path, (path) => {
  selectedKeys.value = [path]
}, { immediate: true })

// 旅程阶段显示
const stageLabel = computed(() => {
  const stage = authStore.user?.journey_stage as JourneyStage
  return stage ? STAGE_LABELS[stage] || stage : ''
})
const stageColor = computed(() => {
  const stage = authStore.user?.journey_stage as JourneyStage
  return stage ? STAGE_COLORS[stage] || '#999' : '#999'
})

// 动态菜单 — 根据角色过滤
const menuItems = computed<ItemType[]>(() => {
  const items: ItemType[] = [
    { key: '/', icon: () => h(HomeOutlined), label: '首页' },
    { key: '/journey', icon: () => h(CompassOutlined), label: '我的旅程' },
    { key: '/assessment', icon: () => h(FormOutlined), label: '健康评估' },
    { key: '/agent', icon: () => h(RobotOutlined), label: 'AI助手' },
    { key: '/actions', icon: () => h(ThunderboltOutlined), label: '今日行动' },
    { key: '/challenges', icon: () => h(TrophyOutlined), label: '挑战打卡' },
    { key: '/learning', icon: () => h(ReadOutlined), label: '学习成长' },
    { key: '/health-data', icon: () => h(HeartOutlined), label: '健康数据' },
    { key: '/points', icon: () => h(StarOutlined), label: '我的积分' },
  ]

  // 教练+ 菜单
  if (authStore.isCoachOrAbove) {
    items.push(
      { type: 'divider' } as any,
      { key: '/coach', icon: () => h(TeamOutlined), label: '教练工作台' },
      { key: '/coach/clients', icon: () => h(UserOutlined), label: '我的学员' },
      { key: '/rx/dashboard', icon: () => h(MedicineBoxOutlined), label: '行为处方' },
    )
  }

  // Admin 菜单
  if (authStore.isAdmin) {
    items.push(
      { type: 'divider' } as any,
      { key: '/admin', icon: () => h(SettingOutlined), label: '管理后台' },
    )
  }

  return items
})

function onMenuClick({ key }: { key: string }) {
  router.push(key)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}

.app-sider {
  background: linear-gradient(180deg, #0f1a2e 0%, #1a2744 100%);
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
  overflow-y: auto;
}

.sider-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #4aa883 0%, #2d8e69 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Noto Serif SC', serif;
  font-weight: 700;
  font-size: 18px;
  color: white;
  flex-shrink: 0;
}

.logo-text {
  font-family: 'Noto Serif SC', serif;
  font-weight: 600;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.92);
  white-space: nowrap;
}

.app-sider :deep(.ant-menu) {
  background: transparent;
  border: none;
  flex: 1;
}

.app-sider :deep(.ant-menu-item) {
  color: rgba(255, 255, 255, 0.65);
  margin: 2px 8px;
  border-radius: 8px;
}

.app-sider :deep(.ant-menu-item:hover) {
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.08);
}

.app-sider :deep(.ant-menu-item-selected) {
  color: white;
  background: linear-gradient(135deg, rgba(74, 168, 131, 0.3) 0%, rgba(45, 142, 105, 0.2) 100%);
}

.sider-footer {
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.sider-footer :deep(.ant-btn) {
  color: rgba(255, 255, 255, 0.45);
}

.app-header {
  background: white;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-avatar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.user-avatar-wrap:hover {
  background: #f5f5f5;
}

.user-avatar {
  background: linear-gradient(135deg, #4aa883 0%, #2d8e69 100%);
  font-family: 'Noto Sans SC', sans-serif;
  font-weight: 600;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.app-content {
  margin: 16px;
  min-height: calc(100vh - 56px - 32px);
}

/* 页面切换动画 */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-leave-to {
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
