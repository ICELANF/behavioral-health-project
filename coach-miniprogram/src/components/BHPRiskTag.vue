<template>
  <view
    class="bhp-risk-tag"
    :class="`bhp-risk-tag--${level}`"
    v-if="level && level !== 'normal'"
  >
    <text class="bhp-risk-tag__dot"></text>
    <text class="bhp-risk-tag__text">{{ RISK_LABEL[level] || level }}</text>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  level?: string   // critical | high | moderate | low | normal
}>()

const RISK_LABEL: Record<string, string> = {
  critical: '危急',
  high:     '高风险',
  moderate: '中风险',
  low:      '低风险',
  normal:   '正常',
}
</script>

<style scoped>
.bhp-risk-tag {
  display: inline-flex; align-items: center; gap: 6rpx;
  font-size: 20rpx; font-weight: 600;
  padding: 4rpx 12rpx; border-radius: var(--radius-full);
}
.bhp-risk-tag__dot {
  width: 10rpx; height: 10rpx; border-radius: 50%;
  background: currentColor; flex-shrink: 0;
}
.bhp-risk-tag--critical { background: #fff1f0; color: #cf1322; }
.bhp-risk-tag--high     { background: #fff2e8; color: #d4380d; }
.bhp-risk-tag--moderate { background: #fffbe6; color: #d48806; }
.bhp-risk-tag--low      { background: #f6ffed; color: #389e0d; }
</style>
