<template>
  <view class="msg-page">
    <view class="msg-navbar">
      <view class="msg-nav-back" @tap="goBack">←</view>
      <text class="msg-nav-title">消息中心</text>
      <view class="msg-nav-action" @tap="markAllRead" v-if="unreadCount > 0">全部已读</view>
    </view>

    <!-- Tab -->
    <view class="msg-tabs">
      <view
        v-for="tab in messageTabs" :key="tab.key"
        class="msg-tab" :class="{ 'msg-tab--active': activeTab === tab.key }"
        @tap="activeTab = tab.key"
      >
        {{ tab.label }}
        <view v-if="tab.badge > 0" class="msg-tab-badge">{{ tab.badge > 99 ? '99+' : tab.badge }}</view>
      </view>
    </view>

    <!-- 会话列表 -->
    <scroll-view scroll-y class="msg-list" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 学员会话 (教练视角) -->
      <template v-if="activeTab === 'students'">
        <view v-for="s in studentConversations" :key="s.id" class="msg-conv-card" @tap="goStudentDetail(s.id)">
          <view class="msg-conv-avatar" :style="{ background: s.risk_level >= 3 ? '#E74C3C' : '#27AE60' }">
            {{ (s.name || '?')[0] }}
          </view>
          <view class="msg-conv-body">
            <view class="msg-conv-header">
              <text class="msg-conv-name">{{ s.name }}</text>
              <text class="msg-conv-time">{{ s.last_time || '' }}</text>
            </view>
            <text class="msg-conv-preview">{{ s.last_message || '暂无消息' }}</text>
          </view>
          <view v-if="s.unread > 0" class="msg-conv-unread">{{ s.unread }}</view>
        </view>
        <view v-if="studentConversations.length === 0" class="msg-empty">
          <text class="msg-empty-icon">💬</text>
          <text class="msg-empty-text">暂无学员会话</text>
        </view>
      </template>

      <!-- 系统通知 -->
      <template v-if="activeTab === 'system' || activeTab === 'review'">
        <view v-for="n in filteredNotifications" :key="n.id" class="msg-notif-card" :class="{ 'msg-notif--unread': !n.is_read }" @tap="openNotification(n)">
          <view class="msg-notif-icon" :style="{ background: notifColor(n.type) }">
            {{ notifIcon(n.type) }}
          </view>
          <view class="msg-notif-body">
            <text class="msg-notif-title">{{ n.title }}</text>
            <text class="msg-notif-desc">{{ n.content }}</text>
            <text class="msg-notif-time">{{ formatTime(n.created_at) }}</text>
          </view>
          <view v-if="!n.is_read" class="msg-notif-dot"></view>
        </view>
        <view v-if="filteredNotifications.length === 0" class="msg-empty">
          <text class="msg-empty-icon">📭</text>
          <text class="msg-empty-text">暂无{{ activeTab === 'review' ? '审核' : '系统' }}通知</text>
        </view>
      </template>

      <!-- AI 消息建议 -->
      <template v-if="activeTab === 'ai'">
        <view class="msg-ai-hint">AI 根据学员数据自动生成的沟通建议</view>
        <view v-for="(sug, idx) in aiSuggestions" :key="idx" class="msg-ai-card">
          <view class="msg-ai-student">致：{{ sug.student_name }}</view>
          <text class="msg-ai-content">{{ sug.content }}</text>
          <view class="msg-ai-actions">
            <view class="msg-ai-btn msg-ai-btn--adopt" @tap="adoptSuggestion(sug)">✓ 采纳发送</view>
            <view class="msg-ai-btn msg-ai-btn--edit" @tap="editSuggestion(sug)">✎ 编辑</view>
          </view>
        </view>
        <view v-if="aiSuggestions.length === 0" class="msg-empty">
          <text class="msg-empty-icon">🤖</text>
          <text class="msg-empty-text">暂无AI消息建议</text>
        </view>
      </template>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const activeTab = ref('students')
