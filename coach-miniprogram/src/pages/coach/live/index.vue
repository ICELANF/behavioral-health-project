<template>
  <view class="lv-page">
    <view class="lv-navbar safe-area-top">
      <view class="lv-navbar__back" @tap="goBack"><text class="lv-navbar__arrow">&#8249;</text></view>
      <text class="lv-navbar__title">直播中心</text>
      <view class="lv-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="lv-body">
      <template v-if="loading">
        <view class="bhp-skeleton" v-for="i in 3" :key="i" style="height: 140rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>
      <template v-else>

        <!-- 进行中 -->
        <view class="lv-section" v-if="liveNow.length">
          <text class="lv-section__title">正在直播</text>
          <view v-for="item in liveNow" :key="item.id" class="lv-card lv-card--live">
            <view class="lv-card__badge"><text>LIVE</text></view>
            <view class="lv-card__info">
              <text class="lv-card__title">{{ item.title }}</text>
              <text class="lv-card__meta">{{ item.host_name || '主讲人' }} · {{ item.online_count || 0 }}人在线</text>
            </view>
            <view class="lv-card__btn lv-card__btn--enter" @tap="enterLive(item)"><text>进入</text></view>
          </view>
        </view>

        <!-- 即将开始 -->
        <view class="lv-section" v-if="upcoming.length">
          <text class="lv-section__title">即将开始</text>
          <view v-for="item in upcoming" :key="item.id" class="lv-card">
            <view class="lv-card__info">
              <text class="lv-card__title">{{ item.title }}</text>
              <text class="lv-card__meta">{{ formatDate(item.start_time) }} · {{ item.host_name || '主讲人' }}</text>
            </view>
            <view class="lv-card__btn" :class="item.reserved ? 'lv-card__btn--reserved' : 'lv-card__btn--book'" @tap="toggleReserve(item)">
              <text>{{ item.reserved ? '已预约' : '预约' }}</text>
            </view>
          </view>
        </view>

        <!-- 历史回放 -->
        <view class="lv-section" v-if="history.length">
          <text class="lv-section__title">历史回放</text>
          <view v-for="item in history" :key="item.id" class="lv-card">
            <view class="lv-card__info">
              <text class="lv-card__title">{{ item.title }}</text>
              <text class="lv-card__meta">{{ formatDate(item.start_time || item.created_at) }} · {{ item.view_count || 0 }}次观看</text>
            </view>
            <view class="lv-card__btn lv-card__btn--replay" @tap="watchReplay(item)"><text>回放</text></view>
          </view>
        </view>

        <!-- 空状态 -->
        <view v-if="!liveNow.length && !upcoming.length && !history.length" class="lv-empty">
          <text class="lv-empty__icon">📡</text>
          <text class="lv-empty__text">暂无直播</text>
        </view>

      </template>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/api/request'

const loading  = ref(false)
const liveNow  = ref<any[]>([])
const upcoming = ref<any[]>([])
const history  = ref<any[]>([])

onMounted(() => loadLives())

async function loadLives() {
  loading.value = true
  try {
    const res = await http.get<any>('/v1/coach/lives')
    const items = res.items || res.lives || (Array.isArray(res) ? res : [])
    liveNow.value  = items.filter((i: any) => i.status === 'live' || i.status === 'streaming')
    upcoming.value = items.filter((i: any) => i.status === 'upcoming' || i.status === 'scheduled')
    history.value  = items.filter((i: any) => i.status === 'ended' || i.status === 'replay')
  } catch {
    liveNow.value = []; upcoming.value = []; history.value = []
  } finally {
    loading.value = false
  }
}

function enterLive(item: any) {
  uni.showToast({ title: '直播功能开发中', icon: 'none' })
}

async function toggleReserve(item: any) {
  try {
    await http.post(`/v1/coach/lives/${item.id}/reserve`, {})
    item.reserved = !item.reserved
    uni.showToast({ title: item.reserved ? '已预约' : '已取消', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

function watchReplay(item: any) {
  uni.showToast({ title: '回放功能开发中', icon: 'none' })
}

function formatDate(dt: string): string {
  if (!dt) return ''
  const d = new Date(dt)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.lv-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.lv-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.lv-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.lv-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.lv-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.lv-navbar__placeholder { width: 64rpx; }
.lv-body { flex: 1; padding: 20rpx 32rpx 40rpx; }

.lv-section { margin-bottom: 28rpx; }
.lv-section__title { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 16rpx; }

.lv-card {
  display: flex; align-items: center; gap: 16rpx;
  background: var(--surface); border-radius: var(--radius-lg); padding: 20rpx; margin-bottom: 12rpx; border: 1px solid var(--border-light);
}
.lv-card--live { border-color: #ef4444; }
.lv-card__badge { padding: 4rpx 14rpx; border-radius: var(--radius-full); background: #ef4444; color: #fff; font-size: 20rpx; font-weight: 700; flex-shrink: 0; }
.lv-card__info { flex: 1; }
.lv-card__title { display: block; font-size: 26rpx; font-weight: 600; color: var(--text-primary); }
.lv-card__meta { display: block; font-size: 22rpx; color: var(--text-tertiary); margin-top: 4rpx; }

.lv-card__btn { padding: 10rpx 24rpx; border-radius: var(--radius-full); font-size: 22rpx; font-weight: 600; cursor: pointer; flex-shrink: 0; }
.lv-card__btn--enter { background: #ef4444; color: #fff; }
.lv-card__btn--book { background: var(--bhp-primary-50); color: var(--bhp-primary-600); }
.lv-card__btn--reserved { background: var(--bhp-gray-100); color: var(--text-secondary); }
.lv-card__btn--replay { background: var(--surface-secondary); color: var(--text-secondary); border: 1px solid var(--border-light); }

.lv-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 16rpx; }
.lv-empty__icon { font-size: 64rpx; }
.lv-empty__text { font-size: 26rpx; color: var(--text-tertiary); }
</style>
