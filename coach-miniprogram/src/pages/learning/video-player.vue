<template>
  <view class="vp-page">
    <!-- 视频播放器 -->
    <view class="vp-video-wrap">
      <video v-if="videoUrl" :src="videoUrl" class="vp-video"
        controls autoplay :title="title" />
      <view v-else class="vp-video-ph">
        <text class="vp-ph-icon">🎬</text>
        <text class="vp-ph-text">{{ loading ? '视频加载中...' : '视频暂不可用' }}</text>
      </view>
    </view>

    <scroll-view scroll-y class="vp-info">
      <view class="vp-title-row">
        <text class="vp-title">{{ title }}</text>
      </view>
      <view class="vp-meta">
        <text v-if="author" class="vp-author">{{ author }}</text>
        <text class="vp-views">👁 {{ viewCount }}</text>
      </view>
      <view class="vp-divider" />
      <rich-text v-if="description" :nodes="description" class="vp-desc" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const videoUrl = ref('')
const title = ref('视频学习')
const author = ref('')
const viewCount = ref(0)
const description = ref('')
const loading = ref(false)

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  const id = Number(page?.options?.id || 0)
  if (!id) return
  loading.value = true
  try {
    const data = await http<any>(`/api/v1/content/${id}`)
    videoUrl.value = data?.media_url || ''
    title.value = data?.title || '视频学习'
    author.value = data?.author?.name || ''
    viewCount.value = data?.view_count || 0
    description.value = data?.subtitle || ''
  } catch (e) { console.warn('[learning/video-player] operation:', e) } finally { loading.value = false }
})
</script>

<style scoped>
.vp-page { min-height: 100vh; background: #000; display: flex; flex-direction: column; }
.vp-video-wrap { width: 100%; background: #000; }
.vp-video { width: 100%; height: 420rpx; display: block; }
.vp-video-ph { height: 420rpx; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16rpx; }
.vp-ph-icon { font-size: 64rpx; }
.vp-ph-text { font-size: 26rpx; color: #8E99A4; }
.vp-info { flex: 1; background: #fff; height: calc(100vh - 420rpx); padding: 24rpx; }
.vp-title-row { margin-bottom: 12rpx; }
.vp-title { font-size: 32rpx; font-weight: 700; color: #2C3E50; line-height: 1.4; }
.vp-meta { display: flex; gap: 20rpx; margin-bottom: 20rpx; }
.vp-author { font-size: 24rpx; color: #5B6B7F; }
.vp-views { font-size: 24rpx; color: #8E99A4; }
.vp-divider { height: 1rpx; background: #F0F0F0; margin-bottom: 20rpx; }
.vp-desc { font-size: 26rpx; color: #5B6B7F; line-height: 1.8; }
</style>
