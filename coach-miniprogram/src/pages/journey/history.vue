<template>
  <view class="jh-page">
    <view class="jh-navbar safe-area-top">
      <view class="jh-navbar__back" @tap="goBack"><text class="jh-navbar__arrow">‹</text></view>
      <text class="jh-navbar__title">晋级历史</text>
      <view class="jh-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="jh-body">
      <template v-if="loading">
        <view class="bhp-skeleton" v-for="i in 4" :key="i" style="height: 100rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>

      <view v-else-if="records.length" class="jh-timeline">
        <view v-for="(item, idx) in records" :key="idx" class="jh-tl-item">
          <view class="jh-tl-line">
            <view class="jh-tl-dot" :class="{ 'jh-tl-dot--first': idx === 0 }"></view>
            <view class="jh-tl-bar" v-if="idx < records.length - 1"></view>
          </view>
          <view class="jh-tl-content">
            <view class="jh-tl-header">
              <text class="jh-tl-from">{{ item.from_level || item.from_stage }}</text>
              <text class="jh-tl-arrow">→</text>
              <text class="jh-tl-to">{{ item.to_level || item.to_stage }}</text>
            </view>
            <text class="jh-tl-date">{{ formatDate(item.created_at || item.transitioned_at) }}</text>
            <text class="jh-tl-points" v-if="item.points_earned">+{{ item.points_earned }} 积分</text>
          </view>
        </view>
      </view>

      <view v-else class="jh-empty">
        <text class="jh-empty__icon">📜</text>
        <text class="jh-empty__text">暂无晋级记录</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/api/request'

const records = ref<any[]>([])
const loading = ref(false)

onMounted(() => loadHistory())

async function loadHistory() {
  loading.value = true
  try {
    const res = await http.get<any>('/v1/journey/history')
    records.value = res.items || res.records || (Array.isArray(res) ? res : [])
  } catch {
    records.value = []
  } finally {
    loading.value = false
  }
}

function formatDate(dt: string): string {
  if (!dt) return ''
  const d = new Date(dt)
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.jh-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.jh-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.jh-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.jh-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.jh-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.jh-navbar__placeholder { width: 64rpx; }
.jh-body { flex: 1; padding: 32rpx 32rpx 40rpx; }

.jh-timeline { display: flex; flex-direction: column; }
.jh-tl-item { display: flex; gap: 20rpx; }
.jh-tl-line { display: flex; flex-direction: column; align-items: center; width: 32rpx; }
.jh-tl-dot { width: 20rpx; height: 20rpx; border-radius: 50%; background: var(--bhp-primary-300); flex-shrink: 0; margin-top: 6rpx; }
.jh-tl-dot--first { background: var(--bhp-primary-500); width: 24rpx; height: 24rpx; }
.jh-tl-bar { width: 2rpx; flex: 1; background: var(--bhp-primary-200); min-height: 40rpx; }

.jh-tl-content { flex: 1; padding-bottom: 32rpx; }
.jh-tl-header { display: flex; align-items: center; gap: 8rpx; margin-bottom: 6rpx; }
.jh-tl-from { font-size: 24rpx; color: var(--text-secondary); font-weight: 600; }
.jh-tl-arrow { font-size: 24rpx; color: var(--text-tertiary); }
.jh-tl-to { font-size: 26rpx; color: var(--bhp-primary-600); font-weight: 700; }
.jh-tl-date { font-size: 22rpx; color: var(--text-tertiary); display: block; }
.jh-tl-points { font-size: 22rpx; color: var(--bhp-primary-500); font-weight: 600; display: block; margin-top: 4rpx; }

.jh-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 16rpx; }
.jh-empty__icon { font-size: 64rpx; }
.jh-empty__text { font-size: 26rpx; color: var(--text-tertiary); }
</style>
