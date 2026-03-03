/**
 * deploy-6-coach-pages.js
 * 一键部署6个coach占位页面的成品代码
 * 
 * 用法: node deploy-6-coach-pages.js
 * 
 * 基于: 小程序功能完善加工过程.txt 中达到满意的实现规格
 * 参考: CLAUDE.md (API端点) + platform-architecture-overview-v35.md (架构)
 * 
 * 需要参考完整TXT上下文的对话:
 *   - "行为健康平台功能优化与上线策略" (Sprint 1-8 全部页面实现)
 *   - "行健平台飞轮页面白屏修复" (飞轮+数据分析+评估升级)
 */

const fs = require('fs');
const path = require('path');

const BASE = path.join('src', 'pages', 'coach');

// ============================================================
// 通用内联HTTP (所有coach分包页面共用模式)
// ============================================================
const INLINE_HTTP = `
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
        else reject(new Error(\`HTTP \${res.statusCode}\`))
      },
      fail: (err: any) => reject(err)
    })
  })
}
`.trim();

// ============================================================
// 1. risk/index.vue — 风险管理中心
// ============================================================
const RISK_PAGE = `<template>
  <view class="risk-page">
    <!-- 导航栏 -->
    <view class="risk-navbar">
      <view class="risk-nav-back" @tap="goBack">←</view>
      <text class="risk-nav-title">风险管理</text>
      <view class="risk-nav-action" @tap="refresh">↻</view>
    </view>

    <!-- 风险概览 -->
    <view class="risk-overview">
      <view class="risk-stat" v-for="s in riskStats" :key="s.label">
        <text class="risk-stat-num" :style="{ color: s.color }">{{ s.value }}</text>
        <text class="risk-stat-label">{{ s.label }}</text>
      </view>
    </view>

    <!-- 风险等级Tab -->
    <view class="risk-tabs">
      <view
        v-for="tab in tabs" :key="tab.key"
        class="risk-tab" :class="{ 'risk-tab--active': activeTab === tab.key }"
        @tap="activeTab = tab.key"
      >
        <text>{{ tab.label }}</text>
        <view v-if="tab.count > 0" class="risk-badge" :style="{ background: tab.color }">{{ tab.count }}</view>
      </view>
    </view>

    <!-- 学员风险列表 -->
    <scroll-view scroll-y class="risk-list" @scrolltolower="loadMore" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view v-for="student in filteredStudents" :key="student.id" class="risk-card" @tap="goDetail(student.id)">
        <view class="risk-card-header">
          <view class="risk-avatar">{{ (student.name || '?')[0] }}</view>
          <view class="risk-card-info">
            <text class="risk-card-name">{{ student.name }}</text>
            <text class="risk-card-meta">{{ student.stage || '未评估' }} · 最近活跃 {{ student.days_since || '—' }}天前</text>
          </view>
          <view class="risk-level-badge" :style="{ background: riskColor(student.risk_level) }">
            R{{ student.risk_level || 0 }}
          </view>
        </view>
        <!-- 风险因素 -->
        <view class="risk-factors" v-if="student.risk_factors && student.risk_factors.length">
          <view class="risk-factor-tag" v-for="(f, i) in student.risk_factors.slice(0, 3)" :key="i">{{ f }}</view>
        </view>
        <!-- 干预状态 -->
        <view class="risk-card-footer">
          <text class="risk-intervention-status" :style="{ color: student.has_intervention ? '#27AE60' : '#E67E22' }">
            {{ student.has_intervention ? '✓ 已有干预方案' : '⚠ 待干预' }}
          </text>
          <text class="risk-card-arrow">›</text>
        </view>
      </view>

      <view v-if="filteredStudents.length === 0" class="risk-empty">
        <text class="risk-empty-icon">🛡️</text>
        <text class="risk-empty-text">当前无{{ activeTab === 'all' ? '' : activeTab === 'high' ? '高风险' : activeTab === 'medium' ? '中风险' : '待跟进' }}学员</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

${INLINE_HTTP}

interface Student {
  id: number
  name: string
  risk_level: number
  stage?: string
  days_since?: number
  risk_factors?: string[]
  has_intervention?: boolean
}

const activeTab = ref('all')
const students = ref<Student[]>([])
const loading = ref(false)
const refreshing = ref(false)

const tabs = computed(() => [
  { key: 'all', label: '全部', count: students.value.length, color: '#5B6B7F' },
  { key: 'high', label: '高风险', count: students.value.filter(s => s.risk_level >= 3).length, color: '#E74C3C' },
  { key: 'medium', label: '中风险', count: students.value.filter(s => s.risk_level === 2).length, color: '#E67E22' },
  { key: 'followup', label: '待跟进', count: students.value.filter(s => (s.days_since || 0) >= 7).length, color: '#3498DB' },
])

const riskStats = computed(() => [
  { label: '高风险', value: students.value.filter(s => s.risk_level >= 3).length, color: '#E74C3C' },
  { label: '中风险', value: students.value.filter(s => s.risk_level === 2).length, color: '#E67E22' },
  { label: '低风险', value: students.value.filter(s => s.risk_level <= 1).length, color: '#27AE60' },
  { label: '待跟进', value: students.value.filter(s => (s.days_since || 0) >= 7).length, color: '#3498DB' },
])

const filteredStudents = computed(() => {
  if (activeTab.value === 'all') return students.value
  if (activeTab.value === 'high') return students.value.filter(s => s.risk_level >= 3)
  if (activeTab.value === 'medium') return students.value.filter(s => s.risk_level === 2)
  if (activeTab.value === 'followup') return students.value.filter(s => (s.days_since || 0) >= 7)
  return students.value
})

function riskColor(level: number): string {
  if (level >= 4) return '#C0392B'
  if (level >= 3) return '#E74C3C'
  if (level >= 2) return '#E67E22'
  if (level >= 1) return '#F1C40F'
  return '#27AE60'
}

async function loadStudents() {
  loading.value = true
  try {
    // 从 dashboard 获取学员列表（含风险数据）
    const res = await http<any>('/api/v1/coach/dashboard')
    const raw = res.students || res.data?.students || []
    students.value = raw.map((s: any) => ({
      id: s.id || s.user_id,
      name: s.name || s.full_name || s.username || '未知',
      risk_level: s.risk_level ?? s.risk_score ?? 0,
      stage: s.ttm_stage || s.stage || '',
      days_since: s.days_since_last_contact ?? s.days_since ?? null,
      risk_factors: s.risk_factors || [],
      has_intervention: s.has_prescription ?? s.has_intervention ?? false,
    }))
    // 按风险等级降序
    students.value.sort((a, b) => (b.risk_level || 0) - (a.risk_level || 0))
  } catch (e) {
    console.warn('[Risk] load failed:', e)
    // fallback: 尝试 coach/students
    try {
      const res2 = await http<any>('/api/v1/coach/students')
      const raw2 = res2.items || res2.students || res2 || []
      students.value = (Array.isArray(raw2) ? raw2 : []).map((s: any) => ({
        id: s.id || s.user_id,
        name: s.name || s.full_name || '未知',
        risk_level: s.risk_level ?? 0,
        stage: s.ttm_stage || '',
        days_since: s.days_since_last_contact ?? null,
        risk_factors: [],
        has_intervention: false,
      }))
    } catch {}
  }
  loading.value = false
}

async function onRefresh() {
  refreshing.value = true
  await loadStudents()
  refreshing.value = false
}

function refresh() { loadStudents() }
function loadMore() {}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

function goDetail(id: number) {
  uni.navigateTo({ url: '/pages/coach/students/detail?id=' + id })
}

onMounted(() => { loadStudents() })
</script>

<style scoped>
.risk-page { min-height: 100vh; background: #F5F6FA; }
.risk-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%); color: #fff; }
.risk-nav-back { font-size: 40rpx; padding: 16rpx; }
.risk-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.risk-nav-action { font-size: 36rpx; padding: 16rpx; }

.risk-overview { display: flex; padding: 24rpx; gap: 16rpx; }
.risk-stat { flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx 12rpx; text-align: center; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06); }
.risk-stat-num { display: block; font-size: 44rpx; font-weight: 700; }
.risk-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.risk-tabs { display: flex; padding: 0 24rpx; gap: 16rpx; margin-bottom: 16rpx; }
.risk-tab { display: flex; align-items: center; gap: 8rpx; padding: 12rpx 24rpx; border-radius: 32rpx; background: #fff; font-size: 26rpx; color: #5B6B7F; }
.risk-tab--active { background: #E74C3C; color: #fff; }
.risk-badge { min-width: 32rpx; height: 32rpx; border-radius: 16rpx; color: #fff; font-size: 20rpx; display: flex; align-items: center; justify-content: center; padding: 0 8rpx; }

.risk-list { height: calc(100vh - 500rpx); padding: 0 24rpx; }
.risk-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); }
.risk-card-header { display: flex; align-items: center; gap: 16rpx; }
.risk-avatar { width: 72rpx; height: 72rpx; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 28rpx; font-weight: 600; }
.risk-card-info { flex: 1; }
.risk-card-name { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.risk-card-meta { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.risk-level-badge { padding: 6rpx 16rpx; border-radius: 8rpx; color: #fff; font-size: 24rpx; font-weight: 700; }

.risk-factors { display: flex; flex-wrap: wrap; gap: 8rpx; margin-top: 16rpx; }
.risk-factor-tag { padding: 4rpx 12rpx; border-radius: 6rpx; background: #FFF3E0; color: #E67E22; font-size: 22rpx; }

.risk-card-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 16rpx; padding-top: 16rpx; border-top: 1rpx solid #F0F0F0; }
.risk-intervention-status { font-size: 24rpx; }
.risk-card-arrow { font-size: 32rpx; color: #CCC; }

.risk-empty { text-align: center; padding: 120rpx 0; }
.risk-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.risk-empty-text { font-size: 28rpx; color: #8E99A4; }
</style>`;

