<script setup lang="ts">
// ============================================================
// ExpertWorkspaceVue.vue - 专家工作台Vue包装器
// 位置: src/components/vue-wrappers/ExpertWorkspaceVue.vue
// ============================================================

import { ref, onMounted, onUnmounted, watch } from 'vue'
import { createRoot, Root } from 'react-dom/client'
import React from 'react'
import type { PublishResult } from '@/types/react-components'

// Props定义
interface Props {
  initialTab?: 'audit' | 'trace' | 'brain'
  containerClass?: string
}

// Emits定义
interface Emits {
  (e: 'tabChange', tab: string): void
  (e: 'publish', result: PublishResult): void
  (e: 'mounted'): void
  (e: 'error', error: Error): void
}

const props = withDefaults(defineProps<Props>(), {
  initialTab: 'audit',
  containerClass: '',
})

const emit = defineEmits<Emits>()

const containerRef = ref<HTMLDivElement | null>(null)
let reactRoot: Root | null = null

const renderReact = async () => {
  if (!containerRef.value) return
  
  try {
    const { default: ExpertWorkspace } = await import('@/components/react/pages/ExpertWorkspace')
    
    if (!reactRoot) {
      reactRoot = createRoot(containerRef.value)
    }
    
    const handleTabChange = (tab: string) => {
      emit('tabChange', tab)
    }
    
    const handlePublish = (result: PublishResult) => {
      emit('publish', result)
    }
    
    reactRoot.render(
      React.createElement(ExpertWorkspace, {
        initialTab: props.initialTab,
        onTabChange: handleTabChange,
        onPublish: handlePublish,
      })
    )
  } catch (error) {
    console.error('[ExpertWorkspaceVue] Render error:', error)
    emit('error', error as Error)
  }
}

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

watch(
  () => props.initialTab,
  () => renderReact(),
)
</script>

<template>
  <div 
    ref="containerRef" 
    :class="['expert-workspace-container', containerClass]"
    data-react-component="ExpertWorkspace"
  />
</template>

<style scoped>
.expert-workspace-container {
  width: 100%;
  min-height: 100vh;
}
</style>
