<template>
  <view class="notif-page">
    <view class="notif-header">
      <text class="notif-title">消息中心</text>
      <text class="notif-mark-all" @tap="markAllRead">全部已读</text>
    </view>

    <!-- Tab 筛选 -->
    <scroll-view scroll-x class="notif-tabs">
      <view v-for="t in tabs" :key="t.key"
        class="notif-tab" :class="{ 'notif-tab--active': activeTab === t.key }"
        @tap="activeTab = t.key">
        {{ t.label }}
        <view v-if="t.count > 0" class="notif-badge">{{ t.count }}</view>
      </view>
    </scroll-view>

    <!-- 消息列表 -->
    <scroll-view scroll-y class="notif-list" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view v-for="n in filteredItems" :key="n.id"
        class="notif-item" :class="{ 'notif-item--unread': !n.is_read }"
        @tap="openNotif(n)">
        <view class="notif-icon-wrap" :style="{ background: typeColor(n.type) + '20' }">
          <text class="notif-icon">{{ typeIcon(n.type) }}</text>
        </view>
        <view class="notif-body">
          <view class="notif-row">
            <text class="notif-item-title">{{ n.title }}</text>
            <view v-if="!n.is_read" class="notif-dot" />
          </view>
          <text class="notif-item-body">{{ n.body }}</text>
          <text class="notif-item-time">{{ formatTime(n.created_at) }}</text>
        </view>
      </view>

      <view v-if="filteredItems.length === 0" class="notif-empty">
        <text class="notif-empty-icon">🔔</text>
        <text class="notif-empty-text">暂无消息</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const activeTab = ref('all')
const refreshing = ref(false)
const items = ref<any[]>([])

const tabs = computed(() => {
  const unread = items.value.filter(n => !n.is_read).length
  return [
    { key: 'all',      label: '全部',   count: items.value.length },
    { key: 'unread',   label: '未读',   count: unread },
    { key: 'review',   label: '审核',   count: items.value.filter(n => n.type === 'review').length },
    { key: 'system',   label: '系统',   count: items.value.filter(n => n.type === 'system').length },
  ]
})

const filteredItems = computed(() => {
  if (activeTab.value === 'all') return items.value
  if (activeTab.value === 'unread') return items.value.filter(n => !n.is_read)
  return items.value.filter(n => n.type === activeTab.value)
})

function typeIcon(t: string): string {
  const m: Record<string, string> = {
    review: '📋', assessment: '📊', system: '📣',
    learning: '📚', reminder: '⏰', alert: '⚠️',
  }
  return m[t] || '🔔'
}
function typeColor(t: string): string {
  const m: Record<string, string> = {
    review: '#3498DB', assessment: '#E67E22', system: '#9B59B6',
    learning: '#27AE60', alert: '#E74C3C',
  }
  return m[t] || '#5B6B7F'
}

function formatTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = Math.floor((now.getTime() - d.getTime()) / 1000)
  if (diff < 60)   return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400)return Math.floor(diff / 3600) + '小时前'
  if (diff < 86400 * 7) return Math.floor(diff / 86400) + '天前'
  return (d.getMonth() + 1) + '/' + d.getDate()
}

async function loadData() {
  try {
    const res = await http<any>('/api/v1/notifications?limit=50')
    items.value = res.items || []
  } catch { items.value = [] }
}

async function openNotif(n: any) {
  if (!n.is_read) {
    try {
      await http(`/api/v1/notifications/${n.id}/read`, { method: 'POST' })
      n.is_read = true
    } catch {}
  }
  // 按类型跳转
  const links: Record<string, string> = {
    review: '/pages/coach/assessment/index',
    assessment: '/pages/coach/assessment/index',
    learning: '/pages/learning/index',
  }
  const url = links[n.type]
  if (url) uni.navigateTo({ url }).catch(() => {})
}

async function markAllRead() {
  try {
    await http('/api/v1/notifications/read-all', { method: 'POST' })
    items.value.forEach(n => n.is_read = true)
    uni.showToast({ title: '已全部标记已读', icon: 'success' })
  } catch {
    // 逐条标记
    await Promise.allSettled(
      items.value.filter(n => !n.is_read).map(n =>
        http(`/api/v1/notifications/${n.id}/read`, { method: 'POST' })
      )
    )
    items.value.forEach(n => n.is_read = true)
    uni.showToast({ title: '已全部标记已读', icon: 'success' })
  }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }

onMounted(() => { loadData() })
</script>

<style scoped>
.notif-page { min-height: 100vh; background: #F5F6FA; }

.notif-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 24rpx 32rpx;
  padding-top: calc(80rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%);
  color: #fff;
}
.notif-title { font-size: 38rpx; font-weight: 700; }
.notif-mark-all { font-size: 26rpx; opacity: 0.85; }

.notif-tabs {
  display: flex; white-space: nowrap;
  background: #fff; padding: 0 24rpx;
  border-bottom: 1rpx solid #F0F0F0;
}
.notif-tab {
  display: inline-flex; align-items: center; gap: 8rpx;
  padding: 20rpx 24rpx; font-size: 26rpx; color: #8E99A4;
  border-bottom: 4rpx solid transparent; flex-shrink: 0;
}
.notif-tab--active { color: #2D8E69; border-bottom-color: #2D8E69; font-weight: 600; }
.notif-badge {
  background: #E74C3C; color: #fff;
  font-size: 18rpx; padding: 2rpx 8rpx; border-radius: 20rpx; min-width: 30rpx; text-align: center;
}

.notif-list { height: calc(100vh - 280rpx); }

.notif-item {
  display: flex; align-items: flex-start; gap: 20rpx;
  background: #fff; padding: 24rpx 32rpx;
  border-bottom: 1rpx solid #F8F8F8;
}
.notif-item--unread { background: #FAFFFE; }
.notif-icon-wrap {
  width: 72rpx; height: 72rpx; border-radius: 18rpx;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.notif-icon { font-size: 36rpx; }
.notif-body { flex: 1; min-width: 0; }
.notif-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8rpx; }
.notif-item-title { font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.notif-dot { width: 14rpx; height: 14rpx; border-radius: 50%; background: #E74C3C; flex-shrink: 0; }
.notif-item-body { display: block; font-size: 24rpx; color: #5B6B7F; line-height: 1.5; margin-bottom: 8rpx; }
.notif-item-time { display: block; font-size: 22rpx; color: #BDC3C7; }

.notif-empty { text-align: center; padding: 120rpx 0; }
.notif-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.notif-empty-text { font-size: 28rpx; color: #8E99A4; }
</style>