const refreshing = ref(false)
const studentConversations = ref<any[]>([])
const notifications = ref<any[]>([])
const aiSuggestions = ref<any[]>([])

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

const messageTabs = computed(() => [
  { key: 'students', label: '学员', badge: studentConversations.value.reduce((sum, s) => sum + (s.unread || 0), 0) },
  { key: 'review', label: '审核', badge: notifications.value.filter(n => !n.is_read && (n.type === 'review' || n.type === 'assessment')).length },
  { key: 'ai', label: 'AI建议', badge: aiSuggestions.value.length },
  { key: 'system', label: '系统', badge: notifications.value.filter(n => !n.is_read && n.type === 'system').length },
])

const filteredNotifications = computed(() => {
  if (activeTab.value === 'review') return notifications.value.filter(n => n.type === 'review' || n.type === 'assessment')
  if (activeTab.value === 'system') return notifications.value.filter(n => n.type === 'system' || n.type === 'learning')
  return notifications.value
})

function notifColor(type: string): string {
  const map: Record<string, string> = { system: '#3498DB', review: '#E67E22', assessment: '#9B59B6', learning: '#27AE60' }
  return map[type] || '#5B6B7F'
}
function notifIcon(type: string): string {
  const map: Record<string, string> = { system: '🔔', review: '📋', assessment: '📊', learning: '📚' }
  return map[type] || '📩'
}
function formatTime(t: string): string {
  if (!t) return ''
  const d = new Date(t)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return (d.getMonth() + 1) + '/' + d.getDate() + ' ' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
}

async function loadData() {
  // 学员会话 (从dashboard获取)
  try {
    const res = await http<any>('/api/v1/coach/dashboard')
    const raw = res.students || res.data?.students || []
    studentConversations.value = (Array.isArray(raw) ? raw : []).map((s: any) => ({
      id: s.id || s.user_id,
      name: s.name || s.full_name || '未知',
      risk_level: s.risk_level ?? 0,
      last_message: s.last_action || '最近活跃' + (s.days_since_last_contact || '—') + '天前',
      last_time: '',
      unread: s.unread_count || 0,
    }))
  } catch (e) { console.warn('[coach/messages/index] dashboard:', e) }

  // 通知
  try {
    const res = await http<any>('/api/v1/notifications?page_size=50')
    notifications.value = res.items || res.notifications || res || []
  } catch {
    notifications.value = []
  }

  // AI建议 (遍历学员)
  try {
    const ids = studentConversations.value.map(s => s.id).slice(0, 5)
    const results: any[] = []
    for (const id of ids) {
      try {
        const res = await http<any>(`/api/v1/coach/messages/ai-suggestions/${id}`)
        const suggestions = res.suggestions || res.items || (Array.isArray(res) ? res : [])
        suggestions.forEach((s: any) => {
          results.push({
            student_id: id,
            student_name: studentConversations.value.find(st => st.id === id)?.name || '学员',
            content: s.content || s.message || s.text || JSON.stringify(s),
          })
        })
      } catch (e) { console.warn('[coach/messages/index] operation:', e) }
    }
    aiSuggestions.value = results
  } catch (e) { console.warn('[coach/messages/index] operation:', e) }
}

async function onRefresh() {
  refreshing.value = true
  await loadData()
  refreshing.value = false
}

async function markAllRead() {
  try { await http('/api/v1/notifications/mark-all-read', { method: 'POST' }) } catch (e) { console.warn('[coach/messages/index] markAllRead:', e) }
  notifications.value.forEach(n => n.is_read = true)
}

function openNotification(n: any) {
  if (!n.is_read) {
    n.is_read = true
    http(`/api/v1/notifications/${n.id}/read`, { method: 'POST' }).catch(() => {})
  }
  if (n.link) uni.navigateTo({ url: n.link })
}