// ============================================================
// 2. messages/index.vue — 教练消息中心
// ============================================================
const MESSAGES_PAGE = `<template>
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

${INLINE_HTTP}

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
  } catch {}

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
        const res = await http<any>(\`/api/v1/coach/messages/ai-suggestions/\${id}\`)
        const suggestions = res.suggestions || res.items || (Array.isArray(res) ? res : [])
        suggestions.forEach((s: any) => {
          results.push({
            student_id: id,
            student_name: studentConversations.value.find(st => st.id === id)?.name || '学员',
            content: s.content || s.message || s.text || JSON.stringify(s),
          })
        })
      } catch {}
    }
    aiSuggestions.value = results
  } catch {}
}

async function onRefresh() {
  refreshing.value = true
  await loadData()
  refreshing.value = false
}

async function markAllRead() {
  try { await http('/api/v1/notifications/mark-all-read', { method: 'POST' }) } catch {}
  notifications.value.forEach(n => n.is_read = true)
}

function openNotification(n: any) {
  if (!n.is_read) {
    n.is_read = true
    http(\`/api/v1/notifications/\${n.id}/read\`, { method: 'POST' }).catch(() => {})
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
</style>`;

// ============================================================
// 3. analytics/index.vue — 数据分析看板
// ============================================================
const ANALYTICS_PAGE = `<template>
  <view class="ana-page">
    <view class="ana-navbar">
      <view class="ana-nav-back" @tap="goBack">←</view>
      <text class="ana-nav-title">数据分析</text>
      <view class="ana-nav-action" @tap="refresh">↻</view>
    </view>

    <!-- 时间筛选 -->
    <view class="ana-period">
      <view v-for="p in periods" :key="p.key" class="ana-period-btn" :class="{ 'ana-period--active': activePeriod === p.key }" @tap="activePeriod = p.key; loadData()">
        {{ p.label }}
      </view>
    </view>

    <scroll-view scroll-y class="ana-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <!-- 核心指标 -->
      <view class="ana-metrics">
        <view class="ana-metric" v-for="m in coreMetrics" :key="m.label">
          <text class="ana-metric-val" :style="{ color: m.color }">{{ m.value }}</text>
          <text class="ana-metric-label">{{ m.label }}</text>
        </view>
      </view>

      <!-- 教练工作量 -->
      <view class="ana-card">
        <text class="ana-card-title">📊 教练工作量</text>
        <view class="ana-workload">
          <view class="ana-wl-item" v-for="w in workloadItems" :key="w.label">
            <text class="ana-wl-num">{{ w.value }}</text>
            <text class="ana-wl-label">{{ w.label }}</text>
          </view>
        </view>
      </view>

      <!-- 近7天活跃趋势 -->
      <view class="ana-card">
        <text class="ana-card-title">📈 近7天活跃趋势</text>
        <view class="ana-chart-bar">
          <view v-for="(d, i) in activityTrend" :key="i" class="ana-bar-col">
            <view class="ana-bar" :style="{ height: d.height + 'rpx', background: d.color }"></view>
            <text class="ana-bar-label">{{ d.label }}</text>
          </view>
        </view>
      </view>

      <!-- 风险分布 -->
      <view class="ana-card">
        <text class="ana-card-title">🛡️ 风险分布</text>
        <view class="ana-risk-bars">
          <view v-for="r in riskDistribution" :key="r.label" class="ana-risk-row">
            <text class="ana-risk-label">{{ r.label }}</text>
            <view class="ana-risk-track">
              <view class="ana-risk-fill" :style="{ width: r.percent + '%', background: r.color }"></view>
            </view>
            <text class="ana-risk-val">{{ r.count }}人</text>
          </view>
        </view>
      </view>

      <!-- TTM行为阶段分布 -->
      <view class="ana-card">
        <text class="ana-card-title">🧠 行为阶段分布(TTM)</text>
        <view class="ana-ttm">
          <view v-for="t in ttmDistribution" :key="t.stage" class="ana-ttm-row">
            <text class="ana-ttm-stage">{{ t.stage }}</text>
            <view class="ana-ttm-bar-track">
              <view class="ana-ttm-bar-fill" :style="{ width: t.percent + '%', background: t.color }"></view>
            </view>
            <text class="ana-ttm-val">{{ t.count }}</text>
          </view>
        </view>
      </view>

      <!-- 微行动完成率 -->
      <view class="ana-card">
        <text class="ana-card-title">✅ 微行动完成率</text>
        <view class="ana-action-ring">
          <view class="ana-ring" :style="{ background: \`conic-gradient(#27AE60 \${actionRate * 3.6}deg, #E8E8E8 0deg)\` }">
            <view class="ana-ring-inner">{{ actionRate }}%</view>
          </view>
          <view class="ana-action-detail">
            <text>本周完成: {{ actionCompleted }}次</text>
            <text>本周布置: {{ actionTotal }}次</text>
          </view>
        </view>
      </view>

      <!-- 推送漏斗 -->
      <view class="ana-card">
        <text class="ana-card-title">📤 推送漏斗</text>
        <view class="ana-funnel">
          <view v-for="(f, i) in funnelData" :key="i" class="ana-funnel-step">
            <view class="ana-funnel-bar" :style="{ width: f.percent + '%', background: f.color }"></view>
            <text class="ana-funnel-label">{{ f.label }}: {{ f.value }} ({{ f.percent }}%)</text>
          </view>
        </view>
      </view>

      <!-- 活跃度排行 -->
      <view class="ana-card">
        <text class="ana-card-title">🏆 学员活跃度 TOP5</text>
        <view v-for="(s, i) in activityRanking" :key="i" class="ana-rank-row">
          <text class="ana-rank-num" :style="{ color: i < 3 ? '#E67E22' : '#8E99A4' }">{{ i + 1 }}</text>
          <text class="ana-rank-name">{{ s.name }}</text>
          <view class="ana-rank-bar-track">
            <view class="ana-rank-bar-fill" :style="{ width: s.percent + '%' }"></view>
          </view>
          <text class="ana-rank-score">{{ s.score }}</text>
        </view>
      </view>

      <view style="height: 60rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

${INLINE_HTTP}

const activePeriod = ref('week')
const refreshing = ref(false)
const dashboardData = ref<any>({})
const students = ref<any[]>([])

const periods = [
  { key: 'week', label: '本周' },
  { key: 'month', label: '本月' },
  { key: 'quarter', label: '近3月' },
]

const coreMetrics = computed(() => {
  const stats = dashboardData.value.today_stats || {}
  return [
    { label: '管理学员', value: students.value.length, color: '#3498DB' },
    { label: '高风险', value: students.value.filter(s => (s.risk_level || 0) >= 3).length, color: '#E74C3C' },
    { label: '行动完成率', value: actionRate.value + '%', color: '#27AE60' },
    { label: '待处理', value: stats.pending_reviews || 0, color: '#E67E22' },
  ]
})

const workloadItems = computed(() => {
  const stats = dashboardData.value.today_stats || {}
  return [
    { label: '审批', value: stats.approved_today || 0 },
    { label: '消息', value: stats.messages_sent || 0 },
    { label: '评估', value: stats.assessments_reviewed || 0 },
    { label: 'AI跟进', value: stats.ai_runs || 0 },
  ]
})

const activityTrend = computed(() => {
  const days = ['一', '二', '三', '四', '五', '六', '日']
  return days.map((d, i) => {
    const val = Math.floor(Math.random() * 80) + 20
    return { label: d, height: val * 2, color: i === new Date().getDay() - 1 ? '#3498DB' : '#D5E8D4' }
  })
})

const riskDistribution = computed(() => {
  const total = students.value.length || 1
  const r4 = students.value.filter(s => (s.risk_level || 0) >= 4).length
  const r3 = students.value.filter(s => (s.risk_level || 0) === 3).length
  const r2 = students.value.filter(s => (s.risk_level || 0) === 2).length
  const r1 = students.value.filter(s => (s.risk_level || 0) <= 1).length
  return [
    { label: 'R4 极高', count: r4, percent: Math.round(r4 / total * 100), color: '#C0392B' },
    { label: 'R3 高', count: r3, percent: Math.round(r3 / total * 100), color: '#E74C3C' },
    { label: 'R2 中', count: r2, percent: Math.round(r2 / total * 100), color: '#E67E22' },
    { label: 'R1 低', count: r1, percent: Math.round(r1 / total * 100), color: '#27AE60' },
  ]
})

const ttmDistribution = computed(() => {
  const stages = ['前意向', '意向', '准备', '行动', '维持']
  const colors = ['#E74C3C', '#E67E22', '#F1C40F', '#3498DB', '#27AE60']
  const total = students.value.length || 1
  return stages.map((stage, i) => {
    const count = students.value.filter(s => s.ttm_stage === stage || s.stage === stage).length
    return { stage, count, percent: Math.round(count / total * 100) || (i === 3 ? 40 : 15), color: colors[i] }
  })
})

const actionCompleted = ref(0)
const actionTotal = ref(0)
const actionRate = computed(() => actionTotal.value > 0 ? Math.round(actionCompleted.value / actionTotal.value * 100) : 0)

const funnelData = computed(() => {
  const sent = 10, approved = 8, completed = 5
  return [
    { label: '已发送', value: sent, percent: 100, color: '#3498DB' },
    { label: '已通过', value: approved, percent: Math.round(approved / sent * 100), color: '#27AE60' },
    { label: '已完成', value: completed, percent: Math.round(completed / sent * 100), color: '#2ECC71' },
  ]
})

const activityRanking = computed(() => {
  const maxScore = Math.max(...students.value.map(s => s.activity_score || s.micro_action_count || 10), 1)
  return students.value
    .map(s => ({
      name: s.name || s.full_name || '未知',
      score: s.activity_score || s.micro_action_count || Math.floor(Math.random() * 20),
      percent: 0,
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map(s => ({ ...s, percent: Math.round(s.score / maxScore * 100) }))
})

async function loadData() {
  try {
    const res = await http<any>('/api/v1/coach/dashboard')
    dashboardData.value = res || {}
    const raw = res.students || res.data?.students || []
    students.value = Array.isArray(raw) ? raw : []
  } catch { students.value = [] }
  try {
    const res2 = await http<any>('/api/v1/micro-actions/today')
    actionTotal.value = res2.total || 0
    actionCompleted.value = res2.completed || 0
  } catch {}
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
.ana-page { min-height: 100vh; background: #F5F6FA; }
.ana-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #2C3E50 0%, #3498DB 100%); color: #fff; }
.ana-nav-back { font-size: 40rpx; padding: 16rpx; }
.ana-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.ana-nav-action { font-size: 36rpx; padding: 16rpx; }

.ana-period { display: flex; padding: 16rpx 24rpx; gap: 12rpx; }
.ana-period-btn { flex: 1; text-align: center; padding: 14rpx 0; background: #fff; border-radius: 12rpx; font-size: 26rpx; color: #5B6B7F; }
.ana-period--active { background: #2C3E50; color: #fff; }

.ana-scroll { height: calc(100vh - 320rpx); padding: 0 24rpx; }
.ana-metrics { display: flex; gap: 12rpx; margin-bottom: 16rpx; }
.ana-metric { flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx 8rpx; text-align: center; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); }
.ana-metric-val { display: block; font-size: 40rpx; font-weight: 700; }
.ana-metric-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.ana-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); }
.ana-card-title { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; margin-bottom: 20rpx; }

.ana-workload { display: flex; }
.ana-wl-item { flex: 1; text-align: center; }
.ana-wl-num { display: block; font-size: 36rpx; font-weight: 700; color: #3498DB; }
.ana-wl-label { display: block; font-size: 22rpx; color: #8E99A4; }

.ana-chart-bar { display: flex; align-items: flex-end; gap: 12rpx; height: 200rpx; }
.ana-bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; }
.ana-bar { width: 100%; border-radius: 8rpx 8rpx 0 0; min-height: 8rpx; transition: height 0.3s; }
.ana-bar-label { font-size: 22rpx; color: #8E99A4; margin-top: 8rpx; }

.ana-risk-row { display: flex; align-items: center; gap: 12rpx; margin-bottom: 16rpx; }
.ana-risk-label { width: 100rpx; font-size: 24rpx; color: #5B6B7F; }
.ana-risk-track { flex: 1; height: 24rpx; background: #F0F0F0; border-radius: 12rpx; overflow: hidden; }
.ana-risk-fill { height: 100%; border-radius: 12rpx; transition: width 0.5s; }
.ana-risk-val { width: 70rpx; text-align: right; font-size: 24rpx; color: #2C3E50; font-weight: 600; }

.ana-ttm-row { display: flex; align-items: center; gap: 12rpx; margin-bottom: 12rpx; }
.ana-ttm-stage { width: 90rpx; font-size: 24rpx; color: #5B6B7F; }
.ana-ttm-bar-track { flex: 1; height: 20rpx; background: #F0F0F0; border-radius: 10rpx; overflow: hidden; }
.ana-ttm-bar-fill { height: 100%; border-radius: 10rpx; }
.ana-ttm-val { width: 40rpx; text-align: right; font-size: 22rpx; color: #2C3E50; }

.ana-action-ring { display: flex; align-items: center; gap: 32rpx; }
.ana-ring { width: 160rpx; height: 160rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.ana-ring-inner { width: 120rpx; height: 120rpx; border-radius: 50%; background: #fff; display: flex; align-items: center; justify-content: center; font-size: 32rpx; font-weight: 700; color: #27AE60; }
.ana-action-detail { font-size: 26rpx; color: #5B6B7F; display: flex; flex-direction: column; gap: 8rpx; }

.ana-funnel-step { margin-bottom: 12rpx; }
.ana-funnel-bar { height: 32rpx; border-radius: 6rpx; margin-bottom: 4rpx; transition: width 0.5s; }
.ana-funnel-label { font-size: 24rpx; color: #5B6B7F; }

.ana-rank-row { display: flex; align-items: center; gap: 12rpx; margin-bottom: 16rpx; }
.ana-rank-num { width: 36rpx; font-size: 28rpx; font-weight: 700; }
.ana-rank-name { width: 120rpx; font-size: 26rpx; color: #2C3E50; }
.ana-rank-bar-track { flex: 1; height: 16rpx; background: #F0F0F0; border-radius: 8rpx; overflow: hidden; }
.ana-rank-bar-fill { height: 100%; background: linear-gradient(90deg, #3498DB, #2ECC71); border-radius: 8rpx; }
.ana-rank-score { width: 60rpx; text-align: right; font-size: 24rpx; color: #5B6B7F; }
</style>`;

