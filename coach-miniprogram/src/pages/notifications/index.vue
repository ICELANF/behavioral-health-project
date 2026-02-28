<template>
  <view class="nt-page">

    <!-- 顶部标题栏 -->
    <view class="nt-header safe-area-top">
      <text class="nt-header__title">消息中心</text>
      <view class="nt-header__actions">
        <view class="nt-header__btn" v-if="unreadCount > 0" @tap="markAllRead">
          <text>全部已读</text>
        </view>
      </view>
    </view>

    <!-- Tab 筛选（角色感知） -->
    <view class="nt-tabs">
      <view
        v-for="tab in visibleTabs"
        :key="tab.key"
        class="nt-tab"
        :class="{ 'nt-tab--active': activeTab === tab.key }"
        @tap="switchTab(tab.key)"
      >
        <text>{{ tab.label }}</text>
        <view class="nt-tab__badge" v-if="getTabBadge(tab.key) > 0">
          <text>{{ getTabBadge(tab.key) > 99 ? '99+' : getTabBadge(tab.key) }}</text>
        </view>
      </view>
    </view>

    <!-- 列表区域 -->
    <scroll-view
      scroll-y
      class="nt-body"
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
      @scrolltolower="loadMore"
    >

      <!-- ═══ 消息会话 Tab ═══ -->
      <template v-if="activeTab === 'conversations'">
        <template v-if="conversations.length">
          <view
            v-for="conv in conversations"
            :key="conv.student_id"
            class="nt-conv"
            @tap="openConversation(conv)"
          >
            <view class="nt-conv__avatar-wrap">
              <image class="nt-conv__avatar" :src="conv.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
              <view class="nt-conv__online" v-if="conv.is_online"></view>
            </view>
            <view class="nt-conv__body">
              <view class="nt-conv__row1">
                <text class="nt-conv__name">{{ conv.student_name }}</text>
                <text class="nt-conv__time">{{ formatTime(conv.last_message_at) }}</text>
              </view>
              <view class="nt-conv__row2">
                <text class="nt-conv__preview">{{ conv.last_message || '暂无消息' }}</text>
                <view class="nt-conv__unread" v-if="conv.unread_count > 0">
                  <text>{{ conv.unread_count > 99 ? '99+' : conv.unread_count }}</text>
                </view>
              </view>
              <!-- 学员状态标签 -->
              <view class="nt-conv__tags" v-if="conv.risk_level || conv.ttm_stage">
                <view class="nt-conv__tag nt-conv__tag--risk" v-if="conv.risk_level && conv.risk_level !== 'low'">
                  <text>{{ RISK_LABEL[conv.risk_level] || conv.risk_level }}</text>
                </view>
                <view class="nt-conv__tag nt-conv__tag--stage" v-if="conv.ttm_stage">
                  <text>{{ TTM_LABEL[conv.ttm_stage] || conv.ttm_stage }}</text>
                </view>
              </view>
            </view>
          </view>
        </template>
        <view v-else class="nt-empty">
          <text class="nt-empty__icon">💬</text>
          <text class="nt-empty__text">暂无消息会话</text>
          <text class="nt-empty__sub">学员的消息将显示在这里</text>
        </view>
      </template>

      <!-- ═══ 通知列表 Tab ═══ -->
      <template v-else>
        <template v-if="groupedNotifications.length">
          <view v-for="group in groupedNotifications" :key="group.date" class="nt-group">
            <text class="nt-group__date">{{ group.label }}</text>
            <view
              v-for="item in group.items"
              :key="item.id"
              class="nt-item"
              :class="{ 'nt-item--unread': !item.is_read }"
              @tap="openNotification(item)"
            >
              <view class="nt-item__dot" v-if="!item.is_read"></view>
              <view class="nt-item__icon" :class="`nt-item__icon--${item.type}`">
                <text>{{ getTypeIcon(item.type) }}</text>
              </view>
              <view class="nt-item__content">
                <text class="nt-item__title">{{ item.title }}</text>
                <text class="nt-item__summary">{{ item.summary || item.content }}</text>
                <!-- 快捷操作 -->
                <view class="nt-item__quick" v-if="item.action_type && !item.is_handled">
                  <view class="nt-quick-btn nt-quick-btn--primary" @tap.stop="handleQuickAction(item, 'approve')">
                    <text>{{ QUICK_LABEL[item.action_type]?.approve || '处理' }}</text>
                  </view>
                  <view class="nt-quick-btn nt-quick-btn--secondary" @tap.stop="handleQuickAction(item, 'view')">
                    <text>查看详情</text>
                  </view>
                </view>
                <text class="nt-item__time">{{ formatTime(item.created_at) }}</text>
              </view>
            </view>
          </view>

          <view class="nt-loading" v-if="hasMore">
            <text>加载更多...</text>
          </view>
        </template>

        <view v-else-if="!loading" class="nt-empty">
          <text class="nt-empty__icon">{{ activeTab === 'activity' ? '📊' : '🔔' }}</text>
          <text class="nt-empty__text">{{ EMPTY_TEXT[activeTab] || '暂无消息' }}</text>
        </view>
      </template>

      <!-- 加载骨架 -->
      <template v-if="loading && notifications.length === 0">
        <view class="bhp-skeleton" v-for="i in 4" :key="i" style="height: 120rpx; border-radius: var(--radius-lg); margin-bottom: 12rpx;"></view>
      </template>

    </scroll-view>

    <!-- TabBar 占位 -->
    <view style="height: 120rpx;"></view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import http from '@/api/request'

