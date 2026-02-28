<template>
  <view class="ap-page">

    <view class="ap-navbar safe-area-top">
      <view class="ap-navbar__back" @tap="goBack"><text class="ap-navbar__arrow">‹</text></view>
      <text class="ap-navbar__title">待完成评估</text>
      <view class="ap-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="ap-body">

      <template v-if="loading">
        <view class="bhp-skeleton" v-for="i in 3" :key="i" style="height: 160rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>

      <view v-else-if="list.length" class="ap-list">
        <view v-for="item in list" :key="item.id" class="ap-card" @tap="goAssessment(item.id)">
          <view class="ap-card__header">
            <text class="ap-card__name">{{ item.scales?.join(' + ') || '综合评估' }}</text>
            <view class="ap-card__status" :class="`ap-card__status--${item.status}`">
              <text>{{ STATUS_LABEL[item.status] || item.status }}</text>
            </view>
          </view>
          <view class="ap-card__meta">
            <text class="ap-card__coach" v-if="item.coach_name">分配教练：{{ item.coach_name }}</text>
            <text class="ap-card__date" v-if="item.created_at">分配时间：{{ formatDate(item.created_at) }}</text>
          </view>
          <view class="ap-card__footer" v-if="item.note">
            <text class="ap-card__note">{{ item.note }}</text>
          </view>
        </view>
      </view>

      <view v-else class="ap-empty">
        <text class="ap-empty__icon">🎉</text>
        <text class="ap-empty__text">暂无待完成评估</text>
      </view>

    </scroll-view>

  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/api/request'

const STATUS_LABEL: Record<string, string> = {
  assigned:    '待完成',
  in_progress: '进行中',
  completed:   '已完成',
}

const list    = ref<any[]>([])
const loading = ref(false)

onMounted(() => loadList())

async function loadList() {
  loading.value = true
  try {
    const res = await http.get<{ items: any[] }>('/v1/assessment-assignments/my-pending', { status: 'assigned' })
    list.value = res.items || (Array.isArray(res) ? res : [])
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

function formatDate(dt: string): string {
  if (!dt) return ''
  const d = new Date(dt)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function goAssessment(id: number) {
  uni.navigateTo({ url: `/pages/assessment/do?id=${id}` })
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.ap-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.ap-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.ap-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.ap-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.ap-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.ap-navbar__placeholder { width: 64rpx; }

.ap-body { flex: 1; padding: 20rpx 32rpx 40rpx; }
.ap-list { display: flex; flex-direction: column; gap: 16rpx; }

.ap-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; border: 1px solid var(--border-light); cursor: pointer;
}
.ap-card:active { opacity: 0.85; }
.ap-card__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.ap-card__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); flex: 1; }
.ap-card__status {
  font-size: 20rpx; font-weight: 600; padding: 4rpx 16rpx; border-radius: var(--radius-full);
}
.ap-card__status--assigned { background: #fff7ed; color: #ea580c; }
.ap-card__status--in_progress { background: #eff6ff; color: #2563eb; }
.ap-card__status--completed { background: #f0fdf4; color: #16a34a; }

.ap-card__meta { display: flex; flex-direction: column; gap: 6rpx; }
.ap-card__coach, .ap-card__date { font-size: 22rpx; color: var(--text-secondary); }
.ap-card__footer { margin-top: 12rpx; padding-top: 12rpx; border-top: 1px solid var(--border-light); }
.ap-card__note { font-size: 22rpx; color: var(--text-tertiary); }

.ap-empty { display: flex; flex-direction: column; align-items: center; padding: 160rpx 0; gap: 16rpx; }
.ap-empty__icon { font-size: 64rpx; }
.ap-empty__text { font-size: 26rpx; color: var(--text-tertiary); }
</style>
