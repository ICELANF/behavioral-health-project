<!--
  BigFiveRadar.vue — 五因子人格雷达图
  ======================================
  Canvas 绘制, 无外部依赖
  
  Props:
    profile: BigFiveProfile  — 五维分数 (0-100)
    size:    number           — 画布尺寸 (默认 240)
    animate: boolean          — 是否动画 (默认 true)
-->

<template>
  <div class="bigfive-radar" :style="{ width: size + 'px', height: size + 'px' }">
    <canvas
      ref="canvasRef"
      :width="size * 2"
      :height="size * 2"
      :style="{ width: size + 'px', height: size + 'px' }"
    />
    <div class="radar-legend">
      <span
        v-for="item in legendItems"
        :key="item.key"
        class="legend-item"
        :class="{ dominant: item.dominant }"
      >
        <span class="legend-dot" :style="{ background: item.color }" />
        {{ item.label }} {{ item.value }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import type { BigFiveProfile } from '../types/rx'

interface Props {
  profile: BigFiveProfile
  size?: number
  animate?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 240,
  animate: true,
})

const canvasRef = ref<HTMLCanvasElement | null>(null)

const LABELS = [
  { key: 'O', label: '开放性', color: '#1890ff' },
  { key: 'C', label: '尽责性', color: '#52c41a' },
  { key: 'E', label: '外向性', color: '#faad14' },
  { key: 'A', label: '宜人性', color: '#722ed1' },
  { key: 'N', label: '神经质', color: '#f5222d' },
]

const legendItems = computed(() => {
  const dominant = getDominant()
  return LABELS.map((l) => ({
    ...l,
    value: Math.round(props.profile[l.key as keyof BigFiveProfile]),
    dominant: l.key === dominant,
  }))
})

function getDominant(): string {
  const p = props.profile
  const entries: [string, number][] = [
    ['O', p.O], ['C', p.C], ['E', p.E], ['A', p.A], ['N', p.N],
  ]
  return entries.reduce((a, b) => (b[1] > a[1] ? b : a))[0]
}

function draw(progress = 1) {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const w = canvas.width
  const h = canvas.height
  const cx = w / 2
  const cy = h / 2
  const radius = Math.min(cx, cy) * 0.7

  ctx.clearRect(0, 0, w, h)
  ctx.save()

  const sides = 5
  const angleStep = (Math.PI * 2) / sides
  const startAngle = -Math.PI / 2

  // 绘制背景网格 (5层)
  for (let level = 1; level <= 5; level++) {
    const r = (radius * level) / 5
    ctx.beginPath()
    for (let i = 0; i <= sides; i++) {
      const angle = startAngle + i * angleStep
      const x = cx + r * Math.cos(angle)
      const y = cy + r * Math.sin(angle)
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }
    ctx.closePath()
    ctx.strokeStyle = level === 5 ? 'rgba(0,0,0,0.15)' : 'rgba(0,0,0,0.06)'
    ctx.lineWidth = level === 5 ? 2 : 1
    ctx.stroke()
  }

  // 绘制轴线
  for (let i = 0; i < sides; i++) {
    const angle = startAngle + i * angleStep
    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.lineTo(cx + radius * Math.cos(angle), cy + radius * Math.sin(angle))
    ctx.strokeStyle = 'rgba(0,0,0,0.08)'
    ctx.lineWidth = 1
    ctx.stroke()
  }

  // 绘制数据区域
  const values = [
    props.profile.O,
    props.profile.C,
    props.profile.E,
    props.profile.A,
    props.profile.N,
  ].map((v) => (v / 100) * progress)

  ctx.beginPath()
  values.forEach((v, i) => {
    const angle = startAngle + i * angleStep
    const r = radius * v
    const x = cx + r * Math.cos(angle)
    const y = cy + r * Math.sin(angle)
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  })
  ctx.closePath()

  // 渐变填充
  const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius)
  gradient.addColorStop(0, 'rgba(24, 144, 255, 0.15)')
  gradient.addColorStop(1, 'rgba(24, 144, 255, 0.05)')
  ctx.fillStyle = gradient
  ctx.fill()

  ctx.strokeStyle = 'rgba(24, 144, 255, 0.7)'
  ctx.lineWidth = 2.5
  ctx.stroke()

  // 绘制数据点
  values.forEach((v, i) => {
    const angle = startAngle + i * angleStep
    const r = radius * v
    const x = cx + r * Math.cos(angle)
    const y = cy + r * Math.sin(angle)

    ctx.beginPath()
    ctx.arc(x, y, 5, 0, Math.PI * 2)
    ctx.fillStyle = LABELS[i].color
    ctx.fill()
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = 2
    ctx.stroke()
  })

  // 绘制标签
  ctx.font = `${Math.round(w * 0.045)}px -apple-system, BlinkMacSystemFont, sans-serif`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillStyle = '#333'

  LABELS.forEach((l, i) => {
    const angle = startAngle + i * angleStep
    const labelR = radius * 1.18
    const x = cx + labelR * Math.cos(angle)
    const y = cy + labelR * Math.sin(angle)
    ctx.fillText(l.label, x, y)
  })

  ctx.restore()
}

function animateDraw() {
  if (!props.animate) {
    draw(1)
    return
  }

  let start: number | null = null
  const duration = 600

  function frame(ts: number) {
    if (!start) start = ts
    const elapsed = ts - start
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3) // easeOutCubic
    draw(eased)
    if (progress < 1) requestAnimationFrame(frame)
  }

  requestAnimationFrame(frame)
}

watch(() => props.profile, () => animateDraw(), { deep: true })

onMounted(() => nextTick(() => animateDraw()))
</script>

<style scoped>
.bigfive-radar {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
}

canvas {
  display: block;
}

.radar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  justify-content: center;
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  transition: opacity 0.2s;
}

.legend-item.dominant {
  font-weight: 600;
  color: #333;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
</style>
