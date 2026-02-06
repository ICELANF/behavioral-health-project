<template>
  <div class="health-score-circle">
    <a-progress
      type="circle"
      :percent="score"
      :size="size"
      :stroke-width="strokeWidth"
      :stroke-color="strokeColor"
    >
      <template #format="percent">
        <div class="score-content">
          <div class="score-value" :style="{ fontSize: valueFontSize }">{{ percent }}</div>
          <div class="score-unit" :style="{ fontSize: unitFontSize }">{{ unit }}</div>
          <div v-if="label" class="score-label" :style="{ fontSize: labelFontSize }">
            {{ label }}
          </div>
        </div>
      </template>
    </a-progress>

    <!-- 底部信息 -->
    <div v-if="showInfo" class="score-info">
      <div v-if="statusText" class="score-status" :class="statusClass">
        {{ statusText }}
      </div>
      <div v-if="subtitle" class="score-subtitle">
        {{ subtitle }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  score: number // 0-100
  size?: number
  strokeWidth?: number
  unit?: string
  label?: string
  statusText?: string
  subtitle?: string
  showInfo?: boolean
  colorTheme?: 'green' | 'blue' | 'orange' | 'red' | 'auto'
}

const props = withDefaults(defineProps<Props>(), {
  size: 120,
  strokeWidth: 10,
  unit: '分',
  label: '',
  statusText: '',
  subtitle: '',
  showInfo: true,
  colorTheme: 'auto'
})

// 根据评分自动选择颜色
const strokeColor = computed(() => {
  if (props.colorTheme !== 'auto') {
    const colorMap = {
      green: { '0%': '#10b981', '100%': '#34d399' },
      blue: { '0%': '#3b82f6', '100%': '#60a5fa' },
      orange: { '0%': '#f59e0b', '100%': '#fbbf24' },
      red: { '0%': '#ef4444', '100%': '#f87171' }
    }
    return colorMap[props.colorTheme]
  }

  // 自动根据评分选择颜色
  if (props.score >= 90) return { '0%': '#10b981', '100%': '#34d399' } // 绿色
  if (props.score >= 70) return { '0%': '#3b82f6', '100%': '#60a5fa' } // 蓝色
  if (props.score >= 50) return { '0%': '#f59e0b', '100%': '#fbbf24' } // 橙色
  return { '0%': '#ef4444', '100%': '#f87171' } // 红色
})

const statusClass = computed(() => {
  if (props.score >= 90) return 'status-excellent'
  if (props.score >= 70) return 'status-good'
  if (props.score >= 50) return 'status-fair'
  return 'status-poor'
})

// 响应式字体大小
const valueFontSize = computed(() => {
  if (props.size >= 140) return '32px'
  if (props.size >= 100) return '28px'
  if (props.size >= 80) return '24px'
  return '20px'
})

const unitFontSize = computed(() => {
  if (props.size >= 140) return '14px'
  if (props.size >= 100) return '12px'
  return '10px'
})

const labelFontSize = computed(() => {
  if (props.size >= 140) return '14px'
  if (props.size >= 100) return '13px'
  return '11px'
})
</script>

<style scoped>
.health-score-circle {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.score-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.score-value {
  font-weight: 700;
  line-height: 1;
  margin-bottom: 2px;
}

.score-unit {
  color: #6b7280;
  font-weight: 500;
  line-height: 1;
}

.score-label {
  color: #9ca3af;
  margin-top: 4px;
  line-height: 1;
}

.score-info {
  text-align: center;
  width: 100%;
}

.score-status {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
  padding: 4px 12px;
  border-radius: 12px;
  display: inline-block;
}

.score-status.status-excellent {
  background: #dcfce7;
  color: #16a34a;
}

.score-status.status-good {
  background: #dbeafe;
  color: #2563eb;
}

.score-status.status-fair {
  background: #fef3c7;
  color: #d97706;
}

.score-status.status-poor {
  background: #fee2e2;
  color: #dc2626;
}

.score-subtitle {
  font-size: 13px;
  color: #6b7280;
}
</style>
