<template>
  <view class="notif-page">
    <view class="notif-header">
      <text class="notif-title">消息中心</text>
      <text class="notif-mark-all" @tap="markAllRead" v-if="unreadCount > 0">全部已读</text>
    </view>

    <!-- Tab 筛选 -->
    <scroll-view scroll-x class="notif-tabs">
      <view v-for="t in tabs" :key="t.key"
        class="notif-tab" :class="{ 'notif-tab--active': activeTab === t.key }"
        @tap="activeTab = t.key">
        {{ t.label }}
        <view v-if="t.count > 0" class="notif-badge">{{ t.count > 99 ? '99+' : t.count }}</view>
      </view>
    </scroll-view>

    <!-- loading -->
    <view v-if="loading" class="notif-loading">
      <text class="notif-loading-text">加载中…</text>
    </view>

    <!-- AI建议 Tab -->
    <scroll-view v-else-if="activeTab === 'ai'" scroll-y class="notif-list"
      :style="{ height: scrollH }"
      refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view class="notif-ai-hint">AI 根据学员数据自动生成的沟通建议</view>
      <view v-for="(sg, idx) in aiSuggestions" :key="idx" class="notif-ai-card">
        <text class="notif-ai-student">致：{{ sg.student_name }}</text>
        <text class="notif-ai-content">{{ sg.content }}</text>
        <view class="notif-ai-actions">
          <view class="notif-ai-btn notif-ai-adopt" @tap="adoptSuggestion(sg)">✓ 采纳发送</view>
          <view class="notif-ai-btn notif-ai-edit" @tap="editSuggestion(sg)">✎ 编辑</view>
        </view>
      </view>
      <view v-if="aiSuggestions.length === 0" class="notif-empty">
        <text class="notif-empty-icon">🤖</text>
        <text class="notif-empty-text">暂无AI消息建议</text>
      </view>
    </scroll-view>

    <!-- 通知列表（全部/未读/审核/系统） -->
    <scroll-view v-else scroll-y class="notif-list"
      :style="{ height: scrollH }"
      refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
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
          <text class="notif-item-body">{{ n.body || n.content || '' }}</text>
          <text class="notif-item-time">{{ formatTime(n.created_at) }}</text>
        </view>
      </view>

      <view v-if="filteredItems.length === 0 && !loading" class="notif-empty">
        <text class="notif-empty-icon">🔔</text>
        <text class="notif-empty-text">暂无{{ tabLabel }}消息</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { httpReq as http } from '@/api/request'

const activeTab = ref('all')
const refreshing = ref(false)
const loading = ref(false)
const items = ref<any[]>([])
const aiSuggestions = ref<any[]>([])

// 用 JS 计算 scroll-view 高度，避免 calc(100vh - Xrpx) 在部分微信版本失效
const scrollH = ref('60vh')
onMounted(() => {
  try {
    const info = uni.getSystemInfoSync()
    const ratio = info.windowWidth / 750          // px per rpx
    const headerPx = (80 + 24 + 40) * ratio + info.statusBarHeight  // 约 144rpx + 状态栏
    const tabsPx   = 70 * ratio                   // 标签栏
    const h = Math.max(200, info.windowHeight - headerPx - tabsPx - 10)
    scrollH.value = h + 'px'
  } catch { scrollH.value = '60vh' }
})

// 角色检测：只有 coach/admin 才展示 AI建议 + 审核 Tab
const userRole = (() => {
  try {
    const raw = uni.getStorageSync('user_info')
    if (raw) {
      const u = typeof raw === 'string' ? JSON.parse(raw) : raw
      return (u.role || 'grower').toLowerCase()
    }
  } catch { /* ignore */ }
  return 'grower'
})()
const isCoach = ['coach', 'admin', 'supervisor', 'master'].includes(userRole)

const unreadCount = computed(() => items.value.filter(n => !n.is_read).length)

