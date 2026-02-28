<template>
  <view class="pf-page">
    <view class="pf-navbar safe-area-top">
      <view class="pf-navbar__back" @tap="goBack"><text class="pf-navbar__arrow">&#8249;</text></view>
      <text class="pf-navbar__title">我的绩效</text>
      <view class="pf-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="pf-body">
      <template v-if="loading">
        <view class="bhp-skeleton" style="height: 400rpx; border-radius: var(--radius-lg);"></view>
      </template>
      <template v-else>

        <!-- 雷达图 -->
        <view class="pf-card">
          <text class="pf-card__title">本月行为改变指数</text>
          <view class="pf-radar">
            <!-- CSS 五边形雷达图 -->
            <view class="pf-radar__bg">
              <view v-for="(dim, idx) in dimensions" :key="dim.key" class="pf-radar__label" :style="labelPosition(idx)">
                <text>{{ dim.label }}</text>
              </view>
              <!-- 用多个层叠圆环模拟 -->
              <view class="pf-radar__ring pf-radar__ring--outer"></view>
              <view class="pf-radar__ring pf-radar__ring--mid"></view>
              <view class="pf-radar__ring pf-radar__ring--inner"></view>
            </view>
          </view>
        </view>

        <!-- 各维度得分 -->
        <view class="pf-card">
          <text class="pf-card__title">各维度得分</text>
          <view class="pf-dims">
            <view v-for="dim in dimensions" :key="dim.key" class="pf-dim">
              <view class="pf-dim__left">
                <text class="pf-dim__name">{{ dim.label }}</text>
                <view class="pf-dim__bar-track">
                  <view class="pf-dim__bar-fill" :style="{ width: dim.score + '%', background: dim.color }"></view>
                </view>
              </view>
              <view class="pf-dim__right">
                <text class="pf-dim__score">{{ dim.score }}</text>
                <text class="pf-dim__trend" :class="dim.trend > 0 ? 'pf-dim__trend--up' : dim.trend < 0 ? 'pf-dim__trend--down' : ''">
                  {{ dim.trend > 0 ? '+' + dim.trend : dim.trend < 0 ? String(dim.trend) : '-' }}
                </text>
              </view>
            </view>
          </view>
        </view>

        <!-- 综合评价 -->
        <view class="pf-card" v-if="overall">
          <text class="pf-card__title">综合评价</text>
          <view class="pf-overall">
            <text class="pf-overall__score">{{ overall.score }}</text>
            <text class="pf-overall__label">综合得分</text>
          </view>
          <text class="pf-overall__trend" v-if="overall.trend !== undefined">
            较上月 {{ overall.trend > 0 ? '+' : '' }}{{ overall.trend }}
          </text>
        </view>

      </template>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/api/request'

const DIM_META: { key: string; label: string; color: string }[] = [
  { key: 'nutrition', label: '饮食', color: '#10b981' },
  { key: 'exercise', label: '运动', color: '#f59e0b' },
  { key: 'sleep', label: '睡眠', color: '#8b5cf6' },
  { key: 'mental', label: '心理', color: '#3b82f6' },
  { key: 'social', label: '社交', color: '#ec4899' },
]

const loading    = ref(false)
const dimensions = ref<{ key: string; label: string; color: string; score: number; trend: number }[]>([])
const overall    = ref<{ score: number; trend: number } | null>(null)

onMounted(() => loadPerformance())

async function loadPerformance() {
  loading.value = true
  try {
    const res = await http.get<any>('/v1/users/me/performance')
    const scores = res.dimensions || res.scores || {}
    const trends = res.trends || res.changes || {}
    dimensions.value = DIM_META.map(m => ({
      ...m,
      score: scores[m.key] ?? 0,
      trend: trends[m.key] ?? 0,
    }))
    overall.value = {
      score: res.overall_score ?? res.total ?? Math.round(dimensions.value.reduce((s, d) => s + d.score, 0) / (dimensions.value.length || 1)),
      trend: res.overall_trend ?? res.total_change ?? 0,
    }
  } catch {
    dimensions.value = DIM_META.map(m => ({ ...m, score: 0, trend: 0 }))
  } finally {
    loading.value = false
  }
}

function labelPosition(idx: number) {
  const angle = (idx * 72 - 90) * (Math.PI / 180)
  const r = 140
  const cx = 140, cy = 140
  const x = cx + r * Math.cos(angle)
  const y = cy + r * Math.sin(angle)
  return { left: x + 'rpx', top: y + 'rpx', transform: 'translate(-50%, -50%)' }
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.pf-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.pf-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.pf-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.pf-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.pf-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.pf-navbar__placeholder { width: 64rpx; }
.pf-body { flex: 1; padding: 20rpx 32rpx 40rpx; }

.pf-card { background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light); }
.pf-card__title { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 20rpx; }

.pf-radar { display: flex; justify-content: center; padding: 20rpx 0; }
.pf-radar__bg { position: relative; width: 280rpx; height: 280rpx; }
.pf-radar__label { position: absolute; font-size: 22rpx; color: var(--text-secondary); font-weight: 600; white-space: nowrap; }
.pf-radar__ring { position: absolute; border-radius: 50%; border: 2rpx solid var(--bhp-gray-200); }
.pf-radar__ring--outer { top: 0; left: 0; right: 0; bottom: 0; }
.pf-radar__ring--mid { top: 25%; left: 25%; right: 25%; bottom: 25%; }
.pf-radar__ring--inner { top: 42%; left: 42%; right: 42%; bottom: 42%; }

.pf-dims { display: flex; flex-direction: column; gap: 16rpx; }
.pf-dim { display: flex; align-items: center; gap: 16rpx; }
.pf-dim__left { flex: 1; }
.pf-dim__name { display: block; font-size: 24rpx; color: var(--text-secondary); margin-bottom: 6rpx; }
.pf-dim__bar-track { height: 16rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.pf-dim__bar-fill { height: 100%; border-radius: var(--radius-full); transition: width 0.4s; }
.pf-dim__right { display: flex; align-items: center; gap: 8rpx; flex-shrink: 0; }
.pf-dim__score { font-size: 28rpx; font-weight: 800; color: var(--text-primary); width: 48rpx; text-align: right; }
.pf-dim__trend { font-size: 22rpx; font-weight: 600; width: 48rpx; text-align: center; }
.pf-dim__trend--up { color: #22c55e; }
.pf-dim__trend--down { color: #ef4444; }

.pf-overall { text-align: center; padding: 16rpx 0; }
.pf-overall__score { display: block; font-size: 48rpx; font-weight: 800; color: var(--bhp-primary-600); }
.pf-overall__label { display: block; font-size: 22rpx; color: var(--text-secondary); }
.pf-overall__trend { display: block; text-align: center; font-size: 24rpx; color: var(--text-tertiary); margin-top: 8rpx; }
</style>
