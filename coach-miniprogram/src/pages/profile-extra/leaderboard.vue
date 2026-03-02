<template>
  <view class="lb-page">
    <view class="lb-header">
      <text class="lb-title">积分排行榜</text>
      <text class="lb-sub">教练培养积分榜</text>
    </view>

    <scroll-view scroll-y class="lb-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 我的排名 -->
      <view class="lb-my-rank">
        <text class="lb-my-rank-label">我的排名</text>
        <text class="lb-my-rank-num">{{ myRank > 0 ? '#' + myRank : '—' }}</text>
        <text class="lb-my-points">{{ myPoints }} 分</text>
      </view>

      <!-- 排行榜 -->
      <view class="lb-list">
        <view v-for="(item, idx) in list" :key="item.id || idx"
          class="lb-item" :class="{ 'lb-item--me': item.is_me }">
          <view class="lb-rank-num">
            <text v-if="idx < 3" class="lb-rank-medal">{{ ['🥇','🥈','🥉'][idx] }}</text>
            <text v-else class="lb-rank-text">{{ idx + 1 }}</text>
          </view>
          <view class="lb-avatar" :style="{ background: avatarColor(item.name) }">
            {{ (item.name || '?')[0] }}
          </view>
          <view class="lb-item-info">
            <text class="lb-item-name">{{ item.name || '用户' }}</text>
            <text class="lb-item-level">{{ levelName(item.level) }}</text>
          </view>
          <text class="lb-item-points">{{ item.points || item.total_credits || 0 }}</text>
        </view>
      </view>

      <view v-if="list.length === 0 && !loading" class="lb-empty">
        <text class="lb-empty-icon">🏅</text>
        <text class="lb-empty-text">排行榜数据加载中</text>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const BASE_URL = 'http://localhost:8000'
function getToken() { return uni.getStorageSync('access_token') || '' }

async function http<T = any>(url: string): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url, method: 'GET',
      header: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/json' },
      success: (res: any) => {
        if (res.statusCode === 401) { uni.removeStorageSync('access_token'); uni.reLaunch({ url: '/pages/auth/login' }); reject(new Error('401')); return }
        res.statusCode < 300 ? resolve(res.data as T) : reject(new Error(`${res.statusCode}`))
      },
      fail: (e: any) => reject(e),
    })
  })
}

const list = ref<any[]>([])
const myRank = ref(0)
const myPoints = ref(0)
const refreshing = ref(false)
const loading = ref(false)

const colorPool = ['#3498DB','#E74C3C','#27AE60','#9B59B6','#E67E22','#1ABC9C']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let h = 0; for (const c of name) h = c.charCodeAt(0) + ((h << 5) - h)
  return colorPool[Math.abs(h) % colorPool.length]
}
function levelName(k: string) { return { observer:'观察者', grower:'成长者', sharer:'分享者' }[k] || (k || '') }

async function loadData() {
  // /api/v1/leaderboard/credits 后端尚未开放，直接展示空状态
  loading.value = false
  list.value = []
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
onMounted(() => { loadData() })
</script>

<style scoped>
.lb-page { min-height: 100vh; background: #F5F6FA; }
.lb-header { padding: 24rpx 32rpx; padding-top: calc(80rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff; }
.lb-title { display: block; font-size: 38rpx; font-weight: 700; }
.lb-sub { display: block; font-size: 24rpx; opacity: 0.85; margin-top: 6rpx; }
.lb-scroll { height: calc(100vh - 200rpx); }
.lb-my-rank { display: flex; align-items: center; gap: 16rpx; background: linear-gradient(135deg, #F0FBF6, #E8F8F0); margin: 24rpx; border-radius: 16rpx; padding: 20rpx 24rpx; border: 1rpx solid #C8EFD9; }
.lb-my-rank-label { font-size: 24rpx; color: #5B6B7F; flex: 1; }
.lb-my-rank-num { font-size: 36rpx; font-weight: 700; color: #2D8E69; }
.lb-my-points { font-size: 28rpx; font-weight: 700; color: #2D8E69; }
.lb-list { background: #fff; margin: 0 24rpx 16rpx; border-radius: 16rpx; padding: 8rpx 0; }
.lb-item { display: flex; align-items: center; gap: 16rpx; padding: 16rpx 24rpx; border-bottom: 1rpx solid #F8F8F8; }
.lb-item:last-child { border-bottom: none; }
.lb-item--me { background: #EAFAF2; }
.lb-rank-num { width: 48rpx; text-align: center; flex-shrink: 0; }
.lb-rank-medal { font-size: 32rpx; }
.lb-rank-text { font-size: 26rpx; color: #8E99A4; font-weight: 600; }
.lb-avatar { width: 64rpx; height: 64rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 26rpx; font-weight: 700; flex-shrink: 0; }
.lb-item-info { flex: 1; }
.lb-item-name { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; }
.lb-item-level { font-size: 20rpx; color: #8E99A4; }
.lb-item-points { font-size: 28rpx; font-weight: 700; color: #2D8E69; }
.lb-empty { text-align: center; padding: 80rpx 0; }
.lb-empty-icon { display: block; font-size: 64rpx; margin-bottom: 16rpx; }
.lb-empty-text { font-size: 26rpx; color: #8E99A4; }
</style>
