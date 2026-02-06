<script setup lang="ts">
// ============================================================
// JourneyPageVue.vue - 成长之旅页面Vue包装器
// 位置: src/components/vue-wrappers/JourneyPageVue.vue
// ============================================================

import { ref, onMounted, onUnmounted, watch } from 'vue'
import { createRoot, Root } from 'react-dom/client'
import React from 'react'
import type { AuditLog } from '@/types/react-components'

// Props定义
interface Props {
  patientId?: string
  showHeader?: boolean
  containerClass?: string
}

// Emits定义
interface Emits {
  (e: 'messageReceived', message: AuditLog): void
  (e: 'mounted'): void
  (e: 'error', error: Error): void
}

const props = withDefaults(defineProps<Props>(), {
  showHeader: true,
  containerClass: '',
})

const emit = defineEmits<Emits>()

const containerRef = ref<HTMLDivElement | null>(null)
let reactRoot: Root | null = null

const renderReact = async () => {
  if (!containerRef.value) return
  
  try {
    const { JourneyPage } = await import('@/components/react/pages/JourneyPage')
    
    if (!reactRoot) {
      reactRoot = createRoot(containerRef.value)
    }
    
    const handleMessageReceived = (message: AuditLog) => {
      emit('messageReceived', message)
    }
    
    reactRoot.render(
      React.createElement(JourneyPage, {
        patientId: props.patientId,
        showHeader: props.showHeader,
        onMessageReceived: handleMessageReceived,
      })
    )
  } catch (error) {
    console.error('[JourneyPageVue] Render error:', error)
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
  () => [props.patientId, props.showHeader],
  () => renderReact(),
)
</script>

<template>
  <div 
    ref="containerRef" 
    :class="['journey-page-container', containerClass]"
    data-react-component="JourneyPage"
  />
</template>

<style scoped>
.journey-page-container {
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(to bottom right, #f0fdf4, white, #f0fdf4);
}
</style>
