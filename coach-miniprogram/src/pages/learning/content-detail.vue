<template>
  <view class="cd-page">
    <view v-if="loading" class="cd-loading"><text>加载中...</text></view>

    <view v-else-if="item">
      <image v-if="item.cover_url" :src="item.cover_url" class="cd-cover" mode="aspectFill" />
      <view v-else class="cd-cover cd-cover--ph"><text>{{ typeIcon(item.type) }}</text></view>

      <view class="cd-body">
        <view class="cd-tags">
          <text class="cd-tag cd-tag--type">{{ typeLabel(item.type) }}</text>
          <text v-if="item.domain" class="cd-tag cd-tag--domain">{{ item.domain }}</text>
          <text v-if="item.level" class="cd-tag cd-tag--level">L{{ item.level }}</text>
        </view>
        <text class="cd-title">{{ item.title }}</text>
        <view class="cd-meta">
          <text class="cd-author">{{ item.author?.name || '官方' }}</text>
          <text class="cd-stat">👁 {{ item.view_count || 0 }}</text>
          <text class="cd-stat">❤️ {{ item.like_count || 0 }}</text>
        </view>
        <view v-if="item.type === 'video'" class="cd-play-btn" @tap="playMedia"><text>▶ 观看视频</text></view>
        <view v-else-if="item.type === 'audio'" class="cd-play-btn" @tap="playMedia"><text>🎧 收听音频</text></view>
        <view class="cd-divider" />
        <rich-text v-if="item.subtitle" :nodes="item.subtitle" class="cd-richtext" />
        <text v-else class="cd-richtext cd-richtext--empty">暂无详细内容</text>
      </view>
    </view>

    <view v-else class="cd-error">
      <text class="cd-error-icon">😕</text>
      <text class="cd-error-text">内容加载失败</text>
      <view class="cd-retry" @tap="loadData"><text>重试</text></view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const BASE_URL = 'http://localhost:8000'
function getToken() { return uni.getStorageSync('access_token') || '' }

async function http<T = any>(url: string, opts: any = {}): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url, method: opts.method || 'GET', data: opts.data,
      header: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/json' },
      success: (res: any) => {
        if (res.statusCode === 401) { uni.removeStorageSync('access_token'); uni.reLaunch({ url: '/pages/auth/login' }); reject(new Error('401')); return }
        res.statusCode < 300 ? resolve(res.data as T) : reject(new Error(`${res.statusCode}`))
      },
      fail: (e: any) => reject(e),
    })
  })
}

const item = ref<any>(null)
const loading = ref(false)
let contentId = 0

onMounted(() => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  contentId = Number(page?.options?.id || 0)
  if (contentId) loadData()
})

async function loadData() {
  loading.value = true
  try { item.value = await http<any>(`/api/v1/content/${contentId}`) }
  catch { item.value = null } finally { loading.value = false }
}

function typeIcon(t: string) { return { article: '📄', video: '🎬', audio: '🎧' }[t] || '📄' }
function typeLabel(t: string) { return { article: '文章', video: '视频', audio: '音频' }[t] || t }
function playMedia() {
  if (item.value?.type === 'video') uni.navigateTo({ url: '/pages/learning/video-player?id=' + contentId })
  else uni.navigateTo({ url: '/pages/learning/audio-player?id=' + contentId })
}
</script>

<style scoped>
.cd-page { min-height: 100vh; background: #F5F6FA; }
.cd-loading { display: flex; align-items: center; justify-content: center; height: 100vh; font-size: 28rpx; color: #8E99A4; }
.cd-cover { width: 100%; height: 400rpx; display: block; }
.cd-cover--ph { display: flex; align-items: center; justify-content: center; font-size: 80rpx; background: #E8F8F0; height: 400rpx; }
.cd-body { padding: 32rpx; background: #fff; }
.cd-tags { display: flex; gap: 8rpx; margin-bottom: 16rpx; flex-wrap: wrap; }
.cd-tag { font-size: 20rpx; padding: 4rpx 12rpx; border-radius: 8rpx; }
.cd-tag--type { background: #E8F8F0; color: #2D8E69; }
.cd-tag--domain { background: #EEF4FF; color: #3498DB; }
.cd-tag--level { background: #FEF5E7; color: #E67E22; }
.cd-title { display: block; font-size: 36rpx; font-weight: 700; color: #2C3E50; margin-bottom: 16rpx; line-height: 1.4; }
.cd-meta { display: flex; gap: 20rpx; margin-bottom: 24rpx; }
.cd-author { font-size: 24rpx; color: #5B6B7F; }
.cd-stat { font-size: 24rpx; color: #8E99A4; }
.cd-play-btn { background: #2D8E69; border-radius: 16rpx; padding: 20rpx; text-align: center; color: #fff; font-size: 30rpx; font-weight: 600; margin-bottom: 24rpx; }
.cd-divider { height: 1rpx; background: #F0F0F0; margin: 24rpx 0; }
.cd-richtext { font-size: 28rpx; color: #2C3E50; line-height: 1.8; }
.cd-richtext--empty { color: #8E99A4; }
.cd-error { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; gap: 16rpx; }
.cd-error-icon { font-size: 80rpx; }
.cd-error-text { font-size: 28rpx; color: #8E99A4; }
.cd-retry { padding: 16rpx 48rpx; border-radius: 16rpx; border: 1rpx solid #2D8E69; color: #2D8E69; font-size: 26rpx; margin-top: 16rpx; }
</style>
