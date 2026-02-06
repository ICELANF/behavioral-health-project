<script setup lang="ts">
// ============================================================
// LogicFlowBridgeVue.vue - 决策逻辑联动组件Vue包装器
// 位置: src/components/vue-wrappers/LogicFlowBridgeVue.vue
// ============================================================

import { ref, onMounted, onUnmounted, watch } from 'vue'
import { createRoot, Root } from 'react-dom/client'
import React from 'react'
import type { DecisionRules } from '@/types/react-components'

// Props定义
interface Props {
  decisionRules: DecisionRules
  highlightLine?: number
  containerClass?: string
}

// Emits定义
interface Emits {
  (e: 'lineHover', lineNumber: number | null): void
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
    const { LogicFlowBridge } = await import('@/components/react/Expert/LogicFlowBridge')
    
    if (!reactRoot) {
      reactRoot = createRoot(containerRef.value)
    }
    
    const handleLineHover = (lineNumber: number | null) => {
      emit('lineHover', lineNumber)
    }
    
    reactRoot.render(
      React.createElement(LogicFlowBridge, {
        decisionRules: props.decisionRules,
        highlightLine: props.highlightLine,
        onLineHover: handleLineHover,
      })
    )
  } catch (error) {
    console.error('[LogicFlowBridgeVue] Render error:', error)
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
  () => [props.decisionRules, props.highlightLine],
  () => renderReact(),
  { deep: true }
)
</script>

<template>
  <div 
    ref="containerRef" 
    :class="['logic-flow-bridge-container', containerClass]"
    data-react-component="LogicFlowBridge"
  />
</template>

<style scoped>
.logic-flow-bridge-container {
  width: 100%;
  min-height: 400px;
}
</style>
