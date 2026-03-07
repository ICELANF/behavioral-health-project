<template>
  <svg width="200" height="200" viewBox="0 0 200 200">
    <path v-for="(g, i) in gridPaths" :key="'g'+i" :d="g" fill="none" stroke="rgba(0,0,0,.08)" stroke-width="1" />
    <line v-for="d in dims" :key="'l'+d.k" :x1="cx" :y1="cy" :x2="toXY(d.angle, R)[0]" :y2="toXY(d.angle, R)[1]"
      stroke="rgba(0,0,0,.08)" stroke-width="1" />
    <path :d="dataPath" :fill="color + '33'" :stroke="color" stroke-width="2" />
    <circle v-for="(p, i) in dataPoints" :key="'p'+i" :cx="p[0]" :cy="p[1]" r="4" :fill="color" />
    <text v-for="d in dims" :key="'t'+d.k" :x="toXY(d.angle, R + 14)[0]" :y="toXY(d.angle, R + 14)[1]"
      text-anchor="middle" dominant-baseline="middle" font-size="9" fill="rgba(0,0,0,.45)">
      {{ d.label }}
    </text>
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Scores } from '@/data/scoring'

const props = defineProps<{ scores: Scores; color: string }>()

const cx = 100, cy = 100, R = 72
const dims = [
  { k: 'metabolism' as const, label: '代谢负荷', angle: -90 },
  { k: 'stress' as const,     label: '压力激活', angle: -18 },
  { k: 'sleep' as const,      label: '睡眠修复', angle: 54 },
  { k: 'stability' as const,  label: '行为稳定', angle: 126 },
  { k: 'control' as const,    label: '心理掌控', angle: 198 },
]

function toXY(angle: number, r: number): [number, number] {
  return [cx + r * Math.cos(angle * Math.PI / 180), cy + r * Math.sin(angle * Math.PI / 180)]
}

const gridPaths = computed(() =>
  [0.25, 0.5, 0.75, 1].map(f =>
    dims.map((d, i) => {
      const [x, y] = toXY(d.angle, R * f)
      return i === 0 ? `M${x},${y}` : `L${x},${y}`
    }).join(' ') + 'Z'
  )
)

const dataPoints = computed(() =>
  dims.map(d => toXY(d.angle, R * (props.scores[d.k] / 100)))
)

const dataPath = computed(() =>
  dataPoints.value.map((p, i) => (i === 0 ? 'M' : 'L') + p[0] + ',' + p[1]).join(' ') + 'Z'
)
</script>
