<template>
  <div class="score-ring" :style="{ width: size + 'px', height: size + 'px' }">
    <svg :width="size" :height="size" style="transform: rotate(-90deg)">
      <circle :cx="c" :cy="c" :r="r" fill="none" stroke="rgba(255,255,255,0.2)" :stroke-width="strokeW" />
      <circle :cx="c" :cy="c" :r="r" fill="none" :stroke="color" :stroke-width="strokeW"
        :stroke-dasharray="`${dash} ${circ - dash}`" stroke-linecap="round" />
    </svg>
    <div class="score-ring__val">{{ pct }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  pct: number
  size?: number
  strokeW?: number
  color?: string
}>(), { size: 52, strokeW: 5, color: '#F9C74F' })

const r = computed(() => (props.size - props.strokeW * 2) / 2)
const c = computed(() => props.size / 2)
const circ = computed(() => 2 * Math.PI * r.value)
const dash = computed(() => circ.value * Math.min(props.pct, 100) / 100)
</script>

<style scoped>
.score-ring { position: relative; }
.score-ring__val {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  font-weight: 900; font-size: 15px; color: white;
}
</style>
