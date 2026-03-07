<template>
  <div class="app-shell">
    <router-view />
    <!-- Bottom tab bar (only on main pages) -->
    <nav class="tab-bar" v-if="showTabBar">
      <div
        v-for="t in tabs" :key="t.path"
        class="tab-item" :class="{ active: route.path === t.path }"
        @click="router.push(t.path)"
      >
        <span class="tab-icon">{{ t.icon }}</span>
        <span class="tab-label">{{ t.label }}</span>
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
  { path: '/', icon: '\u{1F3E0}', label: '\u5DE5\u4F5C\u53F0' },
  { path: '/seekers', icon: '\u{1F465}', label: '\u670D\u52A1' },
  { path: '/knowledge', icon: '\u{1F4DA}', label: '\u77E5\u8BC6\u5E93' },
  { path: '/chat', icon: '\u{1F4AC}', label: '\u667A\u4F34' },
  { path: '/profile', icon: '\u{1F464}', label: '\u6211\u7684' },
]

const tabPaths = tabs.map(t => t.path)
const showTabBar = computed(() => tabPaths.includes(route.path))
</script>

<style scoped>
.app-shell {
  max-width: 480px; margin: 0 auto; min-height: 100vh;
  background: var(--bg); position: relative;
}
.tab-bar {
  position: fixed; bottom: 0; left: 50%; transform: translateX(-50%);
  width: 100%; max-width: 480px;
  display: flex; background: white;
  border-top: 1px solid var(--border);
  padding: 6px 0 env(safe-area-inset-bottom, 8px);
  z-index: 100;
}
.tab-item {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; gap: 2px; cursor: pointer;
  padding: 4px 0; transition: all .2s;
}
.tab-icon { font-size: 20px; }
.tab-label { font-size: 10px; font-weight: 600; color: var(--sub); }
.tab-item.active .tab-label { color: var(--xzb-primary); }
</style>
