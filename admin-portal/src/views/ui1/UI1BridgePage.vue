<template>
  <div class="ui1-frame-container">
    <!-- 顶部提示条 -->
    <div class="frame-toolbar">
      <div class="toolbar-left">
        <span class="dot blue"></span>
        <span class="toolbar-title">{{ pageTitle }}</span>
      </div>
      <div class="toolbar-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.path"
          :class="['tab-btn', { active: currentPath === tab.path }]"
          @click="switchTab(tab.path)"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          {{ tab.label }}
        </button>
      </div>
      <button class="open-btn" @click="openInNewTab" title="新窗口打开">
        ↗ 新窗口
      </button>
    </div>

    <!-- iframe -->
    <iframe
      :src="frameSrc"
      class="ui1-iframe"
      frameborder="0"
      allow="clipboard-write"
      @load="onFrameLoad"
    />

    <!-- 加载遮罩 -->
    <div v-if="loading" class="frame-loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const UI1_BASE = 'http://localhost:5175'

const tabs = [
  { path: '/user',  label: '用户端',  icon: '👤' },
  { path: '/coach', label: '教练端',  icon: '🎯' },
  { path: '/docs',  label: '组件文档', icon: '📄' },
]

const currentPath = ref('/user')
const loading = ref(true)

const frameSrc = computed(() => `${UI1_BASE}${currentPath.value}`)
const pageTitle = computed(() => tabs.find(t => t.path === currentPath.value)?.label || '')

const switchTab = (path: string) => {
  loading.value = true
  currentPath.value = path
}

const onFrameLoad = () => {
  loading.value = false
}

const openInNewTab = () => {
  window.open(frameSrc.value, '_blank')
}
</script>

<style scoped>
.ui1-frame-container {
  position: relative;
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.frame-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  z-index: 10;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.dot.blue { background: #3b82f6; }

.toolbar-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.toolbar-tabs {
  display: flex;
  gap: 4px;
  background: #f1f5f9;
  padding: 3px;
  border-radius: 10px;
}

.tab-btn {
  padding: 6px 14px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.tab-btn:hover {
  color: #1e293b;
  background: rgba(255,255,255,0.5);
}

.tab-btn.active {
  color: white;
  background: #3b82f6;
  box-shadow: 0 1px 3px rgba(59,130,246,0.3);
}

.tab-icon {
  font-size: 14px;
}

.open-btn {
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 12px;
  color: #64748b;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.open-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.ui1-iframe {
  flex: 1;
  width: 100%;
  border: none;
}

.frame-loading {
  position: absolute;
  inset: 48px 0 0 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(239,246,255,0.9);
  backdrop-filter: blur(4px);
  z-index: 5;
}

.frame-loading p {
  color: #64748b;
  font-size: 14px;
  margin-top: 12px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
