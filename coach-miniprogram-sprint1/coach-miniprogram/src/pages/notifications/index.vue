<template>
  <view class="notify-page">

    <!-- 顶部工具栏 -->
    <view class="notify-toolbar px-4" v-if="!loading && total > 0">
      <text class="notify-toolbar__count text-secondary-color text-xs">
        共 {{ total }} 条{{ unreadCount > 0 ? `，${unreadCount} 条未读` : '' }}
      </text>
      <text
        class="notify-toolbar__all-read"
        v-if="unreadCount > 0"
        @tap="markAllRead"
      >全部已读</text>
    </view>

    <!-- 分类 Tab -->
    <view class="notify-tabs px-4">
      <view class="notify-tabs__inner">
        <view
          v-for="tab in TABS"
          :key="tab.key"
          class="notify-tab"
          :class="{ 'notify-tab--active': activeTab === tab.key }"
          @tap="switchTab(tab.key)"
        >
          <text>{{ tab.label }}</text>
          <text class="notify-tab__dot" v-if="tab.key === 'all' && unreadCount > 0"></text>
        </view>
      </view>
    </view>

    <!-- 列表 -->
    <view class="notify-list px-4">

      <!-- 骨架屏 -->
      <template v-if="loading">
        <view v-for="i in 5" :key="i" class="bhp-skeleton" style="height: 110rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else-if="items.length">
        <view
          v-for="item in items"
          :key="item.id"
          class="notify-item bhp-card bhp-card--flat"
          :class="{ 'notify-item--unread': !item.is_read }"
          @tap="handleTap(item)"
        >
          <!-- 未读点 -->
          <view class="notify-item__dot" v-if="!item.is_read"></view>

          <!-- 图标 -->
          <view
            class="notify-item__icon"
            :style="{ background: typeColor(item.type) + '18' }"
          >
            <text :style="{ fontSize: '32rpx' }">{{ TYPE_ICON[item.type] || '🔔' }}</text>
          </view>

          <!-- 内容 -->
          <view class="notify-item__body">
            <view class="notify-item__top">
              <text class="notify-item__title" :class="{ 'notify-item__title--bold': !item.is_read }">
                {{ item.title }}
              </text>
              <text class="notify-item__time text-xs text-tertiary-color">{{ relativeTime(item.created_at) }}</text>
            </view>
            <text class="notify-item__content text-sm text-secondary-color">{{ item.content }}</text>

            <!-- 类型标签 -->
            <view class="notify-item__tag" :style="{ background: typeColor(item.type) + '12', color: typeColor(item.type) }">
              <text class="text-xs">{{ TYPE_LABEL[item.type] || item.type }}</text>
            </view>
          </view>
        </view>

        <!-- 加载更多 -->
        <view class="notify-more" v-if="hasMore" @tap="loadMore">
          <text v-if="!loadingMore">加载更多</text>
          <text v-else class="text-secondary-color">加载中...</text>
        </view>
        <view class="notify-more notify-more--end" v-else-if="items.length >= 5">
          <text class="text-tertiary-color">已显示全部</text>
        </view>
      </template>

      <!-- 空状态 -->
      <view class="notify-empty" v-else>
        <text class="notify-empty__icon">🔔</text>
        <text class="notify-empty__title">暂无通知</text>
        <text class="notify-empty__sub text-secondary-color">
          {{ activeTab === 'system' ? '暂无系统通知' : activeTab === 'coach' ? '暂无教练消息' : '您暂时没有任何通知' }}
        </text>
      </view>

    </view>

    <view style="height: 40rpx;"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'

type TabKey = 'all' | 'system' | 'coach' | 'assessment'

interface Notification {
  id: number
  type: string           // system | coach_message | assessment | push | milestone | promotion
  title: string
  content: string
  is_read: boolean
  created_at: string
  link?: string          // 可选跳转路径
  metadata?: Record<string, any>
}

const TABS: { key: TabKey; label: string }[] = [
  { key: 'all',        label: '全部'   },
  { key: 'system',     label: '系统'   },
  { key: 'coach',      label: '教练'   },
  { key: 'assessment', label: '评估'   },
]

const TYPE_LABEL: Record<string, string> = {
  system:          '系统',
  coach_message:   '教练消息',
  assessment:      '评估任务',
  push:            '健康推送',
  milestone:       '成就里程碑',
  promotion:       '晋级通知',
}
const TYPE_ICON: Record<string, string> = {
  system:          '📢',
  coach_message:   '💬',
  assessment:      '📋',
  push:            '💊',
  milestone:       '🏆',
  promotion:       '🎯',
}
const TYPE_COLORS: Record<string, string> = {
  system:          '#722ed1',
  coach_message:   '#1890ff',
  assessment:      '#fa8c16',
  push:            '#52c41a',
  milestone:       '#eb2f96',
  promotion:       '#10b981',
}

const activeTab   = ref<TabKey>('all')
const items       = ref<Notification[]>([])
const loading     = ref(false)
const loadingMore = ref(false)
const page        = ref(1)
const hasMore     = ref(true)
const total       = ref(0)

const unreadCount = computed(() => items.value.filter(i => !i.is_read).length)

onMounted(() => loadData(true))

onPullDownRefresh(async () => {
  await loadData(true)
  uni.stopPullDownRefresh()
})

async function switchTab(key: TabKey) {
  if (key === activeTab.value) return
  activeTab.value = key
  await loadData(true)
}

