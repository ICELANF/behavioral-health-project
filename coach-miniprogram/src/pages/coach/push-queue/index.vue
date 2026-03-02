<template>
  <view class="pq-page">
    <view class="pq-navbar">
      <view class="pq-nav-back" @tap="goBack">←</view>
      <text class="pq-nav-title">推送队列</text>
      <view class="pq-nav-action" @tap="refresh">↻</view>
    </view>

    <!-- 统计 -->
    <view class="pq-stats">
      <view class="pq-stat">
        <text class="pq-stat-num" style="color:#E67E22;">{{ pendingCount }}</text>
        <text class="pq-stat-label">待推送</text>
      </view>
      <view class="pq-stat">
        <text class="pq-stat-num" style="color:#27AE60;">{{ sentToday }}</text>
        <text class="pq-stat-label">今日已推</text>
      </view>
      <view class="pq-stat">
        <text class="pq-stat-num" style="color:#3498DB;">{{ totalStudents }}</text>
        <text class="pq-stat-label">覆盖学员</text>
      </view>
    </view>

    <!-- Tab -->
    <view class="pq-tabs">
      <view v-for="t in queueTabs" :key="t.key" class="pq-tab" :class="{ 'pq-tab--active': activeTab === t.key }" @tap="activeTab = t.key">
        {{ t.label }}
        <view v-if="t.count > 0" class="pq-tab-badge">{{ t.count }}</view>
      </view>
    </view>

    <!-- 队列列表 -->
    <scroll-view scroll-y class="pq-list" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view v-for="item in filteredItems" :key="item.id" class="pq-card">
        <view class="pq-card-header">
          <view class="pq-card-avatar">{{ (item.student_name || '?')[0] }}</view>
          <view class="pq-card-info">
            <text class="pq-card-name">{{ item.student_name }}</text>
            <text class="pq-card-type">{{ item.type_label }}</text>
          </view>
          <view class="pq-card-status" :style="{ background: statusColor(item.status) }">
            {{ statusLabel(item.status) }}
          </view>
        </view>
        <text class="pq-card-content">{{ item.content || item.ai_summary || '—' }}</text>
        <view class="pq-card-footer">
          <text class="pq-card-time">{{ item.scheduled_at || item.created_at || '' }}</text>
          <view v-if="item.status === 'pending'" class="pq-card-actions">
            <view class="pq-btn pq-btn--send" @tap="sendPush(item)">发送</view>
            <view class="pq-btn pq-btn--cancel" @tap="cancelPush(item)">取消</view>
          </view>
        </view>
      </view>

      <view v-if="filteredItems.length === 0" class="pq-empty">
        <text class="pq-empty-icon">📤</text>
        <text class="pq-empty-text">{{ activeTab === 'pending' ? '无待推送任务' : '暂无记录' }}</text>
      </view>
    </scroll-view>
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

const activeTab = ref('pending')
const refreshing = ref(false)
const queueItems = ref<any[]>([])

const pendingCount = computed(() => queueItems.value.filter(i => i.status === 'pending').length)
const sentToday = computed(() => queueItems.value.filter(i => i.status === 'sent' || i.status === 'approved').length)
const totalStudents = computed(() => new Set(queueItems.value.map(i => i.student_id)).size)

const queueTabs = computed(() => [
  { key: 'pending', label: '待推送', count: pendingCount.value },
  { key: 'sent', label: '已推送', count: sentToday.value },
  { key: 'all', label: '全部', count: queueItems.value.length },
])

const filteredItems = computed(() => {
  if (activeTab.value === 'all') return queueItems.value
  return queueItems.value.filter(i => i.status === activeTab.value)
})

function statusColor(s: string): string {
  const m: Record<string, string> = { pending: '#E67E22', sent: '#27AE60', cancelled: '#BDC3C7', failed: '#E74C3C' }
  return m[s] || '#8E99A4'
}
function statusLabel(s: string): string {
  const m: Record<string, string> = { pending: '待推送', sent: '已推送', cancelled: '已取消', failed: '失败' }
  return m[s] || s
}

const SOURCE_LABELS: Record<string, string> = {
  rx_push: '处方推送', reminder: '提醒', assessment: '评估邀请',
  ai_recommendation: 'AI推荐', content: '内容推送', system: '系统通知',
  coach_message: '消息推送', challenge: '挑战任务',
}

