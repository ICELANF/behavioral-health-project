<template>
  <view
    class="bhp-level-badge"
    :class="`bhp-level-badge--${size}`"
    :style="{ background: color + '18', color: color, borderColor: color + '40' }"
  >
    <text class="bhp-level-badge__text">{{ label }}</text>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ROLE_LABEL, ROLE_COLOR } from '@/utils/level'

const props = withDefaults(defineProps<{
  role:  string
  size?: 'xs' | 'sm' | 'md'
}>(), {
  size: 'sm',
})

const label = computed(() => ROLE_LABEL[props.role?.toLowerCase()] ?? props.role ?? '成长者')
const color = computed(() => ROLE_COLOR[props.role?.toLowerCase()]  ?? '#10b981')
</script>

<style scoped>
.bhp-level-badge {
  display: inline-flex;
  align-items: center;
  border-radius: var(--radius-full);
  border: 1px solid;
  font-weight: 600;
  white-space: nowrap;
}
.bhp-level-badge--xs  { padding: 2rpx 10rpx; }
.bhp-level-badge--sm  { padding: 4rpx 14rpx; }
.bhp-level-badge--md  { padding: 6rpx 20rpx; }
.bhp-level-badge__text { font-size: inherit; }
.bhp-level-badge--xs .bhp-level-badge__text { font-size: 18rpx; }
.bhp-level-badge--sm .bhp-level-badge__text { font-size: 22rpx; }
.bhp-level-badge--md .bhp-level-badge__text { font-size: 26rpx; }
</style>
