<template>
  <div class="app-shell">
    <router-view />
    <!-- Bottom Tab Bar -->
    <nav class="tab-bar" v-if="showTabBar">
      <div
        v-for="tab in tabs" :key="tab.path"
        class="tab-item" :class="{ active: route.path === tab.path }"
        @click="router.push(tab.path)"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </div>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const tabs = [
  { path: '/',          icon: '🏠', label: '今日' },
  { path: '/food',      icon: '🍽️', label: '营养' },
  { path: '/survey',    icon: '📋', label: '问卷' },
  { path: '/report',    icon: '📊', label: '监测' },
  { path: '/profile',   icon: '👤', label: '我的' },
]

const hideTabBarRoutes = ['/login', '/food/record', '/food/survey']
const showTabBar = computed(() => !hideTabBarRoutes.includes(route.path))
</script>

<style scoped>
.app-shell {
  max-width: 390px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--bg);
  position: relative;
}

.tab-bar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 390px;
  background: white;
  border-top: 1px solid var(--border);
  display: flex;
  padding: 8px 0 max(16px, env(safe-area-inset-bottom));
  box-shadow: 0 -4px 20px rgba(0,0,0,.06);
  z-index: 50;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  cursor: pointer;
  padding: 4px 0;
}

.tab-icon { font-size: 22px; }
.tab-label { font-size: 10px; color: var(--sub); font-weight: 500; }
.tab-item.active .tab-label { color: var(--teal); font-weight: 700; }
</style>
