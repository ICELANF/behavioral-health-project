<template>
  <view class="cat-page">
    <scroll-view scroll-y class="cat-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 类型筛选 -->
      <scroll-view scroll-x class="cat-filter-bar">
        <view v-for="f in filters" :key="f.key"
          class="cat-filter-tag" :class="{ 'cat-filter-tag--active': activeFilter === f.key }"
          @tap="activeFilter = f.key">
          {{ f.label }}
        </view>
      </scroll-view>

      <view class="cat-list">
        <view v-for="item in filteredItems" :key="item.id" class="cat-card" @tap="openContent(item)">
          <image v-if="item.cover_url" :src="item.cover_url" class="cat-cover" mode="aspectFill" />
          <view v-else class="cat-cover cat-cover--ph">
            <text>{{ typeIcon(item.type) }}</text>
          </view>
          <view class="cat-info">
            <view class="cat-tags">
              <text class="cat-tag cat-tag--type">{{ typeLabel(item.type) }}</text>
              <text v-if="item.level" class="cat-tag cat-tag--level">L{{ item.level }}</text>
            </view>
            <text class="cat-title">{{ item.title }}</text>
            <view class="cat-stats">
              <text class="cat-stat">👁 {{ item.view_count || 0 }}</text>
              <text class="cat-stat">❤️ {{ item.like_count || 0 }}</text>
            </view>
          </view>
        </view>
      </view>

      <view v-if="filteredItems.length === 0 && !loading" class="cat-empty">
        <text class="cat-empty-icon">📭</text>
        <text class="cat-empty-text">暂无内容</text>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const items = ref<any[]>([])
const activeFilter = ref('all')
const refreshing = ref(false)
const loading = ref(false)

const filters = [
  { key: 'all', label: '全部' },
  { key: 'article', label: '文章' },
  { key: 'video', label: '视频' },
  { key: 'audio', label: '音频' },
]

const filteredItems = computed(() => {
  if (activeFilter.value === 'all') return items.value
  return items.value.filter(i => i.type === activeFilter.value)
})

function typeIcon(t: string) {
  return { article: '📄', video: '🎬', audio: '🎧' }[t] || '📄'
}
function typeLabel(t: string) {
  return { article: '文章', video: '视频', audio: '音频' }[t] || t
}

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/content/recommended')
    items.value = Array.isArray(res) ? res : (res?.items || [])
  } catch { items.value = [] } finally { loading.value = false }
}

function openContent(item: any) {
  if (item.type === 'video') uni.navigateTo({ url: '/pages/learning/video-player?id=' + item.id })
  else if (item.type === 'audio') uni.navigateTo({ url: '/pages/learning/audio-player?id=' + item.id })
  else uni.navigateTo({ url: '/pages/learning/content-detail?id=' + item.id })
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
onMounted(() => { loadData() })
</script>

<style scoped>
.cat-page { min-height: 100vh; background: #F5F6FA; }
.cat-scroll { height: 100vh; }

.cat-filter-bar { display: flex; white-space: nowrap; background: #fff; padding: 16rpx 24rpx; border-bottom: 1rpx solid #F0F0F0; }
.cat-filter-tag { display: inline-flex; align-items: center; padding: 12rpx 28rpx; border-radius: 24rpx; font-size: 24rpx; color: #8E99A4; margin-right: 12rpx; background: #F5F6FA; }
.cat-filter-tag--active { background: #2D8E69; color: #fff; }

.cat-list { padding: 16rpx 24rpx; }
.cat-card { display: flex; gap: 16rpx; background: #fff; border-radius: 16rpx; padding: 20rpx; margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.03); }
.cat-cover { width: 150rpx; height: 110rpx; border-radius: 12rpx; flex-shrink: 0; background: #E8F8F0; overflow: hidden; }
.cat-cover--ph { display: flex; align-items: center; justify-content: center; font-size: 48rpx; }
.cat-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 8rpx; }
.cat-tags { display: flex; gap: 8rpx; }
.cat-tag { font-size: 18rpx; padding: 2rpx 10rpx; border-radius: 8rpx; }
.cat-tag--type { background: #E8F8F0; color: #2D8E69; }
.cat-tag--level { background: #FEF5E7; color: #E67E22; }
.cat-title { font-size: 26rpx; font-weight: 600; color: #2C3E50; line-height: 1.5; }
.cat-stats { display: flex; gap: 16rpx; }
.cat-stat { font-size: 20rpx; color: #8E99A4; }

.cat-empty { text-align: center; padding: 100rpx 0; }
.cat-empty-icon { display: block; font-size: 64rpx; margin-bottom: 16rpx; }
.cat-empty-text { font-size: 26rpx; color: #8E99A4; }
</style>