// ============================================================
// 角色与 Tab 配置
// ============================================================
const userInfo = ref<any>(null)
const isCoach = computed(() => {
  const role = userInfo.value?.role || ''
  return ['bhp_coach', 'coach', 'bhp_promoter', 'bhp_master', 'admin'].includes(role)
})

const ALL_TABS = [
  { key: 'all',           label: '全部',   roles: ['all'] },
  { key: 'conversations', label: '会话',   roles: ['coach'] },
  { key: 'activity',      label: '学员动态', roles: ['coach'] },
  { key: 'review',        label: '审核',   roles: ['coach'] },
  { key: 'learning',      label: '学习',   roles: ['student'] },
  { key: 'coach',         label: '教练',   roles: ['student'] },
  { key: 'system',        label: '系统',   roles: ['all'] },
]

const visibleTabs = computed(() => {
  const roleKey = isCoach.value ? 'coach' : 'student'
  return ALL_TABS.filter(t => t.roles.includes('all') || t.roles.includes(roleKey))
})

const RISK_LABEL: Record<string, string> = {
  high: '高风险', medium: '中风险', low: '低风险',
  R4: '高危', R3: '警惕', R2: '关注', R1: '正常',
}
const TTM_LABEL: Record<string, string> = {
  precontemplation: '前意向', contemplation: '意向',
  preparation: '准备', action: '行动',
  maintenance: '维持', termination: '终止',
}
const QUICK_LABEL: Record<string, { approve: string }> = {
  push_review:       { approve: '去审批' },
  assessment_review: { approve: '去审核' },
  flywheel_review:   { approve: '去处理' },
}
const EMPTY_TEXT: Record<string, string> = {
  all: '暂无消息',
  activity: '暂无学员动态',
  review: '暂无待审核提醒',
  learning: '暂无学习通知',
  coach: '暂无教练消息',
  system: '暂无系统通知',
}

// ============================================================
// 状态
// ============================================================
const activeTab     = ref('all')
const notifications = ref<any[]>([])
const conversations = ref<any[]>([])
const loading       = ref(false)
const refreshing    = ref(false)
const hasMore       = ref(false)
const page          = ref(1)

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

