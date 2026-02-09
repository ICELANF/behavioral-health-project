<template>
  <span ref="el">{{ display }}</span>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const props = defineProps<{ target: number; suffix?: string }>()
const el = ref<HTMLElement | null>(null)
const display = ref('0' + (props.suffix || ''))

onMounted(() => {
  if (!el.value) return
  const observer = new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting) {
      observer.disconnect()
      const dur = 2000, t0 = performance.now()
      function step(now: number) {
        const p = Math.min((now - t0) / dur, 1)
        display.value = Math.round(props.target * (1 - Math.pow(1 - p, 3))).toLocaleString() + (props.suffix || '')
        if (p < 1) requestAnimationFrame(step)
      }
      requestAnimationFrame(step)
    }
  }, { threshold: 0.3 })
  observer.observe(el.value)
})
</script>
