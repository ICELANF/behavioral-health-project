<template>
  <!-- 六级角色徽章 -->
  <view
    class="level-badge"
    :class="[`level-badge--${size}`, { 'level-badge--outline': outline }]"
    :style="badgeStyle"
  >
    <text class="level-badge__icon" v-if="showIcon">{{ icon }}</text>
    <text class="level-badge__text">{{ label }}</text>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  role: string        // 角色标识
  size?: 'xs' | 'sm' | 'md' | 'lg'
  outline?: boolean   // 描边模式（默认填充）
  showIcon?: boolean
}>(), {
  size: 'sm',
  outline: false,
  showIcon: true
})

// ─── 六级配色（与 Design Tokens --level-* 对齐）──────────────
const ROLE_CONFIG: Record<string, { color: string; bg: string; label: string; icon: string }> = {
  observer:   { color: '#595959', bg: '#f5f5f5', label: 'L0 观察员', icon: '👁' },
  grower:     { color: '#389e0d', bg: '#f6ffed', label: 'L1 成长者', icon: '🌱' },
  sharer:     { color: '#096dd9', bg: '#e6f7ff', label: 'L2 分享者', icon: '🤝' },
  coach:      { color: '#531dab', bg: '#f9f0ff', label: 'L3 教练',   icon: '🎯' },
  promoter:   { color: '#c41d7f', bg: '#fff0f6', label: 'L4 促进师', icon: '⭐' },
  supervisor: { color: '#c41d7f', bg: '#fff0f6', label: 'L4 督导师', icon: '⭐' },
  master:     { color: '#ad6800', bg: '#fffbe6', label: 'L5 大师',   icon: '👑' },
  admin:      { color: '#a8071a', bg: '#fff1f0', label: '管理员',    icon: '🔑' }
}

const config = computed(() => ROLE_CONFIG[props.role] || ROLE_CONFIG['observer'])
const label  = computed(() => config.value.label)
const icon   = computed(() => config.value.icon)

const badgeStyle = computed(() => {
  if (props.outline) {
    return {
      color:           config.value.color,
      backgroundColor: 'transparent',
      border:          `1.5px solid ${config.value.color}`
    }
  }
  return {
    color:           config.value.color,
    backgroundColor: config.value.bg,
    border:          `1px solid ${config.value.bg}`
  }
})
</script>

<style scoped>
.level-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: 9999px;
  font-weight: 600;
  white-space: nowrap;
}

/* 尺寸变体 */
.level-badge--xs {
  padding: 1px 6px;
  font-size: 20rpx;
}
.level-badge--xs .level-badge__icon { font-size: 18rpx; }

.level-badge--sm {
  padding: 2px 10px;
  font-size: 22rpx;
}
.level-badge--sm .level-badge__icon { font-size: 20rpx; }

.level-badge--md {
  padding: 4px 12px;
  font-size: 26rpx;
}
.level-badge--md .level-badge__icon { font-size: 24rpx; }

.level-badge--lg {
  padding: 6px 16px;
  font-size: 30rpx;
}
.level-badge--lg .level-badge__icon { font-size: 28rpx; }
</style>