// 按日期分组
const groupedNotifications = computed(() => {
  const groups: Record<string, any[]> = {}
  for (const item of notifications.value) {
    const dateKey = getDateKey(item.created_at)
    if (!groups[dateKey]) groups[dateKey] = []
    groups[dateKey].push(item)
  }
  return Object.entries(groups).map(([date, items]) => ({
    date,
    label: getDateLabel(date),
    items,
  }))
})

// Tab 角标
function getTabBadge(key: string): number {
  if (key === 'all') return unreadCount.value
  if (key === 'conversations') return conversations.value.reduce((sum, c) => sum + (c.unread_count || 0), 0)
  return notifications.value.filter(n => !n.is_read && matchTab(n, key)).length
}

function matchTab(item: any, tab: string): boolean {
  if (tab === 'all') return true
  if (tab === 'activity') return ['student_action', 'health_alert', 'milestone'].includes(item.type)
  if (tab === 'review') return ['push_review', 'assessment_review', 'flywheel_review'].includes(item.type)
  return item.type === tab
}

// ============================================================
// 生命周期
// ============================================================
onMounted(async () => {
  // 读取用户信息
  try {
    const info = uni.getStorageSync('user_info')
    userInfo.value = typeof info === 'string' ? JSON.parse(info) : info
  } catch { userInfo.value = {} }

  await loadNotifications()
  if (isCoach.value) loadConversations()
})

// ============================================================
// 数据加载
// ============================================================
async function loadNotifications(reset = false) {
  if (loading.value) return
  if (reset) { page.value = 1; notifications.value = [] }
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: 20 }
    if (activeTab.value !== 'all' && activeTab.value !== 'conversations') {
      params.type = activeTab.value
    }
    const res = await http.get<any>('/v1/notifications', params)
    const items = res.items || res.notifications || []
    if (page.value === 1) {
      notifications.value = items
    } else {
      notifications.value = [...notifications.value, ...items]
    }
    hasMore.value = items.length >= 20
  } catch {
    if (page.value === 1) notifications.value = []
  } finally {
    loading.value = false
  }
}

async function loadConversations() {
  try {
    const res = await http.get<any>('/v1/coach/conversations', { page_size: 50 })
    conversations.value = res.items || res.conversations || []
  } catch {
    // 如果接口不存在，从学员列表构造会话
    try {
      const dash = await http.get<any>('/v1/coach/dashboard')
      conversations.value = (dash.students || []).map((s: any) => ({
        student_id: s.id,
        student_name: s.name || s.full_name || s.username,
        avatar_url: s.avatar_url,
        last_message: s.latest_note || '',
        last_message_at: s.last_active_at || s.updated_at || '',
        unread_count: 0,
        risk_level: s.risk_level,
        ttm_stage: s.ttm_stage,
        is_online: false,
      }))
    } catch {
      conversations.value = []
    }
  }
}

// ============================================================
// 交互操作
// ============================================================
function switchTab(key: string) {
  if (activeTab.value === key) return
  activeTab.value = key
  if (key === 'conversations') {
    loadConversations()
  } else {
    page.value = 1
    notifications.value = []
    loadNotifications()
  }
}

async function onRefresh() {
  refreshing.value = true
  page.value = 1
  await loadNotifications(true)
  if (isCoach.value) await loadConversations()
  refreshing.value = false
}

function loadMore() {
  if (!hasMore.value || loading.value || activeTab.value === 'conversations') return
  page.value++
  loadNotifications()
}

