<template>
  <div ref="reactRoot" class="react-wrapper"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { createRoot, type Root } from 'react-dom/client'
import { createElement } from 'react'

const props = defineProps<{
  component: any
  componentProps?: Record<string, any>
}>()

const reactRoot = ref<HTMLDivElement | null>(null)
let root: Root | null = null

const renderReactComponent = () => {
  if (reactRoot.value && props.component) {
    if (!root) {
      root = createRoot(reactRoot.value)
    }
    root.render(createElement(props.component, props.componentProps || {}))
  }
}

onMounted(() => {
  renderReactComponent()
})

watch(() => [props.component, props.componentProps], () => {
  renderReactComponent()
}, { deep: true })

onUnmounted(() => {
  if (root) {
    root.unmount()
    root = null
  }
})
</script>

<style scoped>
.react-wrapper {
  width: 100%;
  height: 100%;
  min-height: calc(100vh - 64px);
}
</style>
