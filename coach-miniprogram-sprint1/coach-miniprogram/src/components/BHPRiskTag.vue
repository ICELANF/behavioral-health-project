<template>
  <view class="bhp-risk-badge" :class="`bhp-risk-badge--${level}`">
    <text class="risk-icon" v-if="showIcon">{{ RISK_ICON[level] }}</text>
    <text>{{ RISK_LABEL[level] }}</text>
  </view>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  level: 'critical' | 'high' | 'moderate' | 'low' | 'none'
  showIcon?: boolean
}>(), {
  level: 'none',
  showIcon: true
})

const RISK_LABEL = {
  critical: '危急',
  high:     '高风险',
  moderate: '中等',
  low:      '低风险',
  none:     '暂无数据'
}

const RISK_ICON = {
  critical: '🔴',
  high:     '🟠',
  moderate: '🟡',
  low:      '🟢',
  none:     '⚪'
}
</script>

<style scoped>
.risk-icon { margin-right: 4rpx; font-size: 18rpx; }
</style>
