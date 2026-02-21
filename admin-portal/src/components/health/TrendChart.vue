<template>
  <div class="trend-chart" :class="{ compact }">
    <!-- 图表标题 -->
    <div v-if="title" class="chart-header">
      <div class="chart-title">
        <span v-if="icon" class="title-icon">{{ icon }}</span>
        {{ title }}
      </div>
      <div v-if="subtitle" class="chart-subtitle">{{ subtitle }}</div>
    </div>

    <!-- 统计信息 -->
    <div v-if="showStats" class="chart-stats">
      <div class="stat-item">
        <span class="stat-label">平均</span>
        <span class="stat-value">{{ average }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">最高</span>
        <span class="stat-value">{{ max }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">最低</span>
        <span class="stat-value">{{ min }}</span>
      </div>
    </div>

    <!-- 折线图 -->
    <div v-if="type === 'line'" class="chart-container">
      <svg :viewBox="`0 0 ${width} ${height}`" class="line-chart">
        <!-- 背景网格 -->
        <g v-if="showGrid" class="grid">
          <line
            v-for="i in 5"
            :key="`h-${i}`"
            :x1="0"
            :y1="(i - 1) * (height / 4)"
            :x2="width"
            :y2="(i - 1) * (height / 4)"
            stroke="#e5e7eb"
            stroke-width="1"
          />
        </g>

        <!-- 面积填充 -->
        <path
          v-if="showArea"
          :d="areaPath"
          :fill="`url(#gradient-${chartId})`"
          opacity="0.2"
        />

        <!-- 渐变定义 -->
        <defs>
          <linearGradient :id="`gradient-${chartId}`" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" :stop-color="lineColor" stop-opacity="0.8" />
            <stop offset="100%" :stop-color="lineColor" stop-opacity="0" />
          </linearGradient>
        </defs>

        <!-- 折线 -->
        <polyline
          :points="linePoints"
          fill="none"
          :stroke="lineColor"
          :stroke-width="strokeWidth"
          stroke-linecap="round"
          stroke-linejoin="round"
        />

        <!-- 数据点 -->
        <g v-if="showDots">
          <circle
            v-for="(point, i) in pointsArray"
            :key="i"
            :cx="point.x"
            :cy="point.y"
            :r="dotRadius"
            :fill="lineColor"
            class="chart-dot"
            @mouseenter="handleDotHover(i)"
            @mouseleave="handleDotLeave"
          />
        </g>
      </svg>

      <!-- X轴标签 -->
      <div v-if="showLabels" class="x-labels">
        <div v-for="(label, i) in labels" :key="i" class="x-label">
          {{ label }}
        </div>
      </div>
    </div>

    <!-- 柱状图 -->
    <div v-if="type === 'bar'" class="chart-container">
      <svg :viewBox="`0 0 ${width} ${height}`" class="bar-chart">
        <!-- 柱子 -->
        <g>
          <rect
            v-for="(bar, i) in barsArray"
            :key="i"
            :x="bar.x"
            :y="bar.y"
            :width="bar.width"
            :height="bar.height"
            :fill="getBarColor(data[i])"
            :rx="barRadius"
            class="chart-bar"
            @mouseenter="handleBarHover(i)"
            @mouseleave="handleBarLeave"
          />
        </g>

        <!-- 数值标签 -->
        <g v-if="showValues">
          <text
            v-for="(bar, i) in barsArray"
            :key="`val-${i}`"
            :x="bar.x + bar.width / 2"
            :y="bar.y - 5"
            text-anchor="middle"
            font-size="12"
            fill="#6b7280"
            font-weight="500"
          >
            {{ data[i] }}
          </text>
        </g>
      </svg>

      <!-- X轴标签 -->
      <div v-if="showLabels" class="x-labels">
        <div v-for="(label, i) in labels" :key="i" class="x-label">
          {{ label }}
        </div>
      </div>
    </div>

    <!-- 趋势说明 -->
    <div v-if="trendText" class="chart-trend">
      <span class="trend-icon" :class="trendClass">{{ trendIcon }}</span>
      <span class="trend-text">{{ trendText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  type: 'line' | 'bar'
  data: number[]
  labels?: string[]
  title?: string
  subtitle?: string
  icon?: string
  lineColor?: string
  barColor?: string
  width?: number
  height?: number
  showGrid?: boolean
  showArea?: boolean
  showDots?: boolean
  showLabels?: boolean
  showValues?: boolean
  showStats?: boolean
  strokeWidth?: number
  dotRadius?: number
  barRadius?: number
  trendText?: string
  trendDirection?: 'up' | 'down' | 'stable'
  compact?: boolean
}

interface Emits {
  (e: 'pointClick', index: number): void
}

const props = withDefaults(defineProps<Props>(), {
  labels: () => [],
  lineColor: '#10b981',
  barColor: '#10b981',
  width: 300,
  height: 100,
  showGrid: true,
  showArea: true,
  showDots: true,
  showLabels: true,
  showValues: false,
  showStats: true,
  strokeWidth: 3,
  dotRadius: 4,
  barRadius: 4,
  trendDirection: 'stable',
  compact: false
})

const emit = defineEmits<Emits>()

// 生成唯一ID用于渐变
const chartId = ref(`chart-${Math.random().toString(36).substr(2, 9)}`)

// 统计数据
const average = computed(() => {
  if (props.data.length === 0) return '--'
  const sum = props.data.reduce((a, b) => a + b, 0)
  return (sum / props.data.length).toFixed(1)
})

const max = computed(() => {
  if (props.data.length === 0) return '--'
  return Math.max(...props.data).toFixed(1)
})

const min = computed(() => {
  if (props.data.length === 0) return '--'
  return Math.min(...props.data).toFixed(1)
})

// 折线图路径计算
const pointsArray = computed(() => {
  if (props.data.length === 0) return []

  const maxVal = Math.max(...props.data)
  const minVal = Math.min(...props.data)
  const range = maxVal - minVal || 1

  const xDivisor = props.data.length > 1 ? props.data.length - 1 : 1
  return props.data.map((value, index) => {
    const x = (index / xDivisor) * props.width
    const y = props.height - ((value - minVal) / range) * (props.height - 20) - 10
    return { x, y }
  })
})

const linePoints = computed(() => {
  return pointsArray.value.map(p => `${p.x},${p.y}`).join(' ')
})

const areaPath = computed(() => {
  if (pointsArray.value.length === 0) return ''

  const points = pointsArray.value
  let path = `M 0,${props.height} L ${points[0].x},${points[0].y}`

  for (let i = 1; i < points.length; i++) {
    path += ` L ${points[i].x},${points[i].y}`
  }

  path += ` L ${props.width},${props.height} Z`
  return path
})

// 柱状图计算
const barsArray = computed(() => {
  if (props.data.length === 0) return []

  const maxVal = Math.max(...props.data)
  const barWidth = (props.width / props.data.length) * 0.7
  const gap = (props.width / props.data.length) * 0.3

  return props.data.map((value, index) => {
    const height = (value / maxVal) * (props.height - 20)
    const x = index * (props.width / props.data.length) + gap / 2
    const y = props.height - height - 10

    return { x, y, width: barWidth, height }
  })
})

const getBarColor = (value: number) => {
  // 可以根据值的大小返回不同颜色
  const maxVal = Math.max(...props.data)
  const ratio = value / maxVal

  if (ratio >= 0.8) return props.barColor
  if (ratio >= 0.5) return '#fbbf24'
  return '#ef4444'
}

// 趋势图标和样式
const trendIcon = computed(() => {
  if (props.trendDirection === 'up') return '↗'
  if (props.trendDirection === 'down') return '↘'
  return '→'
})

const trendClass = computed(() => {
  return `trend-${props.trendDirection}`
})

// 交互
const handleDotHover = (index: number) => {
  // 可以显示tooltip
}

const handleDotLeave = () => {
  // 隐藏tooltip
}

const handleBarHover = (index: number) => {
  // 可以显示tooltip
}

const handleBarLeave = () => {
  // 隐藏tooltip
}
</script>

<style scoped>
.trend-chart {
  width: 100%;
}

.trend-chart.compact {
  font-size: 13px;
}

/* 标题 */
.chart-header {
  margin-bottom: 12px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 6px;
}

.trend-chart.compact .chart-title {
  font-size: 15px;
}

.title-icon {
  font-size: 18px;
}

.chart-subtitle {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

/* 统计信息 */
.chart-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 11px;
  color: #9ca3af;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

/* 图表容器 */
.chart-container {
  position: relative;
}

.line-chart,
.bar-chart {
  width: 100%;
  height: auto;
  display: block;
}

.chart-dot {
  cursor: pointer;
  transition: r 0.2s;
}

.chart-dot:hover {
  r: 6;
}

.chart-bar {
  cursor: pointer;
  transition: opacity 0.2s;
}

.chart-bar:hover {
  opacity: 0.8;
}

/* X轴标签 */
.x-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  padding: 0 4px;
}

.x-label {
  font-size: 11px;
  color: #6b7280;
  text-align: center;
  flex: 1;
}

/* 趋势说明 */
.chart-trend {
  margin-top: 12px;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.trend-icon {
  font-size: 16px;
  font-weight: 700;
}

.trend-icon.trend-up {
  color: #ef4444;
}

.trend-icon.trend-down {
  color: #10b981;
}

.trend-icon.trend-stable {
  color: #6b7280;
}

.trend-text {
  color: #6b7280;
  font-weight: 500;
}
</style>
