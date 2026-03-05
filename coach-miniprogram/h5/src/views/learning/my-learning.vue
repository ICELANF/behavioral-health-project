<template>
  <view class="ml-page">
    <scroll-view scroll-y class="ml-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <view class="ml-summary">
        <view class="ml-stat-item">
          <text class="ml-stat-num">{{ summary.total }}</text>
          <text class="ml-stat-label">已学内容</text>
        </view>
        <view class="ml-stat-item">
          <text class="ml-stat-num">{{ summary.completed }}</text>
          <text class="ml-stat-label">已完成</text>
        </view>
        <view class="ml-stat-item">
          <text class="ml-stat-num">{{ summary.credits }}</text>
          <text class="ml-stat-label">获得学分</text>
        </view>
      </view>

      <view class="ml-list">
        <view v-for="item in records" :key="item.id" class="ml-card" @tap="openContent(item)">
          <view class="ml-card-left">
            <view class="ml-icon-wrap" :class="'ml-icon-wrap--' + item.content_type">
              <text>{{ typeIcon(item.content_type) }}</text>
            </view>
          </view>
          <view class="ml-card-body">
            <text class="ml-card-title">{{ item.title || item.content_title || '学习内容' }}</text>
            <text class="ml-card-time">{{ formatTime(item.updated_at || item.created_at) }}</text>
          </view>
          <view class="ml-card-right">
            <view class="ml-progress-badge" :class="item.completed ? 'ml-badge--done' : 'ml-badge--ing'">
              {{ item.completed ? '已完成' : '学习中' }}
            </view>
          </view>
        </view>
      </view>

      <view v-if="records.length === 0 && !loading" class="ml-empty">
        <text class="ml-empty-icon">📖</text>
        <text class="ml-empty-text">还没有学习记录</text>
        <view class="ml-start-btn" @tap="goLearn">
          <text>开始学习</text>
        </view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

interface MyLearning { id: number; title?: string; content_title?: string; content_type?: string; completed?: boolean; progress?: number; updated_at?: string; created_at?: string }

const records = ref<MyLearning[]>([])
const summary = ref({ total: 0, completed: 0, credits: 0 })
const refreshing = ref(false)
const loading = ref(false)

async function loadData() {
  loading.value = true
  try {
    const [myRes, crRes] = await Promise.allSettled([
      http<any>('/api/v1/learning/my'),
      http<any>('/api/v1/learning/credits'),
    ])
    if (myRes.status === 'fulfilled') {
      records.value = myRes.value?.items || []
      summary.value.total = myRes.value?.total || records.value.length
      summary.value.completed = records.value.filter((r: any) => r.completed).length
    }
    if (crRes.status === 'fulfilled') {
      summary.value.credits = crRes.value?.total_credits ?? 0
    }
  } finally { loading.value = false }
}

function typeIcon(t: string) { return { article: '📄', video: '🎬', audio: '🎧', course: '📚' }[t] || '📄' }

function formatTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso), now = new Date()
  const diff = Math.floor((now.getTime() - d.getTime()) / 1000)
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  return Math.floor(diff / 86400) + '天前'
}

function openContent(item: any) {
  if (item.content_id) uni.navigateTo({ url: '/learning/content-detail?id=' + item.content_id })
}

function goLearn() { uni.navigateBack({ fail: () => uni.navigateTo({ url: '/learning/index' }) }) }

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
onMounted(() => { loadData() })
</script>

<style scoped>
.ml-page { min-height: 100vh; background: #F5F6FA; }
.ml-scroll { height: 100vh; }

.ml-summary { display: flex; background: #fff; padding: 24rpx 0; margin-bottom: 16rpx; }
.ml-stat-item { flex: 1; text-align: center; border-right: 1rpx solid #F0F0F0; }
.ml-stat-item:last-child { border-right: none; }
.ml-stat-num { display: block; font-size: 40rpx; font-weight: 700; color: #2D8E69; }
.ml-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.ml-list { padding: 0 24rpx; }
.ml-card { display: flex; align-items: center; gap: 16rpx; background: #fff; border-radius: 16rpx; padding: 20rpx 24rpx; margin-bottom: 12rpx; }
.ml-card-left { flex-shrink: 0; }
.ml-icon-wrap { width: 64rpx; height: 64rpx; border-radius: 16rpx; display: flex; align-items: center; justify-content: center; font-size: 32rpx; background: #E8F8F0; }
.ml-card-body { flex: 1; min-width: 0; }
.ml-card-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 6rpx; }
.ml-card-time { font-size: 22rpx; color: #8E99A4; }
.ml-card-right { flex-shrink: 0; }
.ml-progress-badge { font-size: 20rpx; padding: 4rpx 12rpx; border-radius: 8rpx; }
.ml-badge--done { background: #E8F8F0; color: #2D8E69; }
.ml-badge--ing { background: #FEF5E7; color: #E67E22; }

.ml-empty { text-align: center; padding: 100rpx 0; }
.ml-empty-icon { display: block; font-size: 64rpx; margin-bottom: 16rpx; }
.ml-empty-text { display: block; font-size: 26rpx; color: #8E99A4; margin-bottom: 32rpx; }
.ml-start-btn { display: inline-block; padding: 16rpx 48rpx; background: #2D8E69; color: #fff; border-radius: 16rpx; font-size: 28rpx; }
</style>