async function loadData(reset = false) {
  if (reset) { page.value = 1; items.value = []; hasMore.value = true }
  if (!hasMore.value) return
  reset ? (loading.value = true) : (loadingMore.value = true)

  const typeFilter = activeTab.value === 'all' ? undefined
    : activeTab.value === 'coach' ? 'coach_message'
    : activeTab.value

  try {
    const resp = await http.get<{ items: Notification[]; total: number }>(
      '/v1/notifications',
      { type: typeFilter, page: page.value, page_size: 20 }
    )
    const newItems = resp.items || []
    items.value = reset ? newItems : [...items.value, ...newItems]
    total.value = resp.total || items.value.length
    hasMore.value = newItems.length === 20
    page.value++
  } catch {
    // 后端通知接口可能未实现，静默降级
    if (reset) { items.value = []; total.value = 0 }
    hasMore.value = false
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() { loadData(false) }

async function markAllRead() {
  try {
    await http.post('/v1/notifications/read-all', {})
    items.value.forEach(i => { i.is_read = true })
  } catch {
    // 静默失败
  }
}

async function markRead(id: number) {
  try {
    await http.post(`/v1/notifications/${id}/read`, {})
  } catch {/* ignore */}
}

function handleTap(item: Notification) {
  if (!item.is_read) {
    item.is_read = true
    markRead(item.id)
  }
  // 根据类型跳转
  if (item.link) {
    uni.navigateTo({ url: item.link })
    return
  }
  const type = item.type
  if (type === 'assessment') {
    uni.navigateTo({ url: '/pages/assessment/pending' })
  } else if (type === 'coach_message') {
    // 教练消息暂无独立详情页，直接回到首页
    uni.switchTab({ url: '/pages/home/index' })
  } else if (type === 'promotion') {
    uni.navigateTo({ url: '/pages/journey/overview' })
  } else if (type === 'milestone') {
    uni.navigateTo({ url: '/pages/profile/performance' })
  }
}

function typeColor(type: string): string {
  return TYPE_COLORS[type] || '#8c8c8c'
}

function relativeTime(dateStr: string): string {
  try {
    const diff = Date.now() - new Date(dateStr).getTime()
    const mins  = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days  = Math.floor(diff / 86400000)
    if (mins < 1)   return '刚刚'
    if (mins < 60)  return `${mins}分钟前`
    if (hours < 24) return `${hours}小时前`
    if (days < 7)   return `${days}天前`
    const d = new Date(dateStr)
    return `${d.getMonth() + 1}/${d.getDate()}`
  } catch { return '' }
}
</script>

<style scoped>
.notify-page { background: var(--surface-secondary); min-height: 100vh; }

/* 工具栏 */
.notify-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  padding-top: 12rpx; padding-bottom: 4rpx;
}
.notify-toolbar__all-read {
  font-size: 24rpx; color: var(--bhp-primary-500);
  padding: 8rpx 0; cursor: pointer;
}

/* Tabs */
.notify-tabs { padding-top: 12rpx; padding-bottom: 8rpx; }
.notify-tabs__inner {
  display: flex; background: var(--surface);
  border-radius: var(--radius-full); padding: 6rpx;
  border: 1px solid var(--border-light); gap: 4rpx;
}
.notify-tab {
  flex: 1; text-align: center; padding: 10rpx 8rpx;
  border-radius: var(--radius-full); font-size: 26rpx;
  color: var(--text-secondary); cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 6rpx;
  position: relative;
}
.notify-tab--active { background: var(--bhp-primary-500); color: #fff; font-weight: 600; }
.notify-tab__dot {
  width: 12rpx; height: 12rpx; border-radius: 50%;
  background: #ff4d4f; flex-shrink: 0;
}

/* 列表 */
.notify-list { padding-top: 8rpx; }

/* 通知条目 */
.notify-item {
  display: flex; align-items: flex-start; gap: 16rpx;
  padding: 20rpx 20rpx; margin-bottom: 10rpx;
  cursor: pointer; position: relative;
  border-left: 4rpx solid transparent;
  transition: opacity 0.15s;
}
.notify-item:active { opacity: 0.8; }
.notify-item--unread { border-left-color: var(--bhp-primary-500); }

/* 未读圆点 */
.notify-item__dot {
  position: absolute; top: 16rpx; right: 16rpx;
  width: 14rpx; height: 14rpx; border-radius: 50%;
  background: #ff4d4f;
}

/* 图标 */
.notify-item__icon {
  width: 72rpx; height: 72rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

/* 正文 */
.notify-item__body    { flex: 1; min-width: 0; }
.notify-item__top     { display: flex; justify-content: space-between; align-items: flex-start; gap: 8rpx; margin-bottom: 8rpx; }
.notify-item__title   { font-size: 26rpx; color: var(--text-primary); flex: 1; line-height: 1.4; }
.notify-item__title--bold { font-weight: 600; }
.notify-item__time    { white-space: nowrap; flex-shrink: 0; }
.notify-item__content {
  font-size: 24rpx; color: var(--text-secondary);
  line-height: 1.5; margin-bottom: 10rpx;
  display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}
.notify-item__tag {
  display: inline-block; font-size: 18rpx; font-weight: 600;
  padding: 2rpx 10rpx; border-radius: var(--radius-full);
}

/* 加载更多 */
.notify-more { text-align: center; padding: 20rpx; font-size: 26rpx; color: var(--bhp-primary-500); cursor: pointer; }
.notify-more--end { color: var(--text-tertiary); }

/* 空状态 */
.notify-empty { display: flex; flex-direction: column; align-items: center; padding: 100rpx 0; gap: 16rpx; }
.notify-empty__icon  { font-size: 80rpx; }
.notify-empty__title { font-size: 28rpx; color: var(--text-tertiary); }
.notify-empty__sub   { font-size: 24rpx; text-align: center; padding: 0 48rpx; }
</style>
