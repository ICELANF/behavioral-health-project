<template>
  <view class="live-page">
    <view class="live-navbar">
      <view class="live-nav-back" @tap="goBack">←</view>
      <text class="live-nav-title">直播/活动中心</text>
    </view>

    <!-- Tab -->
    <view class="live-tabs">
      <view v-for="tab in liveTabs" :key="tab.key" class="live-tab" :class="{ 'live-tab--active': activeTab === tab.key }" @tap="activeTab = tab.key">
        {{ tab.label }}
        <view v-if="tab.badge > 0" class="live-tab-badge live-tab-badge--live">{{ tab.badge }}</view>
      </view>
    </view>

    <scroll-view scroll-y class="live-list" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 直播中 -->
      <template v-if="activeTab === 'live'">
        <view v-for="item in liveNow" :key="item.id" class="live-card live-card--live">
          <view class="live-card-cover">
            <view class="live-badge-live">● LIVE</view>
            <text class="live-card-viewers">{{ item.viewers || 0 }}人观看</text>
          </view>
          <view class="live-card-body">
            <text class="live-card-title">{{ item.title }}</text>
            <text class="live-card-host">主讲: {{ item.host || '—' }}</text>
            <view class="live-card-btn live-card-btn--enter" @tap="enterLive(item)">进入直播</view>
          </view>
        </view>
        <view v-if="liveNow.length === 0" class="live-empty">
          <text class="live-empty-icon">📡</text>
          <text class="live-empty-text">当前没有进行中的直播</text>
        </view>
      </template>

      <!-- 即将开始 -->
      <template v-if="activeTab === 'upcoming'">
        <view v-for="item in upcoming" :key="item.id" class="live-card">
          <view class="live-card-body">
            <view class="live-card-time-tag">{{ formatTime(item.start_time) }}</view>
            <text class="live-card-title">{{ item.title }}</text>
            <text class="live-card-host">主讲: {{ item.host || '—' }}</text>
            <view class="live-card-btn" :class="item._reserved ? 'live-card-btn--reserved' : 'live-card-btn--reserve'" @tap="toggleReserve(item)">
              {{ item._reserved ? '✓ 已预约' : '📅 预约提醒' }}
            </view>
          </view>
        </view>
        <view v-if="upcoming.length === 0" class="live-empty">
          <text class="live-empty-icon">📅</text>
          <text class="live-empty-text">暂无即将开始的直播</text>
        </view>
      </template>

      <!-- 历史回放 -->
      <template v-if="activeTab === 'replay'">
        <view v-for="item in replays" :key="item.id" class="live-card" @tap="watchReplay(item)">
          <view class="live-card-body">
            <text class="live-card-title">{{ item.title }}</text>
            <text class="live-card-host">{{ item.host || '—' }} · {{ item.duration || '—' }} · {{ item.views || 0 }}次观看</text>
            <text class="live-card-date">{{ formatDate(item.end_time || item.created_at) }}</text>
          </view>
          <text class="live-card-play">▶</text>
        </view>
        <view v-if="replays.length === 0" class="live-empty">
          <text class="live-empty-icon">📼</text>
          <text class="live-empty-text">暂无历史回放</text>
        </view>
      </template>
    </scroll-view>

    <!-- 底部提示 -->
    <view class="live-footer">
      <text class="live-footer-text">直播功能持续完善中，更多内容即将上线</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const BASE_URL = 'http://localhost:8000'

function getToken(): string {
  return uni.getStorageSync('access_token') || ''
}

async function http<T = any>(url: string, options: any = {}): Promise<T> {
  const { method = 'GET', data } = options
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: {
        'Authorization': 'Bearer ' + getToken(),
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        if (res.statusCode === 401) {
          uni.removeStorageSync('access_token')
          uni.reLaunch({ url: '/pages/auth/login' })
          reject(new Error('401')); return
        }
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail: (err: any) => reject(err)
    })
  })
}

const activeTab = ref('live')
const refreshing = ref(false)
const liveNow = ref<any[]>([])
const upcoming = ref<any[]>([])
const replays = ref<any[]>([])

const liveTabs = computed(() => [
  { key: 'live', label: '直播中', badge: liveNow.value.length },
  { key: 'upcoming', label: '即将开始', badge: upcoming.value.length },
  { key: 'replay', label: '历史回放', badge: 0 },
])

