<template>
  <view class="lc-page">
    <view class="lc-navbar safe-area-top">
      <view class="lc-navbar__back" @tap="goBack"><text class="lc-navbar__arrow">&#8249;</text></view>
      <text class="lc-navbar__title">我的学分</text>
      <view class="lc-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="lc-body">
      <template v-if="loading">
        <view class="bhp-skeleton" style="height: 160rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
        <view class="bhp-skeleton" v-for="i in 4" :key="i" style="height: 80rpx; border-radius: var(--radius-md); margin-bottom: 12rpx;"></view>
      </template>
      <template v-else>

        <!-- 学分统计 -->
        <view class="lc-summary">
          <view class="lc-summary__item lc-summary__item--main">
            <text class="lc-summary__val">{{ summary.total }}</text>
            <text class="lc-summary__label">总学分</text>
          </view>
          <view class="lc-summary__item">
            <text class="lc-summary__val">{{ summary.this_month }}</text>
            <text class="lc-summary__label">本月获得</text>
          </view>
        </view>

        <!-- 按月分组流水 -->
        <template v-if="groupedRecords.length">
          <view v-for="group in groupedRecords" :key="group.month" class="lc-group">
            <text class="lc-group__title">{{ group.month }}</text>
            <view class="lc-records">
              <view v-for="item in group.items" :key="item.id" class="lc-record">
                <view class="lc-record__left">
                  <text class="lc-record__source">{{ item.source || item.description }}</text>
                  <text class="lc-record__time">{{ formatDate(item.created_at || item.earned_at) }}</text>
                </view>
                <text class="lc-record__credits" :class="item.credits > 0 ? 'lc-record__credits--plus' : 'lc-record__credits--minus'">
                  {{ item.credits > 0 ? '+' : '' }}{{ item.credits }}
                </text>
              </view>
            </view>
          </view>
        </template>
        <view v-else class="lc-empty">
          <text class="lc-empty__icon">🏅</text>
          <text class="lc-empty__text">暂无学分记录</text>
        </view>

      </template>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'

const loading = ref(false)
const summary = ref({ total: 0, this_month: 0 })
const records = ref<any[]>([])

const groupedRecords = computed(() => {
  const groups: Record<string, any[]> = {}
  records.value.forEach(r => {
    const dt = r.created_at || r.earned_at || ''
    const d = new Date(dt)
    const key = dt ? `${d.getFullYear()}年${d.getMonth() + 1}月` : '未知'
    if (!groups[key]) groups[key] = []
    groups[key].push(r)
  })
  return Object.entries(groups).map(([month, items]) => ({ month, items }))
})

onMounted(() => loadCredits())

async function loadCredits() {
  loading.value = true
  try {
    const res = await http.get<any>('/v1/learning/credits')
    summary.value = {
      total: res.total_credits ?? res.total ?? 0,
      this_month: res.this_month ?? res.month_credits ?? 0,
    }
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
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.lc-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.lc-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.lc-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.lc-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.lc-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.lc-navbar__placeholder { width: 64rpx; }
.lc-body { flex: 1; padding: 20rpx 32rpx 40rpx; }

.lc-summary { display: flex; gap: 16rpx; margin-bottom: 28rpx; }
.lc-summary__item {
  flex: 1; text-align: center; padding: 28rpx 16rpx;
  background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border-light);
}
.lc-summary__item--main { background: linear-gradient(135deg, var(--bhp-primary-50), var(--bhp-primary-100)); border-color: var(--bhp-primary-200); }
.lc-summary__val { display: block; font-size: 40rpx; font-weight: 800; color: var(--bhp-primary-600); }
.lc-summary__label { display: block; font-size: 22rpx; color: var(--text-secondary); margin-top: 4rpx; }

.lc-group { margin-bottom: 24rpx; }
.lc-group__title { display: block; font-size: 24rpx; font-weight: 700; color: var(--text-secondary); margin-bottom: 12rpx; }

.lc-records { display: flex; flex-direction: column; gap: 8rpx; }
.lc-record {
  display: flex; align-items: center; justify-content: space-between;
  background: var(--surface); border-radius: var(--radius-md); padding: 16rpx 20rpx; border: 1px solid var(--border-light);
}
.lc-record__left { flex: 1; }
.lc-record__source { display: block; font-size: 26rpx; color: var(--text-primary); }
.lc-record__time { display: block; font-size: 20rpx; color: var(--text-tertiary); margin-top: 2rpx; }
.lc-record__credits { font-size: 28rpx; font-weight: 800; flex-shrink: 0; }
.lc-record__credits--plus { color: var(--bhp-primary-600); }
.lc-record__credits--minus { color: #ef4444; }

.lc-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 16rpx; }
.lc-empty__icon { font-size: 64rpx; }
.lc-empty__text { font-size: 26rpx; color: var(--text-tertiary); }
</style>
