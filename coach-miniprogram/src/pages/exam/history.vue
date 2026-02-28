<template>
  <view class="eh-page">
    <view class="eh-navbar safe-area-top">
      <view class="eh-navbar__back" @tap="goBack"><text class="eh-navbar__arrow">&#8249;</text></view>
      <text class="eh-navbar__title">考试记录</text>
      <view class="eh-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="eh-body">
      <template v-if="loading">
        <view class="bhp-skeleton" style="height: 160rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
        <view class="bhp-skeleton" v-for="i in 3" :key="i" style="height: 120rpx; border-radius: var(--radius-lg); margin-bottom: 12rpx;"></view>
      </template>
      <template v-else>

        <!-- 统计 -->
        <view class="eh-summary">
          <view class="eh-summary__item">
            <text class="eh-summary__val">{{ stats.total }}</text>
            <text class="eh-summary__label">参加次数</text>
          </view>
          <view class="eh-summary__item">
            <text class="eh-summary__val">{{ stats.passed }}</text>
            <text class="eh-summary__label">通过次数</text>
          </view>
          <view class="eh-summary__item">
            <text class="eh-summary__val">{{ stats.highest }}</text>
            <text class="eh-summary__label">最高分</text>
          </view>
        </view>

        <!-- 列表 -->
        <view v-if="records.length" class="eh-list">
          <view v-for="item in records" :key="item.id" class="eh-card" @tap="viewDetail(item)">
            <view class="eh-card__top">
              <text class="eh-card__name">{{ item.exam_name || item.title }}</text>
              <view class="eh-card__badge" :class="item.passed ? 'eh-card__badge--pass' : 'eh-card__badge--fail'">
                <text>{{ item.passed ? '通过' : '未通过' }}</text>
              </view>
            </view>
            <view class="eh-card__bottom">
              <text class="eh-card__meta">{{ formatDate(item.completed_at || item.created_at) }}</text>
              <text class="eh-card__score">{{ item.score ?? 0 }}分</text>
              <text class="eh-card__time" v-if="item.time_spent">用时 {{ formatTime(item.time_spent) }}</text>
            </view>
          </view>
        </view>
        <view v-else class="eh-empty">
          <text class="eh-empty__icon">📜</text>
          <text class="eh-empty__text">暂无考试记录</text>
        </view>

      </template>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'

const loading = ref(false)
const records = ref<any[]>([])

const stats = computed(() => {
  const total = records.value.length
  const passed = records.value.filter(r => r.passed).length
  const highest = records.value.reduce((max, r) => Math.max(max, r.score ?? 0), 0)
  return { total, passed, highest }
})

onMounted(() => loadHistory())

async function loadHistory() {
  loading.value = true
  try {
    const res = await http.get<any>('/v1/certification/sessions/my-history')
    records.value = res.items || res.sessions || (Array.isArray(res) ? res : [])
  } catch {
    records.value = []
  } finally {
    loading.value = false
  }
}

function viewDetail(item: any) {
  uni.navigateTo({ url: `/pages/exam/result?id=${item.id}` })
}

function formatDate(dt: string): string {
  if (!dt) return ''
  const d = new Date(dt)
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m}分${s}秒` : `${s}秒`
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.eh-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.eh-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.eh-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.eh-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.eh-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.eh-navbar__placeholder { width: 64rpx; }
.eh-body { flex: 1; padding: 20rpx 32rpx 40rpx; }

.eh-summary {
  display: flex; gap: 12rpx; margin-bottom: 24rpx;
}
.eh-summary__item {
  flex: 1; text-align: center; padding: 24rpx 8rpx;
  background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border-light);
}
.eh-summary__val { display: block; font-size: 36rpx; font-weight: 800; color: var(--bhp-primary-600); }
.eh-summary__label { display: block; font-size: 22rpx; color: var(--text-secondary); margin-top: 4rpx; }

.eh-list { display: flex; flex-direction: column; gap: 12rpx; }
.eh-card {
  background: var(--surface); border-radius: var(--radius-lg); padding: 20rpx; border: 1px solid var(--border-light); cursor: pointer;
}
.eh-card__top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8rpx; }
.eh-card__name { font-size: 26rpx; font-weight: 600; color: var(--text-primary); flex: 1; }
.eh-card__badge { padding: 4rpx 14rpx; border-radius: var(--radius-full); font-size: 20rpx; font-weight: 600; }
.eh-card__badge--pass { background: #dcfce7; color: #16a34a; }
.eh-card__badge--fail { background: #fee2e2; color: #dc2626; }
.eh-card__bottom { display: flex; align-items: center; gap: 16rpx; }
.eh-card__meta { font-size: 22rpx; color: var(--text-tertiary); }
.eh-card__score { font-size: 24rpx; font-weight: 700; color: var(--bhp-primary-600); }
.eh-card__time { font-size: 22rpx; color: var(--text-tertiary); }

.eh-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 16rpx; }
.eh-empty__icon { font-size: 64rpx; }
.eh-empty__text { font-size: 26rpx; color: var(--text-tertiary); }
</style>
