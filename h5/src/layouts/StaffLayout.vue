<template>
  <div class="staff-shell">
    <!-- ── 侧边栏 ── -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-mark">行健</div>
        <span class="logo-text">Staff Portal</span>
      </div>

      <nav class="sidebar-nav">
        <template v-for="item in menuItems" :key="item.path">
          <router-link :to="item.path" class="nav-item" :class="{ active: isActive(item.path) }">
            <span class="nav-icon">{{ item.icon }}</span>
            <span class="nav-label">{{ item.label }}</span>
          </router-link>
        </template>
      </nav>

      <div class="sidebar-footer">
        <div class="role-badge" :style="{ background: roleBadgeColor }">{{ roleLabel }}</div>
      </div>
    </aside>

    <!-- ── 主区域 ── -->
    <div class="main-area">
      <!-- 顶栏 -->
      <header class="topbar">
        <div class="topbar-left">
          <h1 class="page-title">{{ currentPageTitle }}</h1>
        </div>
        <div class="topbar-right">
          <span class="username">{{ username }}</span>
          <button class="logout-btn" @click="handleLogout">退出</button>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content-area">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import storage from '@/utils/storage'

const router = useRouter()
const route = useRoute()

const authUser = storage.getAuthUser()
const role = ((authUser?.role) || 'coach').toLowerCase()
const username = authUser?.full_name || authUser?.username || '用户'

// ── 角色色标 ──
const ROLE_COLORS: Record<string, string> = {
  coach: '#5c6bc0',
  promoter: '#e53935',
  supervisor: '#8e24aa',
  master: '#f9a825',
  admin: '#c62828',
}
const ROLE_LABELS: Record<string, string> = {
  coach: '教练 L3',
  promoter: '促进师 L4',
  supervisor: '督导 L4',
  master: '大师 L5',
  admin: '管理员',
}
const roleBadgeColor = ROLE_COLORS[role] || '#555'
const roleLabel = ROLE_LABELS[role] || role

// ── 菜单定义 ──
const MENUS: Record<string, { path: string; icon: string; label: string }[]> = {
  coach: [
    { path: '/staff/coach/dashboard',     icon: '🏠', label: '工作台' },
    { path: '/staff/coach/students',      icon: '👥', label: '学员管理' },
    { path: '/staff/coach/assessment',    icon: '📋', label: '评估管理' },
    { path: '/staff/coach/flywheel',      icon: '🔄', label: 'AI飞轮' },
    { path: '/staff/coach/push-queue',    icon: '📤', label: '推送审批' },
    { path: '/staff/coach/health-review', icon: '❤️', label: '健康审核' },
    { path: '/staff/coach/risk',          icon: '⚠️', label: '风险管理' },
    { path: '/staff/coach/analytics',     icon: '📊', label: '数据分析' },
    { path: '/staff/coach/promotion',     icon: '⬆️', label: '晋级审核' },
  ],
  supervisor: [
    { path: '/staff/supervisor/dashboard',    icon: '🏠', label: '工作台' },
    { path: '/staff/supervisor/coaches',      icon: '👥', label: '教练管理' },
    { path: '/staff/supervisor/review-queue', icon: '🔍', label: '审核队列' },
    { path: '/staff/supervisor/promotion',    icon: '⬆️', label: '晋级复核' },
  ],
  master: [
    { path: '/staff/master/dashboard',       icon: '🏠', label: '工作台' },
    { path: '/staff/master/critical-review', icon: '🚨', label: '危急病例' },
    { path: '/staff/master/knowledge',       icon: '📚', label: '知识库' },
    { path: '/staff/master/promotion',       icon: '⬆️', label: '晋级终审' },
  ],
  admin: [
    { path: '/staff/admin/overview',   icon: '🖥️', label: '系统概览' },
    { path: '/staff/admin/users',      icon: '👤', label: '用户管理' },
    { path: '/staff/admin/content',    icon: '📄', label: '内容管理' },
    { path: '/staff/admin/coaches',    icon: '🎓', label: '教练审核' },
    { path: '/staff/admin/promotions', icon: '⬆️', label: '晋级总览' },
    { path: '/staff/admin/reports',    icon: '📊', label: '数据报表' },
    { path: '/staff/admin/config',     icon: '⚙️', label: '系统配置' },
    { path: '/staff/admin/logs',       icon: '📋', label: '操作日志' },
  ],
}

// promoter → use supervisor menu
const effectiveRole = role === 'promoter' ? 'supervisor' : role
const menuItems = computed(() => MENUS[effectiveRole] || MENUS.coach)

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}

// ── 当前页标题 ──
const currentPageTitle = computed(() => {
  const item = menuItems.value.find(m => m.path === route.path)
  return item?.label || 'Staff Portal'
})

// ── 退出 ──
function handleLogout() {
  storage.clearAuth()
  router.replace('/portal')
}
</script>

<style scoped>
.staff-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: #f3f4f6;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ── 侧边栏 ── */
.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #1e2330;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 16px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

.logo-mark {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  flex-shrink: 0;
}

.logo-text {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255,255,255,0.8);
  letter-spacing: 0.5px;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 8px;
  text-decoration: none;
  color: rgba(255,255,255,0.6);
  font-size: 14px;
  transition: all 0.15s;
  cursor: pointer;
}

.nav-item:hover {
  background: rgba(255,255,255,0.07);
  color: rgba(255,255,255,0.9);
}

.nav-item.active {
  background: rgba(59,130,246,0.25);
  color: #93c5fd;
}

.nav-icon { font-size: 16px; width: 20px; text-align: center; flex-shrink: 0; }
.nav-label { font-size: 13px; font-weight: 500; }

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(255,255,255,0.08);
}

.role-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  opacity: 0.9;
}

/* ── 主区域 ── */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.topbar {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.logout-btn {
  padding: 6px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.logout-btn:hover {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #ef4444;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>

