<script setup lang="ts">
// ============================================================
// CGMChartVue.vue - 血糖曲线图表Vue包装器
// 位置: src/components/vue-wrappers/CGMChartVue.vue
// ============================================================

import { ref, onMounted, onUnmounted, watch } from 'vue'
import { createRoot, Root } from 'react-dom/client'
import React from 'react'
import type { CGMDataPoint } from '@/types/react-components'

// Props定义
interface Props {
  data?: CGMDataPoint[]
  patientId?: string
  showRawData?: boolean
  height?: number
  containerClass?: string
}

// Emits定义
interface Emits {
  (e: 'dataPointClick', point: CGMDataPoint): void
  (e: 'mounted'): void
  (e: 'error', error: Error): void
}

const props = withDefaults(defineProps<Props>(), {
  showRawData: false,
  height: 200,
  containerClass: '',
})

const emit = defineEmits<Emits>()

const containerRef = ref<HTMLDivElement | null>(null)
let reactRoot: Root | null = null

const renderReact = async () => {
  if (!containerRef.value) return
  
  try {
    const { CGMChart } = await import('@/components/react/Expert/CGMChart')
    
    if (!reactRoot) {
      reactRoot = createRoot(containerRef.value)
    }
    
    const handleDataPointClick = (point: CGMDataPoint) => {
      emit('dataPointClick', point)
    }
    
    reactRoot.render(
      React.createElement(CGMChart, {
        data: props.data,
        patientId: props.patientId,
        showRawData: props.showRawData,
        height: props.height,
        onDataPointClick: handleDataPointClick,
      })
    )
  } catch (error) {
    console.error('[CGMChartVue] Render error:', error)
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
  () => [props.data, props.patientId, props.showRawData, props.height],
  () => renderReact(),
  { deep: true }
)
</script>

<template>
  <div 
    ref="containerRef" 
    :class="['cgm-chart-container', containerClass]"
    :style="{ minHeight: `${height}px` }"
    data-react-component="CGMChart"
  />
</template>

<style scoped>
.cgm-chart-container {
  width: 100%;
  background: rgba(71, 85, 105, 0.4);
  backdrop-filter: blur(4px);
  border-radius: 0.75rem;
  border: 1px solid rgba(148, 163, 184, 0.6);
  padding: 1rem;
}
</style>
