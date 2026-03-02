<template>
  <view class="learn-page">
    <view class="learn-header">
      <text class="learn-title">学习中心</text>
      <view class="learn-header-stats">
        <text class="learn-credit">{{ credits }}学分</text>
      </view>
    </view>

    <!-- 快捷入口 -->
    <view class="learn-shortcuts">
      <view class="learn-shortcut" @tap="go('catalog')">
        <text class="learn-shortcut-icon">📂</text>
        <text class="learn-shortcut-text">课程目录</text>
      </view>
      <view class="learn-shortcut" @tap="go('my-learning')">
        <text class="learn-shortcut-icon">📖</text>
        <text class="learn-shortcut-text">我的学习</text>
      </view>
      <view class="learn-shortcut" @tap="go('credits')">
        <text class="learn-shortcut-icon">🏅</text>
        <text class="learn-shortcut-text">我的学分</text>
      </view>
    </view>

    <scroll-view scroll-y class="learn-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 推荐内容 -->
      <view class="learn-section">
        <view class="learn-section-header">
          <text class="learn-section-title">推荐内容</text>
        </view>

        <view v-if="items.length === 0 && !loading" class="learn-empty">
          <text class="learn-empty-icon">📚</text>
          <text class="learn-empty-text">暂无推荐内容</text>
        </view>

        <view v-for="item in items" :key="item.id" class="learn-card" @tap="openContent(item)">
          <image v-if="item.cover_url" :src="item.cover_url" class="learn-card-cover" mode="aspectFill" />
          <view v-else class="learn-card-cover learn-card-cover--placeholder">
            <text>{{ typeIcon(item.type) }}</text>
          </view>
          <view class="learn-card-body">
            <view class="learn-card-tags">
              <text class="learn-tag learn-tag--type">{{ typeLabel(item.type) }}</text>
              <text v-if="item.domain" class="learn-tag learn-tag--domain">{{ item.domain }}</text>
            </view>
            <text class="learn-card-title">{{ item.title }}</text>
            <view class="learn-card-meta">
              <text class="learn-card-views">👁 {{ item.view_count || 0 }}</text>
              <text class="learn-card-likes">❤️ {{ item.like_count || 0 }}</text>
            </view>
          </view>
        </view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const BASE_URL = 'http://localhost:8000'
function getToken() { return uni.getStorageSync('access_token') || '' }

async function http<T = any>(url: string, opts: any = {}): Promise<T> {
  const { method = 'GET', data } = opts
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url, method, data,
      header: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/json' },
      success: (res: any) => {
        if (res.statusCode === 401) { uni.removeStorageSync('access_token'); uni.reLaunch({ url: '/pages/auth/login' }); reject(new Error('401')); return }
        res.statusCode < 300 ? resolve(res.data as T) : reject(new Error(`${res.statusCode}`))
      },
      fail: (e: any) => reject(e),
    })
  })
}

const items = ref<any[]>([])
const credits = ref(0)
const refreshing = ref(false)
const loading = ref(false)

async function loadData() {
  loading.value = true
  try {
    const [rec, cr] = await Promise.allSettled([
      http<any[]>('/api/v1/content/recommended'),
      http<any>('/api/v1/learning/credits'),
    ])
    if (rec.status === 'fulfilled') {
      items.value = Array.isArray(rec.value) ? rec.value : (rec.value?.items || [])
    }
    if (cr.status === 'fulfilled') {
      credits.value = cr.value?.total_credits ?? 0
    }
  } finally {
    loading.value = false
  }
}

function typeIcon(t: string): string {
  return { article: '📄', video: '🎬', audio: '🎧', course: '📚' }[t] || '📄'
}
function typeLabel(t: string): string {
  return { article: '文章', video: '视频', audio: '音频', course: '课程' }[t] || t
}

function go(page: string) {
  uni.navigateTo({ url: '/pages/learning/' + page })
}

function openContent(item: any) {
  if (item.type === 'video') {
    uni.navigateTo({ url: '/pages/learning/video-player?id=' + item.id })
  } else if (item.type === 'audio') {
    uni.navigateTo({ url: '/pages/learning/audio-player?id=' + item.id })
  } else {
    uni.navigateTo({ url: '/pages/learning/content-detail?id=' + item.id })
  }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
onMounted(() => { loadData() })
</script>

<style scoped>
.learn-page { min-height: 100vh; background: #F5F6FA; }

.learn-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 24rpx 32rpx;
  padding-top: calc(80rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%);
  color: #fff;
}
.learn-title { font-size: 38rpx; font-weight: 700; }
.learn-credit { font-size: 28rpx; font-weight: 600; }

.learn-shortcuts {
  display: flex; gap: 0;
  background: #fff; padding: 24rpx 32rpx;
  border-bottom: 1rpx solid #F0F0F0;
}
.learn-shortcut {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8rpx;
}
.learn-shortcut-icon { font-size: 40rpx; }
.learn-shortcut-text { font-size: 22rpx; color: #5B6B7F; }

.learn-scroll { height: calc(100vh - 280rpx); }

.learn-section { padding: 24rpx; }
.learn-section-header { display: flex; justify-content: space-between; margin-bottom: 16rpx; }
.learn-section-title { font-size: 30rpx; font-weight: 700; color: #2C3E50; }

.learn-card {
  display: flex; gap: 20rpx; background: #fff; border-radius: 16rpx;
  padding: 20rpx; margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04);
}
.learn-card-cover {
  width: 160rpx; height: 120rpx; border-radius: 12rpx; flex-shrink: 0; background: #EEF; overflow: hidden;
}
.learn-card-cover--placeholder {
  display: flex; align-items: center; justify-content: center; font-size: 48rpx; background: #E8F8F0;
}
.learn-card-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 8rpx; }
.learn-card-tags { display: flex; gap: 8rpx; flex-wrap: wrap; }
.learn-tag { font-size: 18rpx; padding: 2rpx 10rpx; border-radius: 8rpx; }
.learn-tag--type { background: #E8F8F0; color: #2D8E69; }
.learn-tag--domain { background: #EEF4FF; color: #3498DB; }
.learn-card-title { font-size: 26rpx; font-weight: 600; color: #2C3E50; line-height: 1.5; }
.learn-card-meta { display: flex; gap: 16rpx; }
.learn-card-views, .learn-card-likes { font-size: 20rpx; color: #8E99A4; }

.learn-empty { text-align: center; padding: 80rpx 0; }
.learn-empty-icon { display: block; font-size: 64rpx; margin-bottom: 16rpx; }
.learn-empty-text { font-size: 26rpx; color: #8E99A4; }
</style>
