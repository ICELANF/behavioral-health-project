<!--
  AI 内容审核标识组件
  铁律: AI生成内容必须标注审核状态

  Props:
    reviewStatus - 'approved' | 'pending' | 'auto' | undefined
      approved: 教练已审核 (绿色)
      pending:  等待审核 (黄色, 可选隐藏内容)
      auto:     AI辅助生成 (蓝色, 事实性数据)
      undefined/missing: 默认为 auto (向下兼容)
    compact - 紧凑模式 (仅图标+短文字)
-->
<template>
  <div class="ai-badge" :class="badgeClass">
    <van-icon :name="iconName" :size="compact ? '12' : '14'" />
    <span class="ai-badge-text">{{ badgeText }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  reviewStatus?: 'approved' | 'pending' | 'auto'
  compact?: boolean
}>(), {
  reviewStatus: 'auto',
  compact: false,
})

const status = computed(() => props.reviewStatus || 'auto')

const badgeClass = computed(() => `ai-badge--${status.value}`)

const iconName = computed(() => {
  switch (status.value) {
    case 'approved': return 'certificate'
    case 'pending': return 'clock-o'
    default: return 'info-o'
  }
})

const badgeText = computed(() => {
  if (props.compact) {
    switch (status.value) {
      case 'approved': return '已审核'
      case 'pending': return '待审核'
      default: return 'AI辅助'
    }
  }
  switch (status.value) {
    case 'approved': return '教练已审核'
    case 'pending': return '等待教练审核'
    default: return 'AI辅助生成，仅供参考'
  }
})
</script>

<style scoped>
.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  line-height: 1.4;
}

.ai-badge--approved {
  background: rgba(82, 196, 26, 0.1);
  color: #52c41a;
  border: 1px solid rgba(82, 196, 26, 0.2);
}

.ai-badge--pending {
  background: rgba(250, 173, 20, 0.1);
  color: #faad14;
  border: 1px solid rgba(250, 173, 20, 0.2);
}

.ai-badge--auto {
  background: rgba(24, 144, 255, 0.08);
  color: #1890ff;
  border: 1px solid rgba(24, 144, 255, 0.15);
}
</style>
