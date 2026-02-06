<template>
  <div
    class="health-metric-card"
    :class="[`theme-${theme}`, { clickable, compact }]"
    @click="handleClick"
  >
    <!-- 顶部彩色条 -->
    <div class="card-stripe" :style="{ background: stripeColor }"></div>

    <!-- 图标 -->
    <div class="metric-icon" :style="{ fontSize: iconSize }">{{ icon }}</div>

    <!-- 数据区 -->
    <div class="metric-data">
      <div class="metric-value" :style="{ fontSize: valueSize }">
        {{ value || '--' }}
      </div>
      <div class="metric-label">{{ label }}</div>
    </div>

    <!-- 状态或趋势 -->
    <div v-if="status || trend" class="metric-footer">
      <div v-if="status" class="metric-status" :class="`status-${status}`">
        {{ statusText }}
      </div>
      <div v-if="trend" class="metric-trend" :class="trendClass">
        {{ trend }}
      </div>
    </div>

    <!-- 进度条（可选） -->
    <div v-if="showProgress && progress !== undefined" class="metric-progress">
      <a-progress
        :percent="progress"
        :show-info="false"
        :stroke-color="stripeColor"
        size="small"
      />
      <div class="progress-text">{{ progressText }}</div>
    </div>

    <!-- 徽章（可选） -->
    <div v-if="badge" class="metric-badge">{{ badge }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  icon: string
  label: string
  value?: string | number
  status?: 'good' | 'normal' | 'warning' | 'danger'
  statusText?: string
  trend?: string
  badge?: string
  progress?: number
  progressText?: string
  showProgress?: boolean
  theme?: 'glucose' | 'weight' | 'exercise' | 'medication' | 'bp' | 'mood'
  clickable?: boolean
  compact?: boolean
}

interface Emits {
  (e: 'click'): void
}

const props = withDefaults(defineProps<Props>(), {
  theme: 'glucose',
  clickable: true,
  compact: false,
  showProgress: false
})

const emit = defineEmits<Emits>()

// 主题颜色映射
const themeColors = {
  glucose: '#ef4444',
  weight: '#8b5cf6',
  exercise: '#10b981',
  medication: '#f59e0b',
  bp: '#ec4899',
  mood: '#3b82f6'
}

const stripeColor = computed(() => themeColors[props.theme])

// 响应式大小
const iconSize = computed(() => props.compact ? '28px' : '32px')
const valueSize = computed(() => props.compact ? '20px' : '24px')

const trendClass = computed(() => {
  if (!props.trend) return ''
  if (props.trend.includes('↑') || props.trend.includes('增')) return 'trend-up'
  if (props.trend.includes('↓') || props.trend.includes('减')) return 'trend-down'
  return 'trend-stable'
})

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<style scoped>
.health-metric-card {
  background: #f9fafb;
  padding: 16px;
  border-radius: 16px;
  position: relative;
  overflow: hidden;
  transition: all 0.2s;
}

.health-metric-card.compact {
  padding: 12px;
  border-radius: 12px;
}

.health-metric-card.clickable {
  cursor: pointer;
}

.health-metric-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* 顶部彩色条 */
.card-stripe {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
}

/* 图标 */
.metric-icon {
  margin-bottom: 8px;
}

.health-metric-card.compact .metric-icon {
  margin-bottom: 6px;
}

/* 数据区 */
.metric-data {
  margin-bottom: 8px;
}

.metric-value {
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
  margin-bottom: 2px;
}

.metric-label {
  font-size: 13px;
  color: #6b7280;
}

.health-metric-card.compact .metric-label {
  font-size: 12px;
}

/* 状态/趋势 */
.metric-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.metric-status {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 10px;
  display: inline-block;
  font-weight: 500;
}

.metric-status.status-good,
.metric-status.status-normal {
  background: #dcfce7;
  color: #16a34a;
}

.metric-status.status-warning {
  background: #fef3c7;
  color: #d97706;
}

.metric-status.status-danger {
  background: #fee2e2;
  color: #dc2626;
}

.metric-trend {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
}

.metric-trend.trend-up {
  color: #dc2626;
}

.metric-trend.trend-down {
  color: #16a34a;
}

.metric-trend.trend-stable {
  color: #6b7280;
}

/* 进度条 */
.metric-progress {
  margin-top: 8px;
}

.progress-text {
  font-size: 11px;
  color: #6b7280;
  margin-top: 4px;
  text-align: right;
}

/* 徽章 */
.metric-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  background: rgba(255, 255, 255, 0.8);
  padding: 4px 8px;
  border-radius: 8px;
}
</style>