function adoptSuggestion(sug: any) {
  uni.showToast({ title: '已采纳，准备发送', icon: 'success' })
}

function editSuggestion(sug: any) {
  uni.navigateTo({ url: '/pages/coach/students/detail?id=' + sug.student_id + '&tab=message' })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

function goStudentDetail(id: number) {
  uni.navigateTo({ url: '/pages/coach/students/detail?id=' + id })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.msg-page { min-height: 100vh; background: #F5F6FA; }
.msg-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%); color: #fff; }
.msg-nav-back { font-size: 40rpx; padding: 16rpx; }
.msg-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.msg-nav-action { font-size: 24rpx; padding: 8rpx 16rpx; background: rgba(255,255,255,0.2); border-radius: 8rpx; }

.msg-tabs { display: flex; padding: 16rpx 24rpx; gap: 12rpx; }
.msg-tab { position: relative; flex: 1; text-align: center; padding: 16rpx 0; border-radius: 12rpx; background: #fff; font-size: 26rpx; color: #5B6B7F; }
.msg-tab--active { background: #3498DB; color: #fff; }
.msg-tab-badge { position: absolute; top: -8rpx; right: 8rpx; min-width: 28rpx; height: 28rpx; border-radius: 14rpx; background: #E74C3C; color: #fff; font-size: 18rpx; display: flex; align-items: center; justify-content: center; padding: 0 6rpx; }

.msg-list { height: calc(100vh - 380rpx); padding: 0 24rpx; }

.msg-conv-card { display: flex; align-items: center; gap: 16rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; }
.msg-conv-avatar { width: 80rpx; height: 80rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 30rpx; font-weight: 600; flex-shrink: 0; }
.msg-conv-body { flex: 1; overflow: hidden; }
.msg-conv-header { display: flex; justify-content: space-between; align-items: center; }
.msg-conv-name { font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.msg-conv-time { font-size: 22rpx; color: #8E99A4; }
.msg-conv-preview { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 6rpx; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.msg-conv-unread { min-width: 36rpx; height: 36rpx; border-radius: 18rpx; background: #E74C3C; color: #fff; font-size: 22rpx; display: flex; align-items: center; justify-content: center; padding: 0 8rpx; }

.msg-notif-card { display: flex; align-items: flex-start; gap: 16rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; }
.msg-notif--unread { border-left: 4rpx solid #3498DB; }
.msg-notif-icon { width: 56rpx; height: 56rpx; border-radius: 12rpx; display: flex; align-items: center; justify-content: center; font-size: 28rpx; flex-shrink: 0; }
.msg-notif-body { flex: 1; }
.msg-notif-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.msg-notif-desc { display: block; font-size: 24rpx; color: #5B6B7F; margin-top: 6rpx; }
.msg-notif-time { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 8rpx; }
.msg-notif-dot { width: 12rpx; height: 12rpx; border-radius: 50%; background: #E74C3C; margin-top: 8rpx; flex-shrink: 0; }

.msg-ai-hint { text-align: center; font-size: 24rpx; color: #8E99A4; padding: 16rpx; }
.msg-ai-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; border-left: 4rpx solid #9B59B6; }
.msg-ai-student { font-size: 24rpx; color: #9B59B6; font-weight: 600; margin-bottom: 8rpx; }
.msg-ai-content { display: block; font-size: 28rpx; color: #2C3E50; line-height: 1.6; }
.msg-ai-actions { display: flex; gap: 16rpx; margin-top: 16rpx; }
.msg-ai-btn { flex: 1; text-align: center; padding: 14rpx 0; border-radius: 8rpx; font-size: 26rpx; }
.msg-ai-btn--adopt { background: #27AE60; color: #fff; }
.msg-ai-btn--edit { background: #F0F0F0; color: #5B6B7F; }

.msg-empty { text-align: center; padding: 120rpx 0; }
.msg-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.msg-empty-text { font-size: 28rpx; color: #8E99A4; }
</style>