function formatTime(t: string): string {
  if (!t) return '待定'
  const d = new Date(t)
  return (d.getMonth() + 1) + '/' + d.getDate() + ' ' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
}
function formatDate(t: string): string {
  if (!t) return ''
  return t.slice(0, 10)
}

async function loadData() {
  // 直播功能后端尚未开放，直接展示空状态，避免 404 控制台报错
  liveNow.value = []
  upcoming.value = []
  replays.value = []
}

function enterLive(item: any) {
  uni.showToast({ title: '直播功能开发中', icon: 'none' })
}
function toggleReserve(item: any) {
  item._reserved = !item._reserved
  uni.showToast({ title: item._reserved ? '预约成功' : '已取消预约', icon: 'success' })
}
function watchReplay(item: any) {
  if (item.replay_url) {
    uni.navigateTo({ url: '/pages/learning/video-player?id=' + item.id + '&url=' + encodeURIComponent(item.replay_url) })
  } else {
    uni.showToast({ title: '回放准备中', icon: 'none' })
  }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.live-page { min-height: 100vh; background: #F5F6FA; }
.live-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #E74C3C 0%, #FF6B6B 100%); color: #fff; }
.live-nav-back { font-size: 40rpx; padding: 16rpx; }
.live-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }

.live-tabs { display: flex; padding: 16rpx 24rpx; gap: 12rpx; }
.live-tab { position: relative; flex: 1; text-align: center; padding: 16rpx 0; background: #fff; border-radius: 12rpx; font-size: 26rpx; color: #5B6B7F; }
.live-tab--active { background: #E74C3C; color: #fff; }
.live-tab-badge { position: absolute; top: -8rpx; right: 16rpx; min-width: 28rpx; height: 28rpx; border-radius: 14rpx; font-size: 18rpx; display: flex; align-items: center; justify-content: center; padding: 0 6rpx; }
.live-tab-badge--live { background: #E74C3C; color: #fff; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.live-list { height: calc(100vh - 380rpx); padding: 0 24rpx; }

.live-card { background: #fff; border-radius: 16rpx; margin-bottom: 16rpx; overflow: hidden; }
.live-card--live { border: 2rpx solid #E74C3C; }
.live-card-cover { position: relative; height: 200rpx; background: linear-gradient(135deg, #2C3E50, #34495E); display: flex; align-items: center; justify-content: center; }
.live-badge-live { position: absolute; top: 16rpx; left: 16rpx; background: #E74C3C; color: #fff; padding: 4rpx 16rpx; border-radius: 8rpx; font-size: 24rpx; font-weight: 600; animation: pulse 1.5s infinite; }
.live-card-viewers { position: absolute; top: 16rpx; right: 16rpx; color: #fff; font-size: 22rpx; background: rgba(0,0,0,0.4); padding: 4rpx 12rpx; border-radius: 6rpx; }
.live-card-body { padding: 20rpx 24rpx; }
.live-card-time-tag { display: inline-block; padding: 4rpx 12rpx; background: #FFF3E0; color: #E67E22; border-radius: 6rpx; font-size: 22rpx; margin-bottom: 8rpx; }
.live-card-title { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.live-card-host { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 6rpx; }
.live-card-date { display: block; font-size: 22rpx; color: #BDC3C7; margin-top: 4rpx; }
.live-card-btn { display: block; text-align: center; padding: 14rpx 0; border-radius: 10rpx; margin-top: 16rpx; font-size: 26rpx; font-weight: 600; }
.live-card-btn--enter { background: #E74C3C; color: #fff; }
.live-card-btn--reserve { background: #FFF3E0; color: #E67E22; }
.live-card-btn--reserved { background: #E8F5E9; color: #27AE60; }
.live-card-play { display: flex; align-items: center; padding: 24rpx; font-size: 36rpx; color: #3498DB; }

.live-empty { text-align: center; padding: 120rpx 0; }
.live-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.live-empty-text { font-size: 28rpx; color: #8E99A4; }

.live-footer { text-align: center; padding: 24rpx; }
.live-footer-text { font-size: 24rpx; color: #BDC3C7; }
</style>