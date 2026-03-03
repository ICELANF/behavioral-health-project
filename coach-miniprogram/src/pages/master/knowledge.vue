<template>
  <view class="kb-page">
    <view class="kb-navbar">
      <view class="kb-back" @tap="goBack">←</view>
      <text class="kb-title">知识库管理</text>
      <view class="kb-refresh" @tap="loadData">↻</view>
    </view>
    <scroll-view scroll-y class="kb-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view class="kb-stat-row">
        <view class="kb-stat"><text class="kb-stat-num" style="color:#9B59B6;">{{ items.length }}</text><text class="kb-stat-label">待审发布</text></view>
        <view class="kb-stat"><text class="kb-stat-num" style="color:#27AE60;">{{ publishedToday }}</text><text class="kb-stat-label">今日发布</text></view>
        <view class="kb-stat"><text class="kb-stat-num" style="color:#E74C3C;">{{ rejectedToday }}</text><text class="kb-stat-label">今日拒绝</text></view>
      </view>

      <view v-for="item in items" :key="item.id" class="kb-card">
        <view class="kb-card-header">
          <view class="kb-category-tag" :style="{ background: categoryBg(item.category), color: categoryColor(item.category) }">
            {{ item.category || '未分类' }}
          </view>
          <text class="kb-card-date">{{ formatDate(item.created_at) }}</text>
        </view>
        <text class="kb-card-title">{{ item.title }}</text>
        <view class="kb-status-row">
          <view class="kb-status-dot" :style="{ background: statusColor(item.status) }"></view>
          <text class="kb-status-text">{{ statusLabel(item.status) }}</text>
        </view>
        <view class="kb-card-actions">
          <view
            class="kb-btn kb-btn--publish"
            :class="{ 'kb-btn--loading': processingIds.has(item.id) }"
            @tap="publishItem(item)"
          >{{ processingIds.has(item.id) ? '…' : '发布' }}</view>
          <view class="kb-btn kb-btn--reject" @tap="rejectItem(item)">拒绝</view>
        </view>
      </view>

      <view v-if="!loading && items.length === 0" class="kb-empty">
        <text class="kb-empty-icon">📚</text>
        <text class="kb-empty-text">暂无待审知识内容</text>
        <text class="kb-empty-hint">所有知识条目均已处理完毕</text>
      </view>
      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const BASE_URL = 'http://localhost:8000'

function getToken(): string {
  return uni.getStorageSync('access_token') || ''
}

async function http<T = any>(url: string, opts: any = {}): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method: opts.method || 'GET',
      data: opts.data,
      header: {
        'Authorization': 'Bearer ' + getToken(),
        'Content-Type': 'application/json',
      },
      success: (res: any) => {
        if (res.statusCode === 401) {
          uni.removeStorageSync('access_token')
          uni.reLaunch({ url: '/pages/auth/login' })
          reject(new Error('401'))
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail: reject,
    })
  })
}

const loading = ref(false)
const refreshing = ref(false)
const items = ref<any[]>([])
const processingIds = ref<Set<string>>(new Set())
const publishedToday = ref(0)
const rejectedToday = ref(0)

const categoryColors: Record<string, string> = {
  nutrition: '#27AE60', exercise: '#3498DB', psychology: '#9B59B6',
  tcm: '#E67E22', lifestyle: '#1ABC9C',
}
const categoryBgs: Record<string, string> = {
  nutrition: '#E8F8F0', exercise: '#EEF6FF', psychology: '#F5EEF8',
  tcm: '#FFF7F0', lifestyle: '#E8FAF5',
}
function categoryColor(cat: string): string { return categoryColors[cat] || '#8E99A4' }
function categoryBg(cat: string): string { return categoryBgs[cat] || '#F5F5F5' }
function statusLabel(s: string): string {
  const m: Record<string, string> = { pending_review: '待审核', draft: '草稿', published: '已发布', rejected: '已拒绝' }
  return m[s] || s
}
function statusColor(s: string): string {
  const m: Record<string, string> = { pending_review: '#E67E22', draft: '#8E99A4', published: '#27AE60', rejected: '#E74C3C' }
  return m[s] || '#BDC3C7'
}
function formatDate(t: string): string {
  return t ? new Date(t).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }) : ''
}

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>('/api/v1/knowledge/items?status=pending_review')
    items.value = res.items || res || []
  } catch {
    items.value = []
  }
  loading.value = false
}

async function publishItem(item: any) {
  if (processingIds.value.has(item.id)) return
  processingIds.value.add(item.id)
  try {
    await http(`/api/v1/knowledge/items/${item.id}/publish`, { method: 'POST', data: {} })
    uni.showToast({ title: '已发布', icon: 'success' })
    publishedToday.value++
    await loadData()
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    processingIds.value.delete(item.id)
  }
}

async function rejectItem(item: any) {
  if (processingIds.value.has(item.id)) return
  processingIds.value.add(item.id)
  try {
    await http(`/api/v1/knowledge/items/${item.id}/reject`, { method: 'POST', data: {} })
    uni.showToast({ title: '已拒绝', icon: 'success' })
    rejectedToday.value++
    await loadData()
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    processingIds.value.delete(item.id)
  }
}

async function onRefresh() {
  refreshing.value = true
  await loadData()
  refreshing.value = false
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => loadData())
</script>

<style scoped>
.kb-page { min-height: 100vh; background: #F5F6FA; }
.kb-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #7D3C98, #9B59B6); color: #fff;
}
.kb-back { font-size: 40rpx; padding: 16rpx; }
.kb-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.kb-refresh { font-size: 40rpx; padding: 16rpx; }
.kb-scroll { height: calc(100vh - 180rpx); }
.kb-stat-row { display: flex; margin: 24rpx; gap: 16rpx; }
.kb-stat { flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx; text-align: center; }
.kb-stat-num { display: block; font-size: 40rpx; font-weight: 700; color: #2C3E50; }
.kb-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.kb-card { margin: 0 24rpx 12rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
.kb-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.kb-category-tag { padding: 4rpx 16rpx; border-radius: 20rpx; font-size: 22rpx; font-weight: 600; }
.kb-card-date { font-size: 22rpx; color: #8E99A4; }
.kb-card-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; line-height: 1.5; margin-bottom: 12rpx; }
.kb-status-row { display: flex; align-items: center; gap: 8rpx; margin-bottom: 20rpx; }
.kb-status-dot { width: 12rpx; height: 12rpx; border-radius: 50%; }
.kb-status-text { font-size: 22rpx; color: #8E99A4; }
.kb-card-actions { display: flex; gap: 16rpx; }
.kb-btn { flex: 1; text-align: center; padding: 18rpx 0; border-radius: 12rpx; font-size: 28rpx; font-weight: 600; }
.kb-btn--publish { background: #9B59B6; color: #fff; }
.kb-btn--reject { background: #FFF0F0; color: #E74C3C; }
.kb-btn--loading { background: #BDC3C7; color: #fff; }
.kb-empty { text-align: center; padding: 120rpx 0; }
.kb-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.kb-empty-text { display: block; font-size: 30rpx; color: #5B6B7F; }
.kb-empty-hint { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 8rpx; }
</style>