const tabs = computed(() => {
  const base = [
    { key: 'all',    label: '全部', count: unreadCount.value },
    { key: 'unread', label: '未读', count: unreadCount.value },
  ]
  if (isCoach) {
    base.push(
      { key: 'ai',     label: 'AI建议', count: aiSuggestions.value.length },
      { key: 'review', label: '审核',   count: items.value.filter(n => !n.is_read && ['review', 'assessment', 'assessment_remind'].includes(n.type)).length },
    )
  } else {
    base.push(
      { key: 'coach',  label: '教练消息', count: items.value.filter(n => !n.is_read && ['coach_message', 'assessment_result', 'assessment_remind'].includes(n.type)).length },
    )
  }
  base.push({ key: 'system', label: '系统', count: items.value.filter(n => !n.is_read && ['system', 'learning'].includes(n.type)).length })
  return base
})

const tabLabel = computed(() => {
  const m: Record<string, string> = { all: '', unread: '未读', review: '审核', system: '系统' }
  return m[activeTab.value] || ''
})

const filteredItems = computed(() => {
  if (activeTab.value === 'all')    return items.value
  if (activeTab.value === 'unread') return items.value.filter(n => !n.is_read)
  if (activeTab.value === 'review') return items.value.filter(n => ['review', 'assessment', 'assessment_remind'].includes(n.type))
  if (activeTab.value === 'coach')  return items.value.filter(n => ['coach_message', 'assessment_result', 'assessment_remind'].includes(n.type))
  if (activeTab.value === 'system') return items.value.filter(n => ['system', 'learning'].includes(n.type))
  return items.value
})