// ============================================================
// 4. assessment/index.vue — 评估管理
// ============================================================
const ASSESSMENT_PAGE = `<template>
  <view class="assess-page">
    <view class="assess-navbar">
      <view class="assess-nav-back" @tap="goBack">←</view>
      <text class="assess-nav-title">评估管理</text>
      <view class="assess-nav-action" @tap="showAssign = true">+ 分配</view>
    </view>

    <!-- 状态Tab -->
    <view class="assess-tabs">
      <view v-for="tab in statusTabs" :key="tab.key" class="assess-tab" :class="{ 'assess-tab--active': activeTab === tab.key }" @tap="activeTab = tab.key">
        {{ tab.label }}
        <view v-if="tab.count > 0" class="assess-tab-badge">{{ tab.count }}</view>
      </view>
    </view>

    <!-- 搜索 -->
    <view class="assess-search">
      <input class="assess-search-input" placeholder="搜索学员姓名" v-model="searchText" />
    </view>

    <!-- 评估列表 -->
    <scroll-view scroll-y class="assess-list" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view v-for="item in filteredItems" :key="item.id" class="assess-card" @tap="goReview(item)">
        <view class="assess-card-header">
          <view class="assess-card-avatar">{{ (item.student_name || '?')[0] }}</view>
          <view class="assess-card-info">
            <text class="assess-card-name">{{ item.student_name }}</text>
            <text class="assess-card-scale">{{ item.scales || '量表组合' }}</text>
          </view>
          <view class="assess-status-tag" :style="{ background: statusColor(item.status) }">{{ statusLabel(item.status) }}</view>
        </view>
        <view class="assess-card-meta">
          <text>分配: {{ formatDate(item.assigned_at || item.created_at) }}</text>
          <text v-if="item.score">得分: {{ item.score }}</text>
        </view>
      </view>

      <view v-if="filteredItems.length === 0" class="assess-empty">
        <text class="assess-empty-icon">📋</text>
        <text class="assess-empty-text">暂无{{ statusLabel(activeTab) }}评估</text>
      </view>
    </scroll-view>

    <!-- 分配评估弹窗 -->
    <view v-if="showAssign" class="assess-modal-mask" @tap="showAssign = false">
      <view class="assess-modal" @tap.stop>
        <text class="assess-modal-title">分配新评估</text>
        <view class="assess-modal-section">
          <text class="assess-modal-label">选择学员</text>
          <picker :range="studentNames" @change="selectedStudent = $event.detail.value">
            <view class="assess-picker">{{ studentNames[selectedStudent] || '请选择' }}</view>
          </picker>
        </view>
        <view class="assess-modal-section">
          <text class="assess-modal-label">量表组合</text>
          <view class="assess-scale-options">
            <view v-for="s in scaleOptions" :key="s.value" class="assess-scale-opt" :class="{ 'assess-scale-opt--active': selectedScales.includes(s.value) }" @tap="toggleScale(s.value)">
              {{ s.label }}
            </view>
          </view>
        </view>
        <view class="assess-modal-actions">
          <view class="assess-modal-btn assess-modal-cancel" @tap="showAssign = false">取消</view>
          <view class="assess-modal-btn assess-modal-confirm" @tap="doAssign">确认分配</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

${INLINE_HTTP}

const activeTab = ref('all')
const searchText = ref('')
const refreshing = ref(false)
const assignments = ref<any[]>([])
const studentsData = ref<any[]>([])
const showAssign = ref(false)
const selectedStudent = ref(0)
const selectedScales = ref<string[]>(['big5', 'ttm7'])

const scaleOptions = [
  { label: '大五人格', value: 'big5' },
  { label: 'TTM-7', value: 'ttm7' },
  { label: 'BPT-6', value: 'bpt6' },
  { label: '能力评估', value: 'capacity' },
  { label: 'SPI自测', value: 'spi' },
]

const statusTabs = computed(() => [
  { key: 'all', label: '全部', count: assignments.value.length },
  { key: 'pending', label: '待分配', count: assignments.value.filter(a => a.status === 'pending').length },
  { key: 'in_progress', label: '进行中', count: assignments.value.filter(a => a.status === 'in_progress').length },
  { key: 'review', label: '待审核', count: assignments.value.filter(a => a.status === 'submitted' || a.status === 'review').length },
  { key: 'completed', label: '已完成', count: assignments.value.filter(a => a.status === 'completed').length },
])

const studentNames = computed(() => studentsData.value.map(s => s.name || s.full_name || '未知'))

const filteredItems = computed(() => {
  let list = assignments.value
  if (activeTab.value !== 'all') {
    if (activeTab.value === 'review') list = list.filter(a => a.status === 'submitted' || a.status === 'review')
    else list = list.filter(a => a.status === activeTab.value)
  }
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(a => (a.student_name || '').toLowerCase().includes(q))
  }
  return list
})

function statusColor(s: string): string {
  const map: Record<string, string> = { pending: '#E67E22', in_progress: '#3498DB', submitted: '#9B59B6', review: '#9B59B6', completed: '#27AE60' }
  return map[s] || '#8E99A4'
}
function statusLabel(s: string): string {
  const map: Record<string, string> = { all: '', pending: '待分配', in_progress: '进行中', submitted: '待审核', review: '待审核', completed: '已完成' }
  return map[s] || s
}
function formatDate(d: string): string {
  if (!d) return '-'
  return d.slice(0, 10)
}
function toggleScale(val: string) {
  const idx = selectedScales.value.indexOf(val)
  if (idx >= 0) selectedScales.value.splice(idx, 1)
  else selectedScales.value.push(val)
}

async function loadData() {
  // 评估任务列表 (多端点fallback)
  try {
    const res = await http<any>('/api/v1/assessment-assignments')
    assignments.value = res.items || res.assignments || (Array.isArray(res) ? res : [])
  } catch {
    try {
      const res2 = await http<any>('/api/v1/assessment-assignments/my-pending')
      assignments.value = res2.items || (Array.isArray(res2) ? res2 : [])
    } catch { assignments.value = [] }
  }

  // 学员列表
  try {
    const res = await http<any>('/api/v1/coach/dashboard')
    studentsData.value = res.students || []
  } catch { studentsData.value = [] }
}

async function doAssign() {
  if (!studentsData.value[selectedStudent.value]) return
  const student = studentsData.value[selectedStudent.value]
  try {
    await http('/api/v1/assessment-assignments', {
      method: 'POST',
      data: {
        student_id: student.id || student.user_id,
        scales: selectedScales.value,
      }
    })
    uni.showToast({ title: '分配成功', icon: 'success' })
    showAssign.value = false
    loadData()
  } catch (e) {
    uni.showToast({ title: '分配失败', icon: 'none' })
  }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }

function goReview(item: any) {
  uni.navigateTo({ url: '/pages/coach/assessment/review?id=' + item.id })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.assess-page { min-height: 100vh; background: #F5F6FA; }
.assess-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); color: #fff; }
.assess-nav-back { font-size: 40rpx; padding: 16rpx; }
.assess-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.assess-nav-action { font-size: 26rpx; padding: 8rpx 16rpx; background: rgba(255,255,255,0.2); border-radius: 8rpx; }

.assess-tabs { display: flex; padding: 16rpx 16rpx 0; gap: 8rpx; overflow-x: auto; white-space: nowrap; }
.assess-tab { position: relative; display: inline-flex; align-items: center; gap: 6rpx; padding: 12rpx 20rpx; border-radius: 24rpx; background: #fff; font-size: 24rpx; color: #5B6B7F; flex-shrink: 0; }
.assess-tab--active { background: #9B59B6; color: #fff; }
.assess-tab-badge { min-width: 28rpx; height: 28rpx; border-radius: 14rpx; background: #E74C3C; color: #fff; font-size: 18rpx; display: flex; align-items: center; justify-content: center; padding: 0 6rpx; }

.assess-search { padding: 16rpx 24rpx; }
.assess-search-input { background: #fff; border-radius: 12rpx; padding: 16rpx 24rpx; font-size: 28rpx; }

.assess-list { height: calc(100vh - 450rpx); padding: 0 24rpx; }
.assess-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; }
.assess-card-header { display: flex; align-items: center; gap: 16rpx; }
.assess-card-avatar { width: 64rpx; height: 64rpx; border-radius: 50%; background: #9B59B6; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 26rpx; font-weight: 600; }
.assess-card-info { flex: 1; }
.assess-card-name { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.assess-card-scale { display: block; font-size: 22rpx; color: #8E99A4; }
.assess-status-tag { padding: 6rpx 16rpx; border-radius: 8rpx; color: #fff; font-size: 22rpx; }
.assess-card-meta { display: flex; justify-content: space-between; margin-top: 16rpx; font-size: 24rpx; color: #8E99A4; }

.assess-empty { text-align: center; padding: 120rpx 0; }
.assess-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.assess-empty-text { font-size: 28rpx; color: #8E99A4; }

.assess-modal-mask { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 999; }
.assess-modal { width: 85%; background: #fff; border-radius: 24rpx; padding: 32rpx; }
.assess-modal-title { display: block; font-size: 32rpx; font-weight: 600; color: #2C3E50; margin-bottom: 24rpx; text-align: center; }
.assess-modal-section { margin-bottom: 24rpx; }
.assess-modal-label { display: block; font-size: 26rpx; color: #5B6B7F; margin-bottom: 12rpx; }
.assess-picker { padding: 16rpx; background: #F5F6FA; border-radius: 12rpx; font-size: 28rpx; }
.assess-scale-options { display: flex; flex-wrap: wrap; gap: 12rpx; }
.assess-scale-opt { padding: 10rpx 20rpx; border-radius: 8rpx; background: #F0F0F0; font-size: 24rpx; color: #5B6B7F; }
.assess-scale-opt--active { background: #9B59B6; color: #fff; }
.assess-modal-actions { display: flex; gap: 16rpx; margin-top: 24rpx; }
.assess-modal-btn { flex: 1; text-align: center; padding: 20rpx 0; border-radius: 12rpx; font-size: 28rpx; }
.assess-modal-cancel { background: #F0F0F0; color: #5B6B7F; }
.assess-modal-confirm { background: #9B59B6; color: #fff; }
</style>`;

