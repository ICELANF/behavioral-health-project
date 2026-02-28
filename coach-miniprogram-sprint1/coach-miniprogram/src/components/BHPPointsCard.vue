<template>
  <!-- 三维积分展示卡 -->
  <view class="points-card bhp-card">

    <!-- 顶部：总成长积分 + 连续打卡 -->
    <view class="points-card__header flex-between">
      <view>
        <text class="points-card__main-label">成长积分</text>
        <view class="points-card__main-value flex-start gap-2">
          <text class="points-card__number">{{ formatPoints(growthPoints) }}</text>
          <text class="points-card__unit">分</text>
        </view>
      </view>
      <view class="points-card__streak" v-if="streak > 0">
        <text class="points-card__streak-icon">🔥</text>
        <text class="points-card__streak-days">{{ streak }}</text>
        <text class="points-card__streak-label">天连续</text>
      </view>
    </view>

    <!-- 晋级进度条 -->
    <view class="points-card__progress-section" v-if="showProgress && nextThreshold > 0">
      <view class="flex-between mb-1">
        <text class="points-card__progress-label">距{{ nextLevelLabel }}还差</text>
        <text class="points-card__progress-remain">{{ nextThreshold - growthPoints }} 分</text>
      </view>
      <view class="bhp-progress">
        <view class="bhp-progress__bar" :style="{ width: progressPct + '%' }"></view>
      </view>
    </view>

    <!-- 三维积分 -->
    <view class="points-card__dims" v-if="showDims">
      <view class="points-card__dim">
        <text class="points-card__dim-value">{{ formatPoints(growthPoints) }}</text>
        <text class="points-card__dim-label">成长积分</text>
        <view class="points-card__dim-dot" style="background: #10b981"></view>
      </view>
      <view class="points-card__dim-divider"></view>
      <view class="points-card__dim">
        <text class="points-card__dim-value">{{ formatPoints(contributionPoints) }}</text>
        <text class="points-card__dim-label">贡献积分</text>
        <view class="points-card__dim-dot" style="background: #3b82f6"></view>
      </view>
      <view class="points-card__dim-divider"></view>
      <view class="points-card__dim">
        <text class="points-card__dim-value">{{ formatPoints(influencePoints) }}</text>
        <text class="points-card__dim-label">影响力</text>
        <view class="points-card__dim-dot" style="background: #f59e0b"></view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatPoints, LEVEL_THRESHOLDS, getNextRole, getRoleLevel, ROLE_LABEL_MAP } from '@/utils/level'

const props = withDefaults(defineProps<{
  role: string
  growthPoints: number
  contributionPoints?: number
  influencePoints?: number
  streak?: number
  showDims?: boolean
  showProgress?: boolean
}>(), {
  contributionPoints: 0,
  influencePoints: 0,
  streak: 0,
  showDims: true,
  showProgress: true
})

const nextRole = computed(() => getNextRole(props.role))

const nextThreshold = computed(() => {
  if (!nextRole.value) return 0
  const lv = `L${getRoleLevel(nextRole.value)}` as keyof typeof LEVEL_THRESHOLDS
  return LEVEL_THRESHOLDS[lv]?.growth || 0
})

const nextLevelLabel = computed(() => {
  if (!nextRole.value) return ''
  return ROLE_LABEL_MAP[nextRole.value] || ''
})

const progressPct = computed(() => {
  if (!nextThreshold.value) return 100
  return Math.min(Math.round((props.growthPoints / nextThreshold.value) * 100), 100)
})
</script>

<style scoped>
.points-card {
  background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 60%);
}

.points-card__header { margin-bottom: 16px; }

.points-card__main-label {
  font-size: 24rpx;
  color: var(--text-secondary);
  display: block;
  margin-bottom: 4px;
}
.points-card__number {
  font-size: 56rpx;
  font-weight: 700;
  color: var(--bhp-primary-600);
  font-family: var(--font-display);
  line-height: 1;
}
.points-card__unit {
  font-size: 24rpx;
  color: var(--text-secondary);
  margin-top: 8rpx;
}

/* 连续打卡 */
.points-card__streak {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--bhp-warm-50);
  border-radius: 12px;
  padding: 10px 16px;
}
.points-card__streak-icon  { font-size: 32rpx; }
.points-card__streak-days  { font-size: 40rpx; font-weight: 700; color: var(--bhp-warm-600); line-height: 1.2; }
.points-card__streak-label { font-size: 20rpx; color: var(--bhp-warm-600); }

/* 晋级进度 */
.points-card__progress-section { margin-bottom: 16px; }
.points-card__progress-label   { font-size: 22rpx; color: var(--text-secondary); }
.points-card__progress-remain  { font-size: 22rpx; color: var(--bhp-primary-600); font-weight: 600; }

/* 三维积分 */
.points-card__dims {
  display: flex;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--divider);
}
.points-card__dim {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.points-card__dim-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-top: 2px;
}
.points-card__dim-value { font-size: 30rpx; font-weight: 700; color: var(--text-primary); }
.points-card__dim-label { font-size: 20rpx; color: var(--text-secondary); }

.points-card__dim-divider {
  width: 1px;
  height: 40px;
  background: var(--divider);
}
</style>
