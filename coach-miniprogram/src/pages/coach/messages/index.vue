<template>
  <view class="msg-page">
    <!-- 顶部导航 -->
    <view class="msg-navbar safe-area-top">
      <text class="msg-navbar__title">消息</text>
      <view class="msg-navbar__actions">
        <view class="msg-navbar__btn" @tap="markAllRead" v-if="unreadTotal > 0">
          <text class="msg-navbar__btn-text">全部已读</text>
        </view>
      </view>
    </view>

    <!-- 消息分类 Tab -->
    <view class="msg-tabs">
      <view
        v-for="tab in tabs" :key="tab.key"
        class="msg-tab" :class="{ 'msg-tab--active': activeTab === tab.key }"
        @tap="activeTab = tab.key"
      >
        <text class="msg-tab__text">{{ tab.label }}</text>
        <view class="msg-tab__badge" v-if="tab.unread > 0">
          <text>{{ tab.unread > 99 ? '99+' : tab.unread }}</text>
        </view>
      </view>
    </view>

    <!-- 消息列表 -->
    <scroll-view scroll-y class="msg-body" @scrolltolower="loadMore">
      <template v-if="loading && !messages.length">
        <view class="bhp-skeleton" v-for="i in 5" :key="i" style="height: 120rpx; border-radius: var(--radius-lg); margin-bottom: 12rpx;"></view>
      </template>

      <template v-else-if="filteredMessages.length">
        <view
          v-for="msg in filteredMessages" :key="msg.id"
          class="msg-item" :class="{ 'msg-item--unread': !msg.is_read }"
          @tap="openMessage(msg)"
        >
          <!-- 头像/图标 -->
          <view class="msg-item__avatar" :class="`msg-item__avatar--${msg.type || 'system'}`">
            <text>{{ getIcon(msg.type) }}</text>
          </view>

          <!-- 内容 -->
          <view class="msg-item__content">
            <view class="msg-item__header">
              <text class="msg-item__title">{{ msg.title || getTypeLabel(msg.type) }}</text>
              <text class="msg-item__time">{{ formatTime(msg.created_at) }}</text>
            </view>
            <text class="msg-item__preview">{{ msg.content || msg.summary || '点击查看详情' }}</text>
          </view>

          <!-- 未读点 -->
          <view class="msg-item__dot" v-if="!msg.is_read"></view>
        </view>
      </template>

      <!-- 空状态 -->
      <view v-else class="msg-empty">
        <text class="msg-empty__icon">📭</text>
        <text class="msg-empty__text">暂无{{ activeTab === 'all' ? '' : tabs.find(t => t.key === activeTab)?.label }}消息</text>
      </view>

      <!-- 加载更多 -->
      <view v-if="hasMore && filteredMessages.length" class="msg-loadmore">
        <text class="msg-loadmore__text">{{ loadingMore ? '加载中...' : '上拉加载更多' }}</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

/* ── 内联 request ── */
const _BASE = 'http://localhost:8002/api'
function _getToken(): string {
  try { return uni.getStorageSync('access_token') || '' } catch { return '' }
}
function _request<T = any>(method: string, url: string, data?: any): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${_BASE}${url}`,
      method: method as any,
      data,
      header: { Authorization: `Bearer ${_getToken()}`, 'Content-Type': 'application/json' },
      success: (res: any) => {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else reject({ message: res.data?.detail || `HTTP ${res.statusCode}`, statusCode: res.statusCode })
      },
      fail: (err: any) => reject({ message: err.errMsg || '网络异常' }),
    })
  })
}
const http = {
  get: <T = any>(url: string) => _request<T>('GET', url),
  post: <T = any>(url: string, data?: any) => _request<T>('POST', url, data),
}
/* ── end inline request ── */

const loading     = ref(false)
const loadingMore = ref(false)
const activeTab   = ref('all')
const messages    = ref<any[]>([])
const page        = ref(1)
const hasMore     = ref(false)

const TYPE_MAP: Record<string, string> = {
  system: '系统通知',
  coach: '教练消息',
  reminder: '健康提醒',
  task: '任务通知',
  encouragement: '激励消息',
  alert: '预警通知',
}
const ICON_MAP: Record<string, string> = {
  system: '🔔',
  coach: '👨‍⚕️',
  reminder: '⏰',
  task: '📋',
  encouragement: '💪',
  alert: '⚠️',
}

const tabs = computed(() => {
  const countByType: Record<string, number> = {}
  for (const m of messages.value) {
    if (!m.is_read) {
      const key = m.type || 'system'
      countByType[key] = (countByType[key] || 0) + 1
    }
  }
  const totalUnread = Object.values(countByType).reduce((s, n) => s + n, 0)
  return [
    { key: 'all', label: '全部', unread: totalUnread },
    { key: 'coach', label: '教练', unread: countByType['coach'] || 0 },
    { key: 'reminder', label: '提醒', unread: countByType['reminder'] || 0 },
    { key: 'system', label: '系统', unread: countByType['system'] || 0 },
  ]
})

const unreadTotal = computed(() => tabs.value[0].unread)

const filteredMessages = computed(() => {
  if (activeTab.value === 'all') return messages.value
  return messages.value.filter(m => (m.type || 'system') === activeTab.value)
})

function getTypeLabel(type: string): string { return TYPE_MAP[type] || '消息' }
function getIcon(type: string): string { return ICON_MAP[type] || '🔔' }

function formatTime(dt: string): string {
  if (!dt) return ''
  const d = new Date(dt)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH}小时前`
  const diffD = Math.floor(diffH / 24)
  if (diffD < 7) return `${diffD}天前`
  return `${d.getMonth() + 1}/${d.getDate()}`
}