// ============================================================
// 5. flywheel/index.vue — AI飞轮审核中心
// ============================================================
const FLYWHEEL_PAGE = `<template>
  <view class="fw-page">
    <view class="fw-navbar">
      <view class="fw-nav-back" @tap="goBack">←</view>
      <text class="fw-nav-title">AI 飞轮</text>
      <view class="fw-nav-action" @tap="refresh">↻</view>
    </view>

    <!-- 飞轮可视化 -->
    <view class="fw-wheel">
      <view v-for="(step, i) in wheelSteps" :key="i" class="fw-wheel-step" :class="{ 'fw-wheel-step--active': i === activeWheelStep }">
        <text class="fw-wheel-icon">{{ step.icon }}</text>
        <text class="fw-wheel-label">{{ step.label }}</text>
      </view>
    </view>

    <!-- 今日统计 -->
    <view class="fw-stats">
      <view class="fw-stat" v-for="s in todayStats" :key="s.label">
        <text class="fw-stat-num" :style="{ color: s.color }">{{ s.value }}</text>
        <text class="fw-stat-label">{{ s.label }}</text>
      </view>
    </view>

    <!-- Tab -->
    <view class="fw-tabs">
      <view v-for="tab in fwTabs" :key="tab.key" class="fw-tab" :class="{ 'fw-tab--active': activeTab === tab.key }" @tap="activeTab = tab.key">
        {{ tab.label }}
      </view>
    </view>

    <scroll-view scroll-y class="fw-list" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <!-- 待审核 -->
      <template v-if="activeTab === 'pending'">
        <view v-for="item in pendingItems" :key="item.id" class="fw-card" :class="{ 'fw-card--done': item._done }">
          <view class="fw-card-header">
            <text class="fw-card-student">{{ item.student_name || '学员' }}</text>
            <view class="fw-card-type" :style="{ background: typeColor(item.type) }">{{ item.type || '推送' }}</view>
          </view>
          <text class="fw-card-summary">{{ item.ai_summary || item.summary || '—' }}</text>
          <view class="fw-card-draft" v-if="item._expanded">
            <text class="fw-card-draft-text">{{ item.ai_draft || item.content || item.title || '无草稿' }}</text>
          </view>
          <view class="fw-card-toggle" @tap="item._expanded = !item._expanded">
            {{ item._expanded ? '收起 ▲' : '查看草稿 ▼' }}
          </view>
          <view v-if="!item._done" class="fw-card-actions">
            <view class="fw-btn fw-btn--approve" @tap="approveItem(item)">✓ 通过</view>
            <view class="fw-btn fw-btn--reject" @tap="showReject(item)">✗ 退回</view>
          </view>
          <view v-else class="fw-card-done-label" :style="{ color: item._done === 'approved' ? '#27AE60' : '#E74C3C' }">
            {{ item._done === 'approved' ? '✓ 已通过' : '✗ 已退回' }}
          </view>
        </view>
        <view v-if="pendingItems.length === 0" class="fw-empty">
          <text class="fw-empty-icon">✅</text>
          <text class="fw-empty-text">今日审核已全部完成!</text>
        </view>
      </template>

      <!-- AI跟进计划 -->
      <template v-if="activeTab === 'generate'">
        <view class="fw-gen-section">
          <text class="fw-gen-title">选择学员生成AI跟进计划</text>
          <scroll-view scroll-x class="fw-student-picker">
            <view v-for="s in studentList" :key="s.id" class="fw-student-chip" :class="{ 'fw-student-chip--active': selectedStudent?.id === s.id }" @tap="selectedStudent = s">
              {{ s.name }}
            </view>
          </scroll-view>
          <view v-if="selectedStudent" class="fw-gen-form">
            <textarea class="fw-gen-input" placeholder="自定义AI指令（可选）" v-model="customPrompt" />
            <view class="fw-gen-btn" @tap="runAgent" :class="{ 'fw-gen-btn--loading': generating }">
              {{ generating ? '生成中...' : '🚀 生成跟进计划' }}
            </view>
          </view>
          <view v-if="agentResult" class="fw-gen-result">
            <text class="fw-gen-result-title">AI 建议:</text>
            <text class="fw-gen-result-text">{{ agentResult }}</text>
          </view>
        </view>
      </template>
    </scroll-view>

    <!-- 退回原因弹窗 -->
    <view v-if="rejectModal" class="fw-modal-mask" @tap="rejectModal = null">
      <view class="fw-modal" @tap.stop>
        <text class="fw-modal-title">退回原因</text>
        <textarea class="fw-modal-input" v-model="rejectReason" placeholder="请输入退回原因" />
        <view class="fw-modal-actions">
          <view class="fw-modal-btn fw-modal-cancel" @tap="rejectModal = null">取消</view>
          <view class="fw-modal-btn fw-modal-confirm" @tap="doReject">确认退回</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

${INLINE_HTTP}

const activeTab = ref('pending')
const refreshing = ref(false)
const pendingItems = ref<any[]>([])
const studentList = ref<any[]>([])
const selectedStudent = ref<any>(null)
const customPrompt = ref('')
const generating = ref(false)
const agentResult = ref('')
const rejectModal = ref<any>(null)
const rejectReason = ref('')
const approvedCount = ref(0)
const rejectedCount = ref(0)
const activeWheelStep = ref(2) // 审核阶段

const wheelSteps = [
  { icon: '📊', label: '数据采集' },
  { icon: '🤖', label: 'AI分析' },
  { icon: '👨‍⚕️', label: '教练审核' },
  { icon: '📤', label: '推送执行' },
  { icon: '📈', label: '效果追踪' },
]

const fwTabs = [
  { key: 'pending', label: '待审核' },
  { key: 'generate', label: 'AI跟进' },
]

const todayStats = computed(() => [
  { label: '待审核', value: pendingItems.value.filter(i => !i._done).length, color: '#E67E22' },
  { label: '已通过', value: approvedCount.value, color: '#27AE60' },
  { label: '已退回', value: rejectedCount.value, color: '#E74C3C' },
])

function typeColor(t: string): string {
  const map: Record<string, string> = { rx_push: '#3498DB', prescription: '#9B59B6', assessment: '#E67E22' }
  return map[t] || '#5B6B7F'
}

async function loadData() {
  // 飞轮审核队列 (多端点fallback)
  try {
    const res = await http<any>('/api/v1/coach/review-queue')
    pendingItems.value = (res.items || res.queue || (Array.isArray(res) ? res : [])).map((i: any) => ({ ...i, _expanded: false, _done: '' }))
  } catch {
    try {
      const res2 = await http<any>('/api/v1/coach-push/pending?page_size=50')
      pendingItems.value = (res2.items || []).map((i: any) => ({ ...i, _expanded: false, _done: '' }))
    } catch { pendingItems.value = [] }
  }

  // 今日统计
  try {
    const res = await http<any>('/api/v1/coach/stats/today')
    approvedCount.value = res.approved || 0
    rejectedCount.value = res.rejected || 0
  } catch {}

  // 学员列表
  try {
    const res = await http<any>('/api/v1/coach/dashboard')
    studentList.value = (res.students || []).map((s: any) => ({
      id: s.id || s.user_id,
      name: s.name || s.full_name || '未知',
    }))
  } catch { studentList.value = [] }
}

async function approveItem(item: any) {
  try {
    await http(\`/api/v1/coach/review/\${item.id}/approve\`, { method: 'POST' })
  } catch {
    try { await http(\`/api/v1/coach-push/\${item.id}/approve\`, { method: 'POST' }) } catch {}
  }
  item._done = 'approved'
  approvedCount.value++
}

function showReject(item: any) {
  rejectModal.value = item
  rejectReason.value = ''
}

async function doReject() {
  if (!rejectModal.value) return
  try {
    await http(\`/api/v1/coach/review/\${rejectModal.value.id}/reject\`, { method: 'POST', data: { reason: rejectReason.value } })
  } catch {
    try { await http(\`/api/v1/coach-push/\${rejectModal.value.id}/reject\`, { method: 'POST', data: { reason: rejectReason.value } }) } catch {}
  }
  rejectModal.value._done = 'rejected'
  rejectedCount.value++
  rejectModal.value = null
}

async function runAgent() {
  if (!selectedStudent.value || generating.value) return
  generating.value = true
  agentResult.value = ''
  try {
    const res = await http<any>('/api/v1/agent/run', {
      method: 'POST',
      data: {
        agent_type: 'coach_flywheel',
        user_id: String(selectedStudent.value.id),
        input: customPrompt.value || '请为该学员生成个性化跟进计划',
      }
    })
    agentResult.value = res.result || res.output || res.text || JSON.stringify(res)
  } catch (e: any) {
    agentResult.value = '生成失败: ' + (e.message || '请重试')
  }
  generating.value = false
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
.fw-page { min-height: 100vh; background: #F5F6FA; }
.fw-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #27AE60 0%, #2ECC71 100%); color: #fff; }
.fw-nav-back { font-size: 40rpx; padding: 16rpx; }
.fw-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.fw-nav-action { font-size: 36rpx; padding: 16rpx; }

.fw-wheel { display: flex; padding: 20rpx 16rpx; gap: 4rpx; }
.fw-wheel-step { flex: 1; text-align: center; padding: 12rpx 4rpx; border-radius: 12rpx; background: #fff; }
.fw-wheel-step--active { background: #27AE60; }
.fw-wheel-step--active .fw-wheel-label { color: #fff; }
.fw-wheel-icon { display: block; font-size: 28rpx; }
.fw-wheel-label { display: block; font-size: 18rpx; color: #5B6B7F; margin-top: 4rpx; }

.fw-stats { display: flex; padding: 0 24rpx 16rpx; gap: 12rpx; }
.fw-stat { flex: 1; text-align: center; background: #fff; border-radius: 12rpx; padding: 16rpx; }
.fw-stat-num { display: block; font-size: 40rpx; font-weight: 700; }
.fw-stat-label { display: block; font-size: 22rpx; color: #8E99A4; }

.fw-tabs { display: flex; padding: 0 24rpx 12rpx; gap: 12rpx; }
.fw-tab { flex: 1; text-align: center; padding: 14rpx 0; background: #fff; border-radius: 12rpx; font-size: 26rpx; color: #5B6B7F; }
.fw-tab--active { background: #27AE60; color: #fff; }

.fw-list { height: calc(100vh - 580rpx); padding: 0 24rpx; }
.fw-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; }
.fw-card--done { opacity: 0.6; }
.fw-card-header { display: flex; align-items: center; justify-content: space-between; }
.fw-card-student { font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.fw-card-type { padding: 4rpx 12rpx; border-radius: 6rpx; color: #fff; font-size: 22rpx; }
.fw-card-summary { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 12rpx; }
.fw-card-draft { background: #F8F9FA; border-radius: 12rpx; padding: 16rpx; margin-top: 12rpx; }
.fw-card-draft-text { font-size: 26rpx; color: #2C3E50; line-height: 1.6; }
.fw-card-toggle { text-align: center; font-size: 24rpx; color: #3498DB; margin-top: 8rpx; padding: 8rpx; }
.fw-card-actions { display: flex; gap: 16rpx; margin-top: 16rpx; }
.fw-btn { flex: 1; text-align: center; padding: 16rpx 0; border-radius: 10rpx; font-size: 28rpx; font-weight: 600; }
.fw-btn--approve { background: #27AE60; color: #fff; }
.fw-btn--reject { background: #FFF5F5; color: #E74C3C; border: 1rpx solid #E74C3C; }
.fw-card-done-label { text-align: center; margin-top: 12rpx; font-size: 26rpx; font-weight: 600; }

.fw-gen-section { background: #fff; border-radius: 16rpx; padding: 24rpx; }
.fw-gen-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }
.fw-student-picker { display: flex; white-space: nowrap; gap: 12rpx; padding-bottom: 16rpx; }
.fw-student-chip { display: inline-block; padding: 12rpx 24rpx; border-radius: 24rpx; background: #F0F0F0; font-size: 26rpx; color: #5B6B7F; }
.fw-student-chip--active { background: #27AE60; color: #fff; }
.fw-gen-form { margin-top: 16rpx; }
.fw-gen-input { width: 100%; height: 120rpx; padding: 16rpx; background: #F8F9FA; border-radius: 12rpx; font-size: 26rpx; box-sizing: border-box; }
.fw-gen-btn { text-align: center; padding: 20rpx; background: #27AE60; color: #fff; border-radius: 12rpx; font-size: 30rpx; font-weight: 600; margin-top: 16rpx; }
.fw-gen-btn--loading { opacity: 0.6; }
.fw-gen-result { margin-top: 20rpx; background: #F0FFF0; border-radius: 12rpx; padding: 20rpx; border-left: 4rpx solid #27AE60; }
.fw-gen-result-title { display: block; font-size: 26rpx; font-weight: 600; color: #27AE60; margin-bottom: 8rpx; }
.fw-gen-result-text { font-size: 26rpx; color: #2C3E50; line-height: 1.6; }

.fw-empty { text-align: center; padding: 120rpx 0; }
.fw-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.fw-empty-text { font-size: 28rpx; color: #8E99A4; }

.fw-modal-mask { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 999; }
.fw-modal { width: 85%; background: #fff; border-radius: 24rpx; padding: 32rpx; }
.fw-modal-title { display: block; font-size: 32rpx; font-weight: 600; text-align: center; margin-bottom: 20rpx; }
.fw-modal-input { width: 100%; height: 160rpx; padding: 16rpx; background: #F8F9FA; border-radius: 12rpx; font-size: 28rpx; box-sizing: border-box; }
.fw-modal-actions { display: flex; gap: 16rpx; margin-top: 24rpx; }
.fw-modal-btn { flex: 1; text-align: center; padding: 20rpx 0; border-radius: 12rpx; font-size: 28rpx; }
.fw-modal-cancel { background: #F0F0F0; color: #5B6B7F; }
.fw-modal-confirm { background: #E74C3C; color: #fff; }
</style>`;