async function markAllRead() {
  try {
    // 尝试批量接口
    try {
      await http.post('/v1/notifications/read-all', {})
    } catch {
      // 回退：逐条标记
      const unread = notifications.value.filter(n => !n.is_read)
      await Promise.all(unread.map(n => http.post(`/v1/notifications/${n.id}/read`, {}).catch(() => {})))
    }
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

function openConversation(conv: any) {
  uni.navigateTo({ url: `/pages/coach/students/detail?id=${conv.student_id}&tab=message` })
}

async function handleQuickAction(item: any, action: string) {
  if (action === 'view' && item.link) {
    openNotification(item)
    return
  }
  // 快捷审批跳转
  const routes: Record<string, string> = {
    push_review: '/pages/coach/push-queue',
    assessment_review: '/pages/coach/assessment/index',
    flywheel_review: '/pages/coach/flywheel/index',
  }
  const route = routes[item.action_type]
  if (route) {
    if (!item.is_read) {
      try { await http.post(`/v1/notifications/${item.id}/read`, {}); item.is_read = true } catch {}
    }
    uni.navigateTo({ url: route })
  }
}

// ============================================================
// 工具函数
// ============================================================
function getTypeIcon(type: string): string {
  const icons: Record<string, string> = {
    system: '⚙', learning: '📚', coach: '👨‍🏫',
    alert: '⚠', reward: '🎁',
    student_action: '🏃', health_alert: '🩺', milestone: '🏆',
    push_review: '📋', assessment_review: '📝', flywheel_review: '🤖',
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
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return dateStr.slice(0, 10)
}

function getDateKey(dateStr: string): string {
  if (!dateStr) return 'unknown'
  return dateStr.slice(0, 10)
}

function getDateLabel(dateKey: string): string {
  if (dateKey === 'unknown') return '未知'
  const today = new Date().toISOString().slice(0, 10)
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10)
  if (dateKey === today) return '今天'
  if (dateKey === yesterday) return '昨天'
  return dateKey.slice(5).replace('-', '月') + '日'
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
.nt-header__actions { display: flex; gap: 16rpx; }
.nt-header__btn {
  font-size: 24rpx; font-weight: 600; color: var(--bhp-primary-500, #10b981);
  padding: 8rpx 16rpx; border-radius: var(--radius-full);
  background: rgba(16,185,129,0.08);
}
.nt-header__btn:active { opacity: 0.7; }

/* Tab */
.nt-tabs {
  display: flex; background: var(--surface); padding: 0 16rpx;
  border-bottom: 1px solid var(--border-light); overflow-x: auto;
}
.nt-tab {
  flex-shrink: 0; text-align: center; padding: 20rpx 20rpx; position: relative;
  font-size: 26rpx; font-weight: 500; color: var(--text-tertiary);
}
.nt-tab--active {
  color: var(--bhp-primary-500, #10b981); font-weight: 700;
  border-bottom: 4rpx solid var(--bhp-primary-500, #10b981);
}
.nt-tab__badge {
  position: absolute; top: 8rpx; right: 4rpx;
  min-width: 28rpx; height: 28rpx; border-radius: 14rpx;
  background: #ef4444; color: #fff; font-size: 18rpx; font-weight: 700;
  display: flex; align-items: center; justify-content: center; padding: 0 6rpx;
}

/* 列表 */
.nt-body { flex: 1; padding: 12rpx 32rpx; }

/* 日期分组 */
.nt-group { margin-bottom: 8rpx; }
.nt-group__date {
  display: block; font-size: 22rpx; font-weight: 600; color: var(--text-tertiary);
  padding: 16rpx 0 8rpx;
}

/* 通知卡片 */
.nt-item {
  display: flex; align-items: flex-start; gap: 16rpx;
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 20rpx 24rpx; margin-bottom: 12rpx;
  border: 1px solid var(--border-light); position: relative;
}
.nt-item--unread { background: rgba(16,185,129,0.03); border-color: rgba(16,185,129,0.2); }
.nt-item__dot {
  position: absolute; top: 24rpx; left: 12rpx;
  width: 12rpx; height: 12rpx; border-radius: 50%; background: #ef4444;
}
.nt-item__icon {
  width: 56rpx; height: 56rpx; border-radius: var(--radius-md); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 28rpx;
}
.nt-item__icon--system { background: #f3f4f6; }
.nt-item__icon--learning { background: #eff6ff; }
.nt-item__icon--coach { background: #f0fdf4; }
.nt-item__icon--alert,
.nt-item__icon--health_alert { background: #fef2f2; }
.nt-item__icon--reward,
.nt-item__icon--milestone { background: #fffbeb; }
.nt-item__icon--push_review,
.nt-item__icon--assessment_review,
.nt-item__icon--flywheel_review { background: #faf5ff; }
.nt-item__icon--student_action { background: #f0fdf4; }

.nt-item__content { flex: 1; overflow: hidden; }
.nt-item__title {
  font-size: 28rpx; font-weight: 700; color: var(--text-primary); display: block;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.nt-item__summary {
  font-size: 24rpx; color: var(--text-secondary); display: block; margin-top: 4rpx;
  line-height: 1.5;
  overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}
.nt-item__time { font-size: 20rpx; color: var(--text-tertiary); display: block; margin-top: 8rpx; }

/* 快捷操作 */
.nt-item__quick { display: flex; gap: 12rpx; margin-top: 12rpx; }
.nt-quick-btn {
  font-size: 22rpx; font-weight: 600; padding: 8rpx 20rpx;
  border-radius: var(--radius-full);
}
.nt-quick-btn:active { opacity: 0.7; }
.nt-quick-btn--primary { background: var(--bhp-primary-500, #10b981); color: #fff; }
.nt-quick-btn--secondary { background: var(--surface-secondary); color: var(--text-secondary); }

/* ═══ 会话列表 ═══ */
.nt-conv {
  display: flex; align-items: flex-start; gap: 16rpx;
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; margin-bottom: 12rpx;
  border: 1px solid var(--border-light);
}
.nt-conv__avatar-wrap { position: relative; flex-shrink: 0; }
.nt-conv__avatar { width: 80rpx; height: 80rpx; border-radius: 50%; background: var(--bhp-gray-100, #f3f4f6); }
.nt-conv__online {
  position: absolute; bottom: 2rpx; right: 2rpx;
  width: 20rpx; height: 20rpx; border-radius: 50%;
  background: #10b981; border: 3rpx solid var(--surface);
}

.nt-conv__body { flex: 1; overflow: hidden; }
.nt-conv__row1 { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6rpx; }
.nt-conv__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.nt-conv__time { font-size: 20rpx; color: var(--text-tertiary); flex-shrink: 0; }

.nt-conv__row2 { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8rpx; }
.nt-conv__preview {
  font-size: 24rpx; color: var(--text-secondary); flex: 1;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.nt-conv__unread {
  min-width: 32rpx; height: 32rpx; border-radius: 16rpx;
  background: #ef4444; color: #fff; font-size: 18rpx; font-weight: 700;
  display: flex; align-items: center; justify-content: center; padding: 0 8rpx;
  flex-shrink: 0; margin-left: 12rpx;
}

.nt-conv__tags { display: flex; gap: 8rpx; }
.nt-conv__tag {
  font-size: 20rpx; font-weight: 600; padding: 2rpx 10rpx; border-radius: var(--radius-full);
}
.nt-conv__tag--risk { background: #fef2f2; color: #dc2626; }
.nt-conv__tag--stage { background: rgba(16,185,129,0.1); color: #059669; }

/* 加载 & 空状态 */
.nt-loading { text-align: center; padding: 20rpx; font-size: 24rpx; color: var(--text-tertiary); }
.nt-empty {
  display: flex; flex-direction: column; align-items: center;
  padding: 120rpx 32rpx; gap: 12rpx;
}
.nt-empty__icon { font-size: 80rpx; }
.nt-empty__text { font-size: 28rpx; font-weight: 600; color: var(--text-secondary); }
.nt-empty__sub { font-size: 24rpx; color: var(--text-tertiary); }
</style>