onMounted(() => loadMessages())

async function loadMessages() {
  loading.value = true
  page.value = 1
  try {
    const res = await http.get<any>('/v1/messages?page=1&page_size=30')
    messages.value = res.items || res.messages || (Array.isArray(res) ? res : [])
    hasMore.value = (res.total || 0) > messages.value.length
  } catch {
    // fallback: 生成示例消息
    messages.value = [
      { id: 1, type: 'system', title: '欢迎使用行健平台', content: '您已成功注册，开始您的健康管理之旅。', is_read: true, created_at: new Date().toISOString() },
      { id: 2, type: 'reminder', title: '健康提醒', content: '今天别忘了记录血糖数据哦！', is_read: false, created_at: new Date(Date.now() - 3600000).toISOString() },
    ]
    hasMore.value = false
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  page.value++
  try {
    const res = await http.get<any>(`/v1/messages?page=${page.value}&page_size=30`)
    const newItems = res.items || res.messages || []
    messages.value.push(...newItems)
    hasMore.value = newItems.length >= 30
  } catch { hasMore.value = false }
  finally { loadingMore.value = false }
}

async function openMessage(msg: any) {
  // 标记已读
  if (!msg.is_read) {
    msg.is_read = true
    try { await http.post(`/v1/messages/${msg.id}/read`) } catch { /* 静默 */ }
  }
  // 跳转详情或弹窗
  uni.showModal({
    title: msg.title || getTypeLabel(msg.type),
    content: msg.content || '无详细内容',
    showCancel: false,
    confirmText: '知道了',
  })
}

async function markAllRead() {
  try {
    await http.post('/v1/messages/read-all')
    messages.value.forEach(m => m.is_read = true)
    uni.showToast({ title: '已全部标记已读', icon: 'success' })
  } catch {
    // 本地标记
    messages.value.forEach(m => m.is_read = true)
  }
}
</script>

<style scoped>
.msg-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

.msg-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 32rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: var(--surface); }
.msg-navbar__title { font-size: 34rpx; font-weight: 700; color: var(--text-primary); }
.msg-navbar__btn { padding: 8rpx 20rpx; background: var(--surface-secondary); border-radius: var(--radius-full); }
.msg-navbar__btn-text { font-size: 22rpx; color: var(--bhp-primary-600); font-weight: 600; }

.msg-tabs { display: flex; gap: 0; background: var(--surface); border-bottom: 1px solid var(--border-light); padding: 0 32rpx; }
.msg-tab { position: relative; padding: 16rpx 24rpx; cursor: pointer; display: flex; align-items: center; gap: 8rpx; }
.msg-tab__text { font-size: 26rpx; color: var(--text-secondary); font-weight: 500; }
.msg-tab--active { border-bottom: 4rpx solid var(--bhp-primary-600); }
.msg-tab--active .msg-tab__text { color: var(--bhp-primary-600); font-weight: 700; }
.msg-tab__badge { background: #ef4444; color: #fff; font-size: 18rpx; padding: 2rpx 10rpx; border-radius: var(--radius-full); min-width: 28rpx; text-align: center; }

.msg-body { flex: 1; padding: 16rpx 32rpx 120rpx; }

.msg-item {
  display: flex; align-items: center; gap: 20rpx;
  background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; margin-bottom: 12rpx;
  border: 1px solid var(--border-light); position: relative;
}
.msg-item--unread { background: var(--bhp-primary-50); border-color: var(--bhp-primary-100); }

.msg-item__avatar { width: 72rpx; height: 72rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 32rpx; flex-shrink: 0; background: var(--surface-secondary); }
.msg-item__avatar--coach { background: #dbeafe; }
.msg-item__avatar--reminder { background: #fef3c7; }
.msg-item__avatar--alert { background: #fee2e2; }
.msg-item__avatar--task { background: #d1fae5; }
.msg-item__avatar--encouragement { background: #ede9fe; }

.msg-item__content { flex: 1; min-width: 0; }
.msg-item__header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6rpx; }
.msg-item__title { font-size: 26rpx; font-weight: 600; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.msg-item__time { font-size: 20rpx; color: var(--text-tertiary); flex-shrink: 0; margin-left: 12rpx; }
.msg-item__preview { display: block; font-size: 24rpx; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.msg-item__dot { position: absolute; top: 20rpx; right: 20rpx; width: 14rpx; height: 14rpx; border-radius: 50%; background: #ef4444; }

.msg-empty { display: flex; flex-direction: column; align-items: center; padding: 160rpx 0; gap: 16rpx; }
.msg-empty__icon { font-size: 80rpx; }
.msg-empty__text { font-size: 26rpx; color: var(--text-tertiary); }

.msg-loadmore { text-align: center; padding: 24rpx; }
.msg-loadmore__text { font-size: 22rpx; color: var(--text-tertiary); }
</style>