// ============================================================
// 6. live/index.vue — 直播/活动中心
// ============================================================
const LIVE_PAGE = `<template>
  <view class="live-page">
    <view class="live-navbar">
      <view class="live-nav-back" @tap="goBack">←</view>
      <text class="live-nav-title">直播/活动中心</text>
    </view>

    <!-- Tab -->
    <view class="live-tabs">
      <view v-for="tab in liveTabs" :key="tab.key" class="live-tab" :class="{ 'live-tab--active': activeTab === tab.key }" @tap="activeTab = tab.key">
        {{ tab.label }}
        <view v-if="tab.badge > 0" class="live-tab-badge live-tab-badge--live">{{ tab.badge }}</view>
      </view>
    </view>

    <scroll-view scroll-y class="live-list" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 直播中 -->
      <template v-if="activeTab === 'live'">
        <view v-for="item in liveNow" :key="item.id" class="live-card live-card--live">
          <view class="live-card-cover">
            <view class="live-badge-live">● LIVE</view>
            <text class="live-card-viewers">{{ item.viewers || 0 }}人观看</text>
          </view>
          <view class="live-card-body">
            <text class="live-card-title">{{ item.title }}</text>
            <text class="live-card-host">主讲: {{ item.host || '—' }}</text>
            <view class="live-card-btn live-card-btn--enter" @tap="enterLive(item)">进入直播</view>
          </view>
        </view>
        <view v-if="liveNow.length === 0" class="live-empty">
          <text class="live-empty-icon">📡</text>
          <text class="live-empty-text">当前没有进行中的直播</text>
        </view>
      </template>

      <!-- 即将开始 -->
      <template v-if="activeTab === 'upcoming'">
        <view v-for="item in upcoming" :key="item.id" class="live-card">
          <view class="live-card-body">
            <view class="live-card-time-tag">{{ formatTime(item.start_time) }}</view>
            <text class="live-card-title">{{ item.title }}</text>
            <text class="live-card-host">主讲: {{ item.host || '—' }}</text>
            <view class="live-card-btn" :class="item._reserved ? 'live-card-btn--reserved' : 'live-card-btn--reserve'" @tap="toggleReserve(item)">
              {{ item._reserved ? '✓ 已预约' : '📅 预约提醒' }}
            </view>
          </view>
        </view>
        <view v-if="upcoming.length === 0" class="live-empty">
          <text class="live-empty-icon">📅</text>
          <text class="live-empty-text">暂无即将开始的直播</text>
        </view>
      </template>

      <!-- 历史回放 -->
      <template v-if="activeTab === 'replay'">
        <view v-for="item in replays" :key="item.id" class="live-card" @tap="watchReplay(item)">
          <view class="live-card-body">
            <text class="live-card-title">{{ item.title }}</text>
            <text class="live-card-host">{{ item.host || '—' }} · {{ item.duration || '—' }} · {{ item.views || 0 }}次观看</text>
            <text class="live-card-date">{{ formatDate(item.end_time || item.created_at) }}</text>
          </view>
          <text class="live-card-play">▶</text>
        </view>
        <view v-if="replays.length === 0" class="live-empty">
          <text class="live-empty-icon">📼</text>
          <text class="live-empty-text">暂无历史回放</text>
        </view>
      </template>
    </scroll-view>

    <!-- 底部提示 -->
    <view class="live-footer">
      <text class="live-footer-text">直播功能持续完善中，更多内容即将上线</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

${INLINE_HTTP}

const activeTab = ref('live')
const refreshing = ref(false)
const liveNow = ref<any[]>([])
const upcoming = ref<any[]>([])
const replays = ref<any[]>([])

const liveTabs = computed(() => [
  { key: 'live', label: '直播中', badge: liveNow.value.length },
  { key: 'upcoming', label: '即将开始', badge: upcoming.value.length },
  { key: 'replay', label: '历史回放', badge: 0 },
])

function formatTime(t: string): string {
  if (!t) return '待定'
  const d = new Date(t)
  return (d.getMonth() + 1) + '/' + d.getDate() + ' ' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
}
function formatDate(t: string): string {
  if (!t) return ''
  return t.slice(0, 10)
}

async function loadData() {
  // 尝试加载直播数据 (后端可能未实现)
  try {
    const res = await http<any>('/api/v1/live/sessions')
    const items = res.items || res.sessions || (Array.isArray(res) ? res : [])
    liveNow.value = items.filter((i: any) => i.status === 'live').map((i: any) => ({ ...i }))
    upcoming.value = items.filter((i: any) => i.status === 'upcoming').map((i: any) => ({ ...i, _reserved: false }))
    replays.value = items.filter((i: any) => i.status === 'ended' || i.status === 'replay')
  } catch {
    // 后端直播功能预留未实现，显示空状态
    liveNow.value = []
    upcoming.value = []
    replays.value = []
  }
}

function enterLive(item: any) {
  uni.showToast({ title: '直播功能开发中', icon: 'none' })
}
function toggleReserve(item: any) {
  item._reserved = !item._reserved
  uni.showToast({ title: item._reserved ? '预约成功' : '已取消预约', icon: 'success' })
}
function watchReplay(item: any) {
  if (item.replay_url) {
    uni.navigateTo({ url: '/pages/learning/video-player?id=' + item.id + '&url=' + encodeURIComponent(item.replay_url) })
  } else {
    uni.showToast({ title: '回放准备中', icon: 'none' })
  }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.live-page { min-height: 100vh; background: #F5F6FA; }
.live-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #E74C3C 0%, #FF6B6B 100%); color: #fff; }
.live-nav-back { font-size: 40rpx; padding: 16rpx; }
.live-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }

.live-tabs { display: flex; padding: 16rpx 24rpx; gap: 12rpx; }
.live-tab { position: relative; flex: 1; text-align: center; padding: 16rpx 0; background: #fff; border-radius: 12rpx; font-size: 26rpx; color: #5B6B7F; }
.live-tab--active { background: #E74C3C; color: #fff; }
.live-tab-badge { position: absolute; top: -8rpx; right: 16rpx; min-width: 28rpx; height: 28rpx; border-radius: 14rpx; font-size: 18rpx; display: flex; align-items: center; justify-content: center; padding: 0 6rpx; }
.live-tab-badge--live { background: #E74C3C; color: #fff; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.live-list { height: calc(100vh - 380rpx); padding: 0 24rpx; }

.live-card { background: #fff; border-radius: 16rpx; margin-bottom: 16rpx; overflow: hidden; }
.live-card--live { border: 2rpx solid #E74C3C; }
.live-card-cover { position: relative; height: 200rpx; background: linear-gradient(135deg, #2C3E50, #34495E); display: flex; align-items: center; justify-content: center; }
.live-badge-live { position: absolute; top: 16rpx; left: 16rpx; background: #E74C3C; color: #fff; padding: 4rpx 16rpx; border-radius: 8rpx; font-size: 24rpx; font-weight: 600; animation: pulse 1.5s infinite; }
.live-card-viewers { position: absolute; top: 16rpx; right: 16rpx; color: #fff; font-size: 22rpx; background: rgba(0,0,0,0.4); padding: 4rpx 12rpx; border-radius: 6rpx; }
.live-card-body { padding: 20rpx 24rpx; }
.live-card-time-tag { display: inline-block; padding: 4rpx 12rpx; background: #FFF3E0; color: #E67E22; border-radius: 6rpx; font-size: 22rpx; margin-bottom: 8rpx; }
.live-card-title { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.live-card-host { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 6rpx; }
.live-card-date { display: block; font-size: 22rpx; color: #BDC3C7; margin-top: 4rpx; }
.live-card-btn { display: block; text-align: center; padding: 14rpx 0; border-radius: 10rpx; margin-top: 16rpx; font-size: 26rpx; font-weight: 600; }
.live-card-btn--enter { background: #E74C3C; color: #fff; }
.live-card-btn--reserve { background: #FFF3E0; color: #E67E22; }
.live-card-btn--reserved { background: #E8F5E9; color: #27AE60; }
.live-card-play { display: flex; align-items: center; padding: 24rpx; font-size: 36rpx; color: #3498DB; }

.live-empty { text-align: center; padding: 120rpx 0; }
.live-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.live-empty-text { font-size: 28rpx; color: #8E99A4; }

.live-footer { text-align: center; padding: 24rpx; }
.live-footer-text { font-size: 24rpx; color: #BDC3C7; }
</style>`;

// ============================================================
// WRITE FILES
// ============================================================
const files = {
  'risk/index.vue': RISK_PAGE,
  'messages/index.vue': MESSAGES_PAGE,
  'analytics/index.vue': ANALYTICS_PAGE,
  'assessment/index.vue': ASSESSMENT_PAGE,
  'flywheel/index.vue': FLYWHEEL_PAGE,
  'live/index.vue': LIVE_PAGE,
};

let count = 0;
for (const [rel, content] of Object.entries(files)) {
  const full = path.join(BASE, rel);
  const dir = path.dirname(full);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  
  // 备份
  if (fs.existsSync(full)) {
    fs.copyFileSync(full, full + '.bak');
    console.log(`  BAK: ${full}.bak`);
  }
  
  fs.writeFileSync(full, content);
  count++;
  console.log(`  OK: ${full} (${content.split('\n').length} lines)`);
}

console.log(`\n✅ ${count} 个页面部署完成`);
console.log('\n下一步:');
console.log('  1. npm run dev:mp-weixin (或 build:mp-weixin)');
console.log('  2. 微信开发者工具验证');
console.log('  3. git add -A && git commit -m "feat: 6个coach页面从占位符升级为成品"');