async function loadData() {
  try {
    // Fetch all statuses: pending + approved/sent for history tabs
    const [pendingRes, sentRes] = await Promise.allSettled([
      http<any>('/api/v1/coach/push-queue?page_size=50&status=pending'),
      http<any>('/api/v1/coach/push-queue?page_size=50&status=approved'),
    ])
    const allItems: any[] = []
    if (pendingRes.status === 'fulfilled') allItems.push(...(pendingRes.value.items || []))
    if (sentRes.status === 'fulfilled')    allItems.push(...(sentRes.value.items || []))

    queueItems.value = allItems.map((i: any) => ({
      id: i.id,
      student_id: i.student_id,
      student_name: i.student_name || i.grower_name || '学员',
      type_label: SOURCE_LABELS[i.source_type] || SOURCE_LABELS[i.type] || '消息推送',
      content: i.content || i.ai_summary || i.title || '',
      status: i.status === 'approved' ? 'sent' : (i.status || 'pending'),
      scheduled_at: i.scheduled_time || i.scheduled_at || '',
      created_at: i.created_at || '',
    }))
  } catch {
    queueItems.value = []
  }
}

async function sendPush(item: any) {
  try {
    await http('/api/v1/coach/push-queue/' + item.id + '/approve', { method: 'POST', data: {} })
    item.status = 'sent'
    uni.showToast({ title: '已发送', icon: 'success' })
  } catch {
    uni.showToast({ title: '发送失败', icon: 'none' })
  }
}

async function cancelPush(item: any) {
  try {
    await http('/api/v1/coach/push-queue/' + item.id + '/reject', { method: 'POST', data: {} })
    item.status = 'cancelled'
    uni.showToast({ title: '已取消', icon: 'success' })
  } catch {
    uni.showToast({ title: '取消失败', icon: 'none' })
  }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
function refresh() { loadData() }
function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.pq-page { min-height: 100vh; background: #F5F6FA; }
.pq-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #E67E22 0%, #F39C12 100%); color: #fff; }
.pq-nav-back { font-size: 40rpx; padding: 16rpx; }
.pq-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.pq-nav-action { font-size: 36rpx; padding: 16rpx; }

.pq-stats { display: flex; padding: 20rpx 24rpx; gap: 16rpx; }
.pq-stat { flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx; text-align: center; }
.pq-stat-num { display: block; font-size: 44rpx; font-weight: 700; }
.pq-stat-label { display: block; font-size: 22rpx; color: #8E99A4; }

.pq-tabs { display: flex; padding: 0 24rpx; gap: 12rpx; margin-bottom: 16rpx; }
.pq-tab { position: relative; flex: 1; text-align: center; padding: 14rpx 0; background: #fff; border-radius: 12rpx; font-size: 26rpx; color: #5B6B7F; }
.pq-tab--active { background: #E67E22; color: #fff; }
.pq-tab-badge { position: absolute; top: -8rpx; right: 12rpx; min-width: 28rpx; height: 28rpx; border-radius: 14rpx; background: #E74C3C; color: #fff; font-size: 18rpx; display: flex; align-items: center; justify-content: center; padding: 0 6rpx; }

.pq-list { height: calc(100vh - 480rpx); padding: 0 24rpx; }
.pq-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; }
.pq-card-header { display: flex; align-items: center; gap: 12rpx; margin-bottom: 12rpx; }
.pq-card-avatar { width: 56rpx; height: 56rpx; border-radius: 50%; background: #3498DB; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 600; }
.pq-card-info { flex: 1; }
.pq-card-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.pq-card-type { display: block; font-size: 22rpx; color: #8E99A4; }
.pq-card-status { padding: 6rpx 16rpx; border-radius: 8rpx; color: #fff; font-size: 22rpx; }
.pq-card-content { display: block; font-size: 26rpx; color: #5B6B7F; line-height: 1.5; margin-bottom: 12rpx; }
.pq-card-footer { display: flex; justify-content: space-between; align-items: center; }
.pq-card-time { font-size: 22rpx; color: #BDC3C7; }
.pq-card-actions { display: flex; gap: 12rpx; }
.pq-btn { padding: 10rpx 24rpx; border-radius: 8rpx; font-size: 24rpx; font-weight: 600; }
.pq-btn--send { background: #27AE60; color: #fff; }
.pq-btn--cancel { background: #F0F0F0; color: #5B6B7F; }

.pq-empty { text-align: center; padding: 120rpx 0; }
.pq-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.pq-empty-text { font-size: 28rpx; color: #8E99A4; }
</style>