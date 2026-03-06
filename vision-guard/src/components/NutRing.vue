<template>
  <div class="nut-cell">
    <div class="nut-ring" :style="{ width: size + 'px', height: size + 'px' }">
      <svg :width="size" :height="size" style="transform: rotate(-90deg)">
        <circle :cx="c" :cy="c" :r="r" fill="none" stroke="var(--border)" :stroke-width="3" />
        <circle :cx="c" :cy="c" :r="r" fill="none" :stroke="color" :stroke-width="3"
          :stroke-dasharray="`${dash} ${circ - dash}`" stroke-linecap="round" />
      </svg>
      <div class="nut-ring__val">{{ pct }}%</div>
    </div>
    <div class="nut-label">{{ icon }}<br />{{ name }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  pct: number
  color: string
  icon: string
  name: string
  size?: number
}>(), { size: 38 })

const r = computed(() => (props.size - 4) / 2)
const c = computed(() => props.size / 2)
const circ = computed(() => 2 * Math.PI * r.value)
const dash = computed(() => Math.min(props.pct / 100, 1) * circ.value)
</script>

<style scoped>
.nut-cell { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.nut-ring { position: relative; }
.nut-ring__val {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 9px; font-weight: 700; color: var(--ink);
}
.nut-label { font-size: 9px; color: var(--sub); text-align: center; line-height: 1.2; }
</style>
