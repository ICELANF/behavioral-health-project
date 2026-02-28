<template>
  <view class="nt-page">

    <!-- 顶部标题栏 -->
    <view class="nt-header safe-area-top">
      <text class="nt-header__title">消息中心</text>
      <view class="nt-header__action" @tap="markAllRead" v-if="notifications.length">
        <text>全部已读</text>
      </view>
    </view>

    <!-- Tab 筛选 -->
    <view class="nt-tabs">
      <view
        v-for="tab in TABS"
        :key="tab.key"
        class="nt-tab"
        :class="{ 'nt-tab--active': activeTab === tab.key }"
        @tap="switchTab(tab.key)"
      >
        <text>{{ tab.label }}</text>
        <view class="nt-tab__badge" v-if="tab.key === 'all' && unreadCount > 0">
          <text>{{ unreadCount > 99 ? '99+' : unreadCount }}</text>
        </view>
      </view>
    </view>

    <scroll-view scroll-y class="nt-body" @scrolltolower="loadMore">

      <!-- 通知列表 -->
      <template v-if="notifications.length">
        <view
          v-for="item in notifications"
          :key="item.id"
          class="nt-item"
          :class="{ 'nt-item--unread': !item.is_read }"
          @tap="openNotification(item)"
        >
          <view class="nt-item__dot" v-if="!item.is_read"></view>
          <view class="nt-item__icon">
            <text>{{ getTypeIcon(item.type) }}</text>
          </view>
          <view class="nt-item__content">
            <text class="nt-item__title">{{ item.title }}</text>
            <text class="nt-item__summary">{{ item.summary || item.content }}</text>
            <text class="nt-item__time">{{ formatTime(item.created_at) }}</text>
          </view>
        </view>

        <view class="nt-loading" v-if="hasMore">
          <text>加载更多...</text>
        </view>
      </template>

      <!-- 空状态 -->
      <view class="nt-empty" v-else-if="!loading">
        <text class="nt-empty__icon">🔔</text>
        <text class="nt-empty__text">暂无消息</text>
      </view>

    </scroll-view>

    <!-- TabBar 占位 -->
    <view style="height: 120rpx;"></view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'

const TABS = [
  { key: 'all',     label: '全部' },
  { key: 'system',  label: '系统' },
  { key: 'learning', label: '学习' },
  { key: 'coach',   label: '教练' },
]

const activeTab     = ref('all')
const notifications = ref<any[]>([])
const loading       = ref(false)
const hasMore       = ref(false)
const page          = ref(1)

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

onMounted(async () => {
  await loadNotifications()
})

async function loadNotifications() {
  if (loading.value) return
  loading.value = true
  try {
    const res = await http.get<any>('/v1/notifications', {
      type: activeTab.value,
      page: page.value,
      page_size: 20,
    })
    const items = res.items || res.notifications || []
    if (page.value === 1) {
      notifications.value = items
    } else {
      notifications.value = [...notifications.value, ...items]
    }
    hasMore.value = items.length >= 20
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function switchTab(key: string) {
  if (activeTab.value === key) return
  activeTab.value = key
  page.value = 1
  notifications.value = []
  loadNotifications()
}

function loadMore() {
  if (!hasMore.value || loading.value) return
  page.value++
  loadNotifications()
}

async function markAllRead() {
  try {
    // 逐条标记已读（后端无 read-all 接口）
    const unread = notifications.value.filter(n => !n.is_read)
    await Promise.all(unread.map(n => http.post(`/v1/notifications/${n.id}/read`, {})))
    notifications.value = notifications.value.map(n => ({ ...n, is_read: true }))
    uni.showToast({ title: '已全部标记已读', icon: 'success' })
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

async function openNotification(item: any) {
  // 标记已读
  if (!item.is_read) {
    try {
      await http.post(`/v1/notifications/${item.id}/read`, {})
      item.is_read = true
    } catch {}
  }
  // 跳转
  if (item.link) {
    uni.navigateTo({ url: item.link })
  }
}

function getTypeIcon(type: string): string {
  const icons: Record<string, string> = {
    system:  '⚙',
    learning: '📚',
    coach:   '👨‍🏫',
    alert:   '⚠',
    reward:  '🎁',
  }
  return icons[type] || '📢'
}

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins}分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  return dateStr.slice(0, 10)
}
</script>

<style scoped>
.nt-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

/* 顶部 */
.nt-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16rpx 32rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.nt-header__title { font-size: 34rpx; font-weight: 800; color: var(--text-primary); }
.nt-header__action { cursor: pointer; }
.nt-header__action text { font-size: 24rpx; color: var(--bhp-primary-500); font-weight: 600; }

/* Tab */
.nt-tabs {
  display: flex; background: var(--surface); padding: 0 32rpx;
  border-bottom: 1px solid var(--border-light);
}
.nt-tab {
  flex: 1; text-align: center; padding: 20rpx 0; position: relative;
  font-size: 26rpx; font-weight: 600; color: var(--text-tertiary); cursor: pointer;
}
.nt-tab--active { color: var(--bhp-primary-500); border-bottom: 4rpx solid var(--bhp-primary-500); }
.nt-tab__badge {
  position: absolute; top: 10rpx; right: 20rpx;
  min-width: 32rpx; height: 32rpx; border-radius: 16rpx;
  background: #ef4444; color: #fff; font-size: 18rpx; font-weight: 700;
  display: flex; align-items: center; justify-content: center; padding: 0 6rpx;
}

/* 列表 */
.nt-body { flex: 1; padding: 12rpx 32rpx; }

.nt-item {
  display: flex; align-items: flex-start; gap: 16rpx;
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 20rpx 24rpx; margin-bottom: 12rpx;
  border: 1px solid var(--border-light); position: relative; cursor: pointer;
}
.nt-item--unread { background: rgba(16,185,129,0.03); border-color: rgba(16,185,129,0.15); }
.nt-item__dot {
  position: absolute; top: 24rpx; left: 12rpx;
  width: 12rpx; height: 12rpx; border-radius: 50%; background: #ef4444;
}
.nt-item__icon {
  width: 56rpx; height: 56rpx; border-radius: var(--radius-md); flex-shrink: 0;
  background: var(--surface-secondary); display: flex; align-items: center; justify-content: center;
  font-size: 28rpx;
}
.nt-item__content { flex: 1; overflow: hidden; }
.nt-item__title {
  font-size: 28rpx; font-weight: 700; color: var(--text-primary); display: block;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.nt-item__summary {
  font-size: 24rpx; color: var(--text-secondary); display: block; margin-top: 4rpx;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.nt-item__time { font-size: 20rpx; color: var(--text-tertiary); display: block; margin-top: 8rpx; }

.nt-loading { text-align: center; padding: 20rpx; font-size: 24rpx; color: var(--text-tertiary); }

/* 空状态 */
.nt-empty {
  display: flex; flex-direction: column; align-items: center;
  padding: 160rpx 32rpx; gap: 16rpx;
}
.nt-empty__icon { font-size: 80rpx; }
.nt-empty__text { font-size: 28rpx; color: var(--text-secondary); }
</style>
