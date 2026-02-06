<script setup lang="ts">
// ============================================================
// DualSignPanelVue.vue - 双签审批面板Vue包装器
// 位置: src/components/vue-wrappers/DualSignPanelVue.vue
// ============================================================

import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { createRoot, Root } from 'react-dom/client'
import React from 'react'
import type { AuditCase, PublishResult } from '@/types/react-components'

// 动态导入React组件
const DualSignPanel = () => import('@/components/react/Expert/DualSignPanel').then(m => m.DualSignPanel)

// Props定义
interface Props {
  auditCase: AuditCase
  containerClass?: string
}

// Emits定义
interface Emits {
  (e: 'publish', result: PublishResult): void
  (e: 'signChange', signs: { master: boolean; secondary: boolean }): void
  (e: 'mounted'): void
  (e: 'error', error: Error): void
}

const props = withDefaults(defineProps<Props>(), {
  containerClass: '',
})

const emit = defineEmits<Emits>()

// 容器引用
const containerRef = ref<HTMLDivElement | null>(null)
let reactRoot: Root | null = null

// 渲染React组件
const renderReact = async () => {
  if (!containerRef.value) return
  
  try {
    const { DualSignPanel: Component } = await import('@/components/react/Expert/DualSignPanel')
    
    if (!reactRoot) {
      reactRoot = createRoot(containerRef.value)
    }
    
    // 创建事件处理器
    const handlePublish = (result: PublishResult) => {
      emit('publish', result)
    }
    
    const handleSignChange = (signs: { master: boolean; secondary: boolean }) => {
      emit('signChange', signs)
    }
    
    reactRoot.render(
      React.createElement(Component, {
        auditCase: props.auditCase,
        onPublish: handlePublish,
        onSignChange: handleSignChange,
      })
    )
  } catch (error) {
    console.error('[DualSignPanelVue] Render error:', error)
    emit('error', error as Error)
  }
}

// 生命周期
onMounted(() => {
  renderReact()
  emit('mounted')
})

onUnmounted(() => {
  if (reactRoot) {
    reactRoot.unmount()
    reactRoot = null
  }
})

// 监听props变化
watch(
  () => props.auditCase,
  () => renderReact(),
  { deep: true }
)
</script>

<template>
  <div 
    ref="containerRef" 
    :class="['dual-sign-panel-container', containerClass]"
    data-react-component="DualSignPanel"
  />
</template>

<style scoped>
.dual-sign-panel-container {
  width: 100%;
  min-height: 600px;
}
</style>
