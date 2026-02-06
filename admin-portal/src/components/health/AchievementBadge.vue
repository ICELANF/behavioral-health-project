<template>
  <div
    class="achievement-badge"
    :class="[sizeClass, { unlocked, clickable }]"
    @click="handleClick"
  >
    <!-- 徽章图标 -->
    <div class="badge-icon-wrapper">
      <div class="badge-icon">{{ icon }}</div>
      <div v-if="!unlocked" class="badge-lock">🔒</div>
      <div v-if="unlocked && showGlow" class="badge-glow"></div>
    </div>

    <!-- 徽章信息 -->
    <div v-if="showInfo" class="badge-info">
      <div class="badge-name">{{ name }}</div>
      <div v-if="description" class="badge-desc">{{ description }}</div>
      <div v-if="!unlocked && progress !== undefined" class="badge-progress">
        <a-progress
          :percent="progress"
          :show-info="false"
          :stroke-color="'#10b981'"
          size="small"
        />
        <div class="progress-text">{{ progress }}%</div>
      </div>
      <div v-if="unlocked && unlockedDate" class="badge-date">
        {{ formatDate(unlockedDate) }}
      </div>
    </div>

    <!-- 紧凑模式 - 仅显示名称 -->
    <div v-if="compact && !showInfo" class="badge-compact-name">
      {{ name }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  icon: string
  name: string
  description?: string
  unlocked: boolean
  unlockedDate?: string
  progress?: number
  size?: 'small' | 'medium' | 'large'
  showInfo?: boolean
  showGlow?: boolean
  compact?: boolean
  clickable?: boolean
}

interface Emits {
  (e: 'click'): void
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  showInfo: true,
  showGlow: true,
  compact: false,
  clickable: true
})

const emit = defineEmits<Emits>()

const sizeClass = computed(() => `size-${props.size}`)

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${month}月${day}日解锁`
}
</script>

<style scoped>
.achievement-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #fff;
  border-radius: 16px;
  border: 2px solid #e5e7eb;
  transition: all 0.3s;
}

.achievement-badge.clickable {
  cursor: pointer;
}

.achievement-badge.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.achievement-badge.unlocked {
  border-color: #10b981;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.achievement-badge:not(.unlocked) {
  opacity: 0.5;
}

/* 尺寸变化 */
.achievement-badge.size-small {
  padding: 12px;
}

.achievement-badge.size-large {
  padding: 20px;
}

/* 徽章图标 */
.badge-icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.badge-icon {
  font-size: 48px;
  transition: transform 0.3s;
}

.size-small .badge-icon {
  font-size: 36px;
}

.size-large .badge-icon {
  font-size: 64px;
}

.achievement-badge.unlocked:hover .badge-icon {
  transform: scale(1.1) rotate(5deg);
}

.badge-lock {
  position: absolute;
  top: -4px;
  right: -4px;
  font-size: 18px;
  background: #fff;
  border-radius: 50%;
  padding: 2px;
}

.size-small .badge-lock {
  font-size: 14px;
}

.size-large .badge-lock {
  font-size: 22px;
}

/* 解锁光效 */
.badge-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0.5;
  }
  50% {
    transform: translate(-50%, -50%) scale(1.3);
    opacity: 0.2;
  }
}

/* 徽章信息 */
.badge-info {
  text-align: center;
  width: 100%;
}

.badge-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.size-small .badge-name {
  font-size: 13px;
}

.size-large .badge-name {
  font-size: 16px;
}

.badge-desc {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.badge-progress {
  margin-top: 8px;
}

.progress-text {
  font-size: 11px;
  color: #6b7280;
  margin-top: 4px;
}

.badge-date {
  font-size: 11px;
  color: #10b981;
  font-weight: 500;
  margin-top: 4px;
}

/* 紧凑模式 */
.achievement-badge.compact {
  flex-direction: row;
  padding: 8px 12px;
}

.badge-compact-name {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
}
</style>
