<template>
  <view class="notif-page">
    <view class="notif-header">
      <text class="notif-header-title">消息</text>
      <text v-if="unreadTotal > 0" class="notif-mark-all" @tap="markAllRead">全部已读</text>
    </view>

    <scroll-view scroll-y class="notif-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <!-- 快捷入口 -->
      <view class="notif-shortcuts">
        <view class="notif-sc" @tap="goPage('/pages/coach/messages/index')">
          <view class="notif-sc-icon" style="background:#EEF6FF;">💬</view>
          <text class="notif-sc-label">学员消息</text>
          <view v-if="unreadStudents > 0" class="notif-sc-badge">{{ unreadStudents }}</view>
        </view>
        <view class="notif-sc" @tap="goPage('/pages/coach/flywheel/index')">
          <view class="notif-sc-icon" style="background:#FFF2F2;">📋</view>
          <text class="notif-sc-label">审核通知</text>
          <view v-if="unreadReview > 0" class="notif-sc-badge">{{ unreadReview }}</view>
        </view>
        <view class="notif-sc" @tap="goPage('/pages/coach/risk/index')">
          <view class="notif-sc-icon" style="background:#FFF8EE;">⚠️</view>
          <text class="notif-sc-label">风险提醒</text>
          <view v-if="unreadRisk > 0" class="notif-sc-badge">{{ unreadRisk }}</view>
        </view>
      </view>

      <!-- 通知列表 -->
      <view class="notif-section-title">最近通知</view>
      <view v-for="n in notifications" :key="n.id" class="notif-item" :class="{ 'notif-item--unread': !n.is_read }" @tap="openNotification(n)">
        <view class="notif-item-icon" :style="{ background: notifColor(n.type) }">{{ notifIcon(n.type) }}</view>
        <view class="notif-item-body">
          <text class="notif-item-title">{{ n.title }}</text>
          <text class="notif-item-desc">{{ n.content }}</text>
          <text class="notif-item-time">{{ formatTime(n.created_at) }}</text>
        </view>
        <view v-if="!n.is_read" class="notif-item-dot"></view>
      </view>
      <view v-if="notifications.length === 0" class="notif-empty">
        <text class="notif-empty-icon">📭</text>
        <text class="notif-empty-text">暂无新消息</text>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'

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
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail: (err: any) => reject(err)
    })
  })
}

const refreshing = ref(false)
const notifications = ref<any[]>([])

const unreadTotal = computed(() => notifications.value.filter(n => !n.is_read).length)
const unreadStudents = computed(() => notifications.value.filter(n => !n.is_read && n.type === 'message').length)
const unreadReview = computed(() => notifications.value.filter(n => !n.is_read && (n.type === 'review' || n.type === 'assessment')).length)
const unreadRisk = computed(() => notifications.value.filter(n => !n.is_read && (n.type === 'risk' || n.type === 'alert')).length)

function notifColor(type: string): string {
  const m: Record<string, string> = { system: '#3498DB', message: '#27AE60', review: '#E67E22', assessment: '#9B59B6', risk: '#E74C3C', alert: '#E74C3C', learning: '#1ABC9C' }
  return m[type] || '#8E99A4'
}
function notifIcon(type: string): string {
  const m: Record<string, string> = { system: '🔔', message: '💬', review: '📋', assessment: '📊', risk: '⚠️', alert: '🚨', learning: '📚' }
  return m[type] || '📩'
}
function formatTime(t: string): string {
  if (!t) return ''
  const d = new Date(t)
  const diff = Date.now() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return (d.getMonth()+1) + '/' + d.getDate()
}

async function loadData() {
  try {
    const res = await http<any>('/api/v1/notifications?page_size=50')
    notifications.value = res.items || res.notifications || (Array.isArray(res) ? res : [])
  } catch { notifications.value = [] }
}

async function markAllRead() {
  try { await http('/api/v1/notifications/mark-all-read', { method: 'POST' }) } catch {}
  notifications.value.forEach(n => n.is_read = true)
}

function openNotification(n: any) {
  if (!n.is_read) {
    n.is_read = true
    http('/api/v1/notifications/' + n.id + '/read', { method: 'POST' }).catch(() => {})
  }
  if (n.link) uni.navigateTo({ url: n.link })
}

function goPage(url: string) {
  uni.navigateTo({ url })
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }

onShow(() => { loadData() })
onMounted(() => { loadData() })
</script>

<style scoped>
.notif-page { min-height: 100vh; background: #F5F6FA; }
.notif-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16rpx 32rpx; padding-top: calc(80rpx + env(safe-area-inset-top));
  background: #fff;
}
.notif-header-title { font-size: 38rpx; font-weight: 700; color: #2C3E50; }
.notif-mark-all { font-size: 26rpx; color: #3498DB; }

.notif-scroll { height: calc(100vh - 200rpx); }

.notif-shortcuts { display: flex; gap: 16rpx; padding: 24rpx; }
.notif-sc { position: relative; flex: 1; background: #fff; border-radius: 16rpx; padding: 24rpx 12rpx; display: flex; flex-direction: column; align-items: center; gap: 8rpx; }
.notif-sc-icon { width: 72rpx; height: 72rpx; border-radius: 16rpx; display: flex; align-items: center; justify-content: center; font-size: 36rpx; }
.notif-sc-label { font-size: 24rpx; color: #5B6B7F; }
.notif-sc-badge { position: absolute; top: 8rpx; right: 16rpx; min-width: 28rpx; height: 28rpx; border-radius: 14rpx; background: #E74C3C; color: #fff; font-size: 18rpx; display: flex; align-items: center; justify-content: center; padding: 0 6rpx; }

.notif-section-title { padding: 8rpx 32rpx 16rpx; font-size: 26rpx; color: #8E99A4; font-weight: 600; }

.notif-item { display: flex; align-items: flex-start; gap: 16rpx; background: #fff; padding: 24rpx; margin: 0 24rpx 2rpx; }
.notif-item:first-of-type { border-radius: 16rpx 16rpx 0 0; }
.notif-item:last-of-type { border-radius: 0 0 16rpx 16rpx; margin-bottom: 16rpx; }
.notif-item--unread { background: #FAFCFF; }
.notif-item-icon { width: 56rpx; height: 56rpx; border-radius: 12rpx; display: flex; align-items: center; justify-content: center; font-size: 28rpx; flex-shrink: 0; }
.notif-item-body { flex: 1; }
.notif-item-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.notif-item-desc { display: block; font-size: 24rpx; color: #5B6B7F; margin-top: 6rpx; line-height: 1.5; }
.notif-item-time { display: block; font-size: 22rpx; color: #BDC3C7; margin-top: 8rpx; }
.notif-item-dot { width: 12rpx; height: 12rpx; border-radius: 50%; background: #E74C3C; margin-top: 8rpx; flex-shrink: 0; }

.notif-empty { text-align: center; padding: 120rpx 0; }
.notif-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.notif-empty-text { font-size: 28rpx; color: #8E99A4; }
</style>