function typeIcon(t: string): string {
  const m: Record<string, string> = {
    review: '📋', assessment: '📊', assessment_remind: '⏰',
    system: '📣', learning: '📚', reminder: '⏰', alert: '⚠️',
  }
  return m[t] || '🔔'
}
function typeColor(t: string): string {
  const m: Record<string, string> = {
    review: '#3498DB', assessment: '#E67E22', assessment_remind: '#E67E22',
    system: '#9B59B6', learning: '#27AE60', alert: '#E74C3C',
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
  loading.value = true
  // 通知列表（兼容 limit / page_size 两种参数名）
  try {
    const res = await http<any>('/api/v1/notifications?limit=50&page_size=50')
    items.value = res.items || res.notifications || (Array.isArray(res) ? res : [])
  } catch (e) {
    console.warn('[notifications] load:', e)
    items.value = []
  } finally {
    loading.value = false
  }

  // AI建议：仅教练角色加载（避免 grower 触发 403）
  if (isCoach) {
    try {
      const dash = await http<any>('/api/v1/coach/dashboard')
      const students = (dash.students || []).slice(0, 5)
      const results: any[] = []
      for (const s of students) {
        try {
          const res = await http<any>(`/api/v1/coach/messages/ai-suggestions/${s.id || s.user_id}`)
          const sgs = res.suggestions || res.items || (Array.isArray(res) ? res : [])
          sgs.forEach((sg: any) => {
            results.push({
              student_id: s.id || s.user_id,
              student_name: s.name || s.full_name || '学员',
              content: sg.content || sg.text || sg.message || '',
            })
          })
        } catch (e) { console.warn('[notifications] ai-suggestions:', e) }
      }
      aiSuggestions.value = results
    } catch (e) { console.warn('[notifications] dashboard for ai:', e) }
  }
}

async function openNotif(n: any) {
  if (!n.is_read) {
    try {
      await http(`/api/v1/notifications/${n.id}/read`, { method: 'POST' })
      n.is_read = true
    } catch (e) { console.warn('[notifications] openNotif:', e) }
  }
  const coachLinks: Record<string, string> = {
    review: '/pages/coach/assessment/index',
    assessment: '/pages/coach/assessment/index',
    assessment_remind: '/pages/coach/assessment/index',
    learning: '/pages/learning/index',
  }
  const growerLinks: Record<string, string> = {
    assessment: '/pages/assessment/pending',
    assessment_remind: '/pages/assessment/pending',
    assessment_result: '/pages/assessment/pending',
    learning: '/pages/learning/index',
  }
  const links = isCoach ? coachLinks : growerLinks
  const url = links[n.type]
  if (url) uni.navigateTo({ url }).catch(() => {})
}

async function markAllRead() {
  try {
    await http('/api/v1/notifications/read-all', { method: 'POST' })
  } catch {
    await Promise.allSettled(
      items.value.filter(n => !n.is_read).map(n =>
        http(`/api/v1/notifications/${n.id}/read`, { method: 'POST' })
      )
    )
  }
  items.value.forEach(n => n.is_read = true)
  uni.showToast({ title: '已全部标记已读', icon: 'success' })
}

async function adoptSuggestion(sg: any) {
  const content = (sg.content || '').trim()
  if (!content) {
    uni.showToast({ title: 'AI建议内容为空，请手动编辑', icon: 'none' })
    return
  }
  try {
    await http('/api/v1/coach/messages', {
      method: 'POST',
      data: { student_id: sg.student_id, content, message_type: 'text', auto_approve: true }
    })
    uni.showToast({ title: '消息已发送给学员', icon: 'success' })
  } catch (e) {
    console.warn('[notifications] adoptSuggestion:', e)
    uni.showToast({ title: '发送失败，请重试', icon: 'none' })
  }
}

function editSuggestion(sg: any) {
  // 跳转到学员档案督导Tab，在内联Modal中编辑后发送
  uni.navigateTo({ url: '/pages/coach/students/detail?id=' + sg.student_id + '&tab=supervision' })
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }

onShow(() => { loadData() })
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

/* 高度由 JS getSystemInfoSync 动态注入，CSS 不再写 calc(100vh - Xrpx) */
.notif-list { min-height: 200rpx; }

.notif-loading { display: flex; align-items: center; justify-content: center; padding: 120rpx 0; }
.notif-loading-text { font-size: 28rpx; color: #8E99A4; }

/* ── 通知列表 ── */
.notif-item {
  display: flex; align-items: flex-start; gap: 20rpx;
  background: #fff; padding: 24rpx 32rpx;
  border-bottom: 1rpx solid #F8F8F8;
}
.notif-item--unread { background: #FAFFFE; }
.notif-icon-wrap {
  width: 72rpx; height: 72rpx; border-radius: 18rpx;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.notif-icon { font-size: 36rpx; }
.notif-body { flex: 1; min-width: 0; }
.notif-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8rpx; }
.notif-item-title { font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.notif-dot { width: 14rpx; height: 14rpx; border-radius: 50%; background: #E74C3C; flex-shrink: 0; }
.notif-item-body { display: block; font-size: 24rpx; color: #5B6B7F; line-height: 1.5; margin-bottom: 8rpx; }
.notif-item-time { display: block; font-size: 22rpx; color: #BDC3C7; }

/* ── AI建议 ── */
.notif-ai-hint { text-align: center; font-size: 24rpx; color: #8E99A4; padding: 16rpx 32rpx; }
.notif-ai-card {
  background: #fff; margin: 0 24rpx 12rpx; border-radius: 16rpx;
  padding: 24rpx; border-left: 4rpx solid #9B59B6;
}
.notif-ai-student { display: block; font-size: 24rpx; color: #9B59B6; font-weight: 600; margin-bottom: 8rpx; }
.notif-ai-content { display: block; font-size: 28rpx; color: #2C3E50; line-height: 1.6; }
.notif-ai-actions { display: flex; gap: 16rpx; margin-top: 16rpx; }
.notif-ai-btn { flex: 1; text-align: center; padding: 14rpx 0; border-radius: 8rpx; font-size: 26rpx; }
.notif-ai-adopt { background: #27AE60; color: #fff; }
.notif-ai-edit { background: #F0F0F0; color: #5B6B7F; }

/* ── 空状态 ── */
.notif-empty { text-align: center; padding: 120rpx 0; }
.notif-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.notif-empty-text { font-size: 28rpx; color: #8E99A4; }
</style>
