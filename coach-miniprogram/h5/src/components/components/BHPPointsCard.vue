<template>
  <view class="pts-card" :style="{ background: `linear-gradient(135deg, ${color}dd, ${color}99)` }">

    <!-- 角色标题行 -->
    <view class="pts-card__header">
      <BHPLevelBadge :role="role" size="sm" />
      <view class="pts-card__streak" v-if="streak > 0">
        <text class="pts-card__streak-icon">🔥</text>
        <text class="pts-card__streak-text">连续 {{ streak }} 天</text>
      </view>
    </view>

    <!-- 积分三栏 -->
    <view class="pts-card__body">
      <view class="pts-card__dim" v-for="dim in dims" :key="dim.key">
        <text class="pts-card__val">{{ formatPts(dim.value) }}</text>
        <text class="pts-card__lbl">{{ dim.label }}</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ROLE_COLOR, formatPoints } from '@/utils/level'
import BHPLevelBadge from './BHPLevelBadge.vue'

const props = withDefaults(defineProps<{
  role:                string
  growthPoints:        number
  contributionPoints?: number
  influencePoints?:    number
  streak?:             number
}>(), {
  contributionPoints: 0,
  influencePoints:    0,
  streak:             0,
})

const color = computed(() => ROLE_COLOR[props.role?.toLowerCase()] ?? '#10b981')

const dims = computed(() => [
  { key: 'g', label: '成长积分', value: props.growthPoints       },
  { key: 'c', label: '贡献积分', value: props.contributionPoints },
  { key: 'i', label: '影响积分', value: props.influencePoints    },
])

function formatPts(v: number) { return formatPoints(v ?? 0) }
</script>

<style scoped>
.pts-card {
  border-radius: var(--radius-xl);
  padding: 28rpx 32rpx 24rpx;
}
.pts-card__header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 24rpx;
}
.pts-card__streak {
  display: flex; align-items: center; gap: 6rpx;
  background: rgba(255,255,255,0.25); border-radius: var(--radius-full);
  padding: 4rpx 16rpx;
}
.pts-card__streak-icon { font-size: 24rpx; }
.pts-card__streak-text { font-size: 22rpx; color: #fff; font-weight: 600; }

.pts-card__body {
  display: flex; justify-content: space-around;
}
.pts-card__dim  { display: flex; flex-direction: column; align-items: center; gap: 6rpx; }
.pts-card__val  { font-size: 40rpx; font-weight: 700; color: #fff; line-height: 1; }
.pts-card__lbl  { font-size: 20rpx; color: rgba(255,255,255,0.85); }
</style>
