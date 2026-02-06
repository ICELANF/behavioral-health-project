<script setup lang="ts">
// ============================================================
// DecisionTraceVue.vue - 决策追踪组件Vue包装器
// 位置: src/components/vue-wrappers/DecisionTraceVue.vue
// ============================================================

import { ref, onMounted, onUnmounted, watch } from 'vue'
import { createRoot, Root } from 'react-dom/client'
import React from 'react'
import type { TraceNode } from '@/types/react-components'

// Props定义
interface Props {
  nodes: TraceNode[]
  selectedNodeId?: string
  containerClass?: string
}

// Emits定义
interface Emits {
  (e: 'nodeClick', node: TraceNode): void
  (e: 'mounted'): void
  (e: 'error', error: Error): void
}

const props = withDefaults(defineProps<Props>(), {
  containerClass: '',
})

const emit = defineEmits<Emits>()

const containerRef = ref<HTMLDivElement | null>(null)
let reactRoot: Root | null = null

const renderReact = async () => {
  if (!containerRef.value) return
  
  try {
    const { DecisionTrace } = await import('@/components/react/Trace/DecisionTrace')
    
    if (!reactRoot) {
      reactRoot = createRoot(containerRef.value)
    }
    
    const handleNodeClick = (node: TraceNode) => {
      emit('nodeClick', node)
    }
    
    reactRoot.render(
      React.createElement(DecisionTrace, {
        nodes: props.nodes,
        selectedNodeId: props.selectedNodeId,
        onNodeClick: handleNodeClick,
      })
    )
  } catch (error) {
    console.error('[DecisionTraceVue] Render error:', error)
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
  () => [props.nodes, props.selectedNodeId],
  () => renderReact(),
  { deep: true }
)
</script>

<template>
  <div 
    ref="containerRef" 
    :class="['decision-trace-container', containerClass]"
    data-react-component="DecisionTrace"
  />
</template>

<style scoped>
.decision-trace-container {
  width: 100%;
  min-height: 300px;
}
</style>
