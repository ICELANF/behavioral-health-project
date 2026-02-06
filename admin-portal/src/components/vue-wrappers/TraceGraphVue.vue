<script setup lang="ts">
// ============================================================
// TraceGraphVue.vue - 追踪图表组件Vue包装器
// 位置: src/components/vue-wrappers/TraceGraphVue.vue
// ============================================================

import { ref, onMounted, onUnmounted, watch } from 'vue'
import { createRoot, Root } from 'react-dom/client'
import React from 'react'
import type { TraceSession, TraceNode } from '@/types/react-components'

// Props定义
interface Props {
  session: TraceSession
  layout?: 'horizontal' | 'vertical'
  containerClass?: string
}

// Emits定义
interface Emits {
  (e: 'nodeHover', node: TraceNode | null): void
  (e: 'mounted'): void
  (e: 'error', error: Error): void
}

const props = withDefaults(defineProps<Props>(), {
  layout: 'horizontal',
  containerClass: '',
})

const emit = defineEmits<Emits>()

const containerRef = ref<HTMLDivElement | null>(null)
let reactRoot: Root | null = null

const renderReact = async () => {
  if (!containerRef.value) return
  
  try {
    const { TraceGraph } = await import('@/components/react/Trace/TraceGraph')
    
    if (!reactRoot) {
      reactRoot = createRoot(containerRef.value)
    }
    
    const handleNodeHover = (node: TraceNode | null) => {
      emit('nodeHover', node)
    }
    
    reactRoot.render(
      React.createElement(TraceGraph, {
        session: props.session,
        layout: props.layout,
        onNodeHover: handleNodeHover,
      })
    )
  } catch (error) {
    console.error('[TraceGraphVue] Render error:', error)
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
  () => [props.session, props.layout],
  () => renderReact(),
  { deep: true }
)
</script>

<template>
  <div 
    ref="containerRef" 
    :class="['trace-graph-container', containerClass]"
    data-react-component="TraceGraph"
  />
</template>

<style scoped>
.trace-graph-container {
  width: 100%;
  min-height: 400px;
  overflow: auto;
}
</style>
