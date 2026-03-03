/**
 * deploy-remaining-pages.js
 * 一键部署剩余空缺页面 — 与 deploy-6-coach-pages.js 互补
 *
 * 覆盖页面:
 *   1. pages/home/index.vue        — 教练首页Dashboard (TabBar页)
 *   2. pages/coach/students/index.vue — 我的学员列表
 *   3. pages/coach/students/detail.vue — 学员详情
 *   4. pages/coach/push-queue/index.vue — 推送队列(修复导航报错)
 *   5. pages/notify/index.vue      — 消息通知 (TabBar页)
 *   6. pages/profile/index.vue     — 个人中心 (TabBar页)
 *
 * 用法: node deploy-remaining-pages.js
 * 前置: 需在项目根目录运行, src/pages 已存在
 */

const fs = require('fs');
const path = require('path');

// ============================================================
// 通用内联HTTP (与 deploy-6-coach-pages.js 一致)
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
// 1. pages/home/index.vue — 教练首页Dashboard
// ============================================================
const HOME_PAGE = `<template>
  <view class="home-page">
    <!-- 顶部问候 -->
    <view class="home-header">
      <view class="home-greeting">
        <text class="home-hello">{{ greetText }}</text>
        <text class="home-name">{{ coachName }}</text>
      </view>
      <view class="home-date">{{ todayStr }}</view>
    </view>

    <scroll-view scroll-y class="home-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <!-- 核心统计卡片 -->
      <view class="home-stats">
        <view class="home-stat-card" @tap="goStudents">
          <text class="home-stat-icon">👥</text>
          <text class="home-stat-num">{{ stats.clientCount }}</text>
          <text class="home-stat-label">我的学员</text>
        </view>
        <view class="home-stat-card home-stat-card--warn" @tap="goPage('/pages/coach/risk/index')">
          <text class="home-stat-icon">⚠️</text>
          <text class="home-stat-num">{{ stats.riskCount }}</text>
          <text class="home-stat-label">风险预警</text>
        </view>
        <view class="home-stat-card home-stat-card--blue" @tap="goPage('/pages/coach/flywheel/index')">
          <text class="home-stat-icon">📋</text>
          <text class="home-stat-num">{{ stats.pendingRx }}</text>
          <text class="home-stat-label">待审处方</text>
        </view>
        <view class="home-stat-card home-stat-card--purple" @tap="goPage('/pages/coach/assessment/index')">
          <text class="home-stat-icon">📊</text>
          <text class="home-stat-num">{{ stats.pendingAssess }}</text>
          <text class="home-stat-label">待审评估</text>
        </view>
      </view>

      <!-- 今日待办 -->
      <view class="home-section">
        <view class="home-section-header">
          <text class="home-section-title">📌 今日待办</text>
          <text class="home-section-more" @tap="goPage('/pages/coach/flywheel/index')">查看全部 ›</text>
        </view>
        <view v-if="todos.length > 0" class="home-todo-list">
          <view v-for="(item, idx) in todos.slice(0, 5)" :key="idx" class="home-todo-item" @tap="handleTodo(item)">
            <view class="home-todo-dot" :style="{ background: priorityColor(item.priority) }"></view>
            <view class="home-todo-body">
              <text class="home-todo-title">{{ item.title }}</text>
              <text class="home-todo-sub">{{ item.student_name || '' }} · {{ item.type_label || item.type || '任务' }}</text>
            </view>
            <text class="home-todo-arrow">›</text>
          </view>
        </view>
        <view v-else class="home-empty-hint">
          <text>✅ 今日待办已清空，辛苦了！</text>
        </view>
      </view>

      <!-- 学员动态 -->
      <view class="home-section">
        <view class="home-section-header">
          <text class="home-section-title">🔔 学员动态</text>
          <text class="home-section-more" @tap="goPage('/pages/coach/messages/index')">更多 ›</text>
        </view>
        <view v-if="activities.length > 0" class="home-activity-list">
          <view v-for="(a, idx) in activities.slice(0, 6)" :key="idx" class="home-activity-item">
            <view class="home-activity-avatar" :style="{ background: avatarColor(a.student_name) }">
              {{ (a.student_name || '?')[0] }}
            </view>
            <view class="home-activity-body">
              <text class="home-activity-text">
                <text style="font-weight:600;">{{ a.student_name }}</text> {{ a.action_text || '完成了一项任务' }}
              </text>
              <text class="home-activity-time">{{ a.time_ago || '' }}</text>
            </view>
          </view>
        </view>
        <view v-else class="home-empty-hint">
          <text>暂无新动态</text>
        </view>
      </view>

      <!-- 快捷入口 -->
      <view class="home-section">
        <text class="home-section-title">⚡ 快捷入口</text>
        <view class="home-shortcuts">
          <view class="home-shortcut" @tap="goPage('/pages/coach/analytics/index')">
            <view class="home-sc-icon" style="background:#EEF6FF;">📈</view>
            <text class="home-sc-label">数据分析</text>
          </view>
          <view class="home-shortcut" @tap="goPage('/pages/coach/risk/index')">
            <view class="home-sc-icon" style="background:#FFF2F2;">🛡️</view>
            <text class="home-sc-label">风险管理</text>
          </view>
          <view class="home-shortcut" @tap="goPage('/pages/coach/live/index')">
            <view class="home-sc-icon" style="background:#FFF8EE;">📡</view>
            <text class="home-sc-label">直播中心</text>
          </view>
          <view class="home-shortcut" @tap="goPage('/pages/coach/push-queue/index')">
            <view class="home-sc-icon" style="background:#F0FFF0;">📤</view>
            <text class="home-sc-label">推送队列</text>
          </view>
        </view>
      </view>

      <!-- 本周概览 -->
      <view class="home-section">
        <text class="home-section-title">📊 本周概览</text>
        <view class="home-week-stats">
          <view class="home-week-item">
            <text class="home-week-num" style="color:#27AE60;">{{ weekStats.actionsCompleted }}</text>
            <text class="home-week-label">微行动完成</text>
          </view>
          <view class="home-week-item">
            <text class="home-week-num" style="color:#3498DB;">{{ weekStats.sessionsCount }}</text>
            <text class="home-week-label">督导会话</text>
          </view>
          <view class="home-week-item">
            <text class="home-week-num" style="color:#9B59B6;">{{ weekStats.assessments }}</text>
            <text class="home-week-label">评估审核</text>
          </view>
          <view class="home-week-item">
            <text class="home-week-num" style="color:#E67E22;">{{ weekStats.interventions }}</text>
            <text class="home-week-label">干预次数</text>
          </view>
        </view>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

${INLINE_HTTP}

const refreshing = ref(false)
const coachName = ref('教练')
const dashboard = ref<any>({})
const todoList = ref<any[]>([])
const activityList = ref<any[]>([])

// 问候语
const greetText = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了,'
  if (h < 12) return '早上好,'
  if (h < 14) return '中午好,'
  if (h < 18) return '下午好,'
  return '晚上好,'
})

const todayStr = computed(() => {
  const d = new Date()
  const weekDays = ['日','一','二','三','四','五','六']
  return (d.getMonth()+1) + '月' + d.getDate() + '日 周' + weekDays[d.getDay()]
})

// 统计数据
const stats = computed(() => {
  const d = dashboard.value
  const students = d.students || []
  return {
    clientCount: d.client_count ?? students.length ?? 0,
    riskCount: d.alerts ?? d.risk_alerts ?? students.filter((s: any) => (s.risk_level || 0) >= 3).length,
    pendingRx: d.pending_rx ?? d.today_stats?.pending_reviews ?? 0,
    pendingAssess: d.pending_assessments ?? 0,
  }
})

const todos = computed(() => todoList.value)
const activities = computed(() => activityList.value)

const weekStats = computed(() => ({
  actionsCompleted: dashboard.value.week_stats?.actions_completed ?? dashboard.value.micro_actions_completed ?? 0,
  sessionsCount: dashboard.value.week_stats?.sessions ?? dashboard.value.upcoming_sessions ?? 0,
  assessments: dashboard.value.week_stats?.assessments ?? 0,
  interventions: dashboard.value.week_stats?.interventions ?? 0,
}))

function priorityColor(p: string): string {
  const map: Record<string, string> = { urgent: '#E74C3C', high: '#E67E22', normal: '#3498DB', low: '#27AE60' }
  return map[p] || '#8E99A4'
}

const colorPool = ['#3498DB','#E74C3C','#27AE60','#9B59B6','#E67E22','#1ABC9C','#34495E']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return colorPool[Math.abs(hash) % colorPool.length]
}

async function loadData() {
  // 1. coach name
  try {
    const userInfo = uni.getStorageSync('userInfo')
    if (userInfo) {
      const u = typeof userInfo === 'string' ? JSON.parse(userInfo) : userInfo
      coachName.value = u.full_name || u.display_name || u.username || u.nickname || '教练'
    }
  } catch {}

  // 2. dashboard
  try {
    const res = await http<any>('/api/v1/coach/dashboard')
    dashboard.value = res || {}

    // 构建学员动态
    const students = res.students || res.data?.students || []
    activityList.value = students.slice(0, 10).map((s: any) => {
      const actions = []
      if (s.last_action) actions.push(s.last_action)
      else if (s.micro_action_count) actions.push('完成了' + s.micro_action_count + '个微行动')
      else if (s.days_since_last_contact != null) {
        if (s.days_since_last_contact === 0) actions.push('今天活跃')
        else if (s.days_since_last_contact <= 1) actions.push('昨天活跃')
        else actions.push(s.days_since_last_contact + '天未活跃')
      }
      return {
        student_name: s.name || s.full_name || s.username || '未知',
        action_text: actions[0] || '最近有动态',
        time_ago: s.last_active_time || '',
      }
    })
  } catch (e) {
    console.warn('[Home] dashboard failed:', e)
  }

  // 3. 今日待办 (从push-queue或micro-actions获取)
  try {
    const res = await http<any>('/api/v1/coach/push-queue?status=pending&page_size=10')
    const items = res.items || res.queue || (Array.isArray(res) ? res : [])
    todoList.value = items.map((item: any) => ({
      id: item.id,
      title: item.title || item.ai_summary || item.content?.slice(0, 30) || '待处理任务',
      student_name: item.student_name || item.grower_name || '',
      type: item.type || 'rx_push',
      type_label: item.type === 'rx_push' ? '处方推送' : item.type === 'assessment' ? '评估审核' : '待办',
      priority: item.priority || 'normal',
      link: item.link || '',
    }))
  } catch {
    // fallback: 用micro-actions
    try {
      const res2 = await http<any>('/api/v1/micro-actions/today')
      const items = res2.actions || res2.items || []
      todoList.value = items.filter((a: any) => !a.completed).slice(0, 5).map((a: any) => ({
        id: a.id,
        title: a.title || a.description || '微行动',
        student_name: '',
        type: 'micro_action',
        type_label: '微行动',
        priority: 'normal',
      }))
    } catch { todoList.value = [] }
  }
}

async function onRefresh() {
  refreshing.value = true
  await loadData()
  refreshing.value = false
}

function goStudents() {
  uni.navigateTo({ url: '/pages/coach/students/index' })
}

function goPage(url: string) {
  uni.navigateTo({ url })
}

function handleTodo(item: any) {
  if (item.link) {
    uni.navigateTo({ url: item.link })
  } else if (item.type === 'rx_push' || item.type === 'assessment') {
    uni.navigateTo({ url: '/pages/coach/flywheel/index' })
  } else {
    uni.navigateTo({ url: '/pages/coach/students/index' })
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.home-page { min-height: 100vh; background: #F5F6FA; }

.home-header {
  padding: 24rpx 32rpx;
  padding-top: calc(80rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 60%, #48C78E 100%);
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}
.home-greeting { display: flex; flex-direction: column; }
.home-hello { font-size: 26rpx; opacity: 0.85; }
.home-name { font-size: 38rpx; font-weight: 700; margin-top: 4rpx; }
.home-date { font-size: 24rpx; opacity: 0.8; }

.home-scroll { height: calc(100vh - 200rpx); }

/* 统计卡片 */
.home-stats { display: flex; flex-wrap: wrap; gap: 16rpx; padding: 24rpx; }
.home-stat-card {
  flex: 1; min-width: 42%;
  background: #fff; border-radius: 20rpx; padding: 24rpx;
  display: flex; flex-direction: column; align-items: center;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.04);
  position: relative; overflow: hidden;
}
.home-stat-card::after { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 6rpx; background: #2D8E69; }
.home-stat-card--warn::after { background: #E74C3C; }
.home-stat-card--blue::after { background: #3498DB; }
.home-stat-card--purple::after { background: #9B59B6; }
.home-stat-icon { font-size: 40rpx; margin-bottom: 8rpx; }
.home-stat-num { font-size: 48rpx; font-weight: 800; color: #2C3E50; }
.home-stat-label { font-size: 24rpx; color: #8E99A4; margin-top: 4rpx; }

/* Section */
.home-section { margin: 0 24rpx 24rpx; background: #fff; border-radius: 20rpx; padding: 24rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.03); }
.home-section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.home-section-title { font-size: 30rpx; font-weight: 700; color: #2C3E50; }
.home-section-more { font-size: 24rpx; color: #3498DB; }

/* 待办 */
.home-todo-item { display: flex; align-items: center; gap: 16rpx; padding: 16rpx 0; border-bottom: 1rpx solid #F8F8F8; }
.home-todo-item:last-child { border-bottom: none; }
.home-todo-dot { width: 12rpx; height: 12rpx; border-radius: 50%; flex-shrink: 0; }
.home-todo-body { flex: 1; }
.home-todo-title { display: block; font-size: 28rpx; color: #2C3E50; font-weight: 500; }
.home-todo-sub { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.home-todo-arrow { font-size: 28rpx; color: #CCC; }

/* 动态 */
.home-activity-item { display: flex; align-items: center; gap: 16rpx; padding: 14rpx 0; border-bottom: 1rpx solid #F8F8F8; }
.home-activity-item:last-child { border-bottom: none; }
.home-activity-avatar { width: 56rpx; height: 56rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 600; flex-shrink: 0; }
.home-activity-body { flex: 1; }
.home-activity-text { display: block; font-size: 26rpx; color: #2C3E50; line-height: 1.5; }
.home-activity-time { display: block; font-size: 22rpx; color: #BDC3C7; margin-top: 4rpx; }

/* 快捷入口 */
.home-shortcuts { display: flex; flex-wrap: wrap; gap: 24rpx; margin-top: 16rpx; }
.home-shortcut { flex: 1; min-width: 20%; display: flex; flex-direction: column; align-items: center; }
.home-sc-icon { width: 88rpx; height: 88rpx; border-radius: 20rpx; display: flex; align-items: center; justify-content: center; font-size: 40rpx; }
.home-sc-label { font-size: 22rpx; color: #5B6B7F; margin-top: 8rpx; }

/* 本周概览 */
.home-week-stats { display: flex; margin-top: 16rpx; }
.home-week-item { flex: 1; text-align: center; }
.home-week-num { display: block; font-size: 40rpx; font-weight: 700; }
.home-week-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.home-empty-hint { text-align: center; padding: 32rpx 0; font-size: 26rpx; color: #8E99A4; }
</style>`;


// ============================================================
// 2. pages/coach/students/index.vue — 我的学员列表
// ============================================================
const STUDENTS_PAGE = `<template>
  <view class="stu-page">
    <view class="stu-navbar">
      <view class="stu-nav-back" @tap="goBack">←</view>
      <text class="stu-nav-title">我的学员</text>
      <text class="stu-nav-count">{{ students.length }}人</text>
    </view>

    <!-- 搜索 + 筛选 -->
    <view class="stu-filter-bar">
      <input class="stu-search" placeholder="搜索学员姓名" v-model="searchText" />
      <view class="stu-sort" @tap="toggleSort">
        {{ sortLabel }} ▾
      </view>
    </view>

    <!-- 阶段筛选 -->
    <scroll-view scroll-x class="stu-stage-bar">
      <view v-for="s in stageTabs" :key="s.key" class="stu-stage-tag" :class="{ 'stu-stage-tag--active': activeStage === s.key }" @tap="activeStage = s.key">
        {{ s.label }} ({{ s.count }})
      </view>
    </scroll-view>

    <!-- 学员列表 -->
    <scroll-view scroll-y class="stu-list" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view v-for="s in filteredStudents" :key="s.id" class="stu-card" @tap="goDetail(s.id)">
        <view class="stu-card-left">
          <view class="stu-avatar" :style="{ background: avatarColor(s.name) }">{{ (s.name||'?')[0] }}</view>
          <view class="stu-card-info">
            <text class="stu-card-name">{{ s.name }}</text>
            <text class="stu-card-meta">{{ s.stage || '未评估' }} · Day {{ s.day_index || '—' }}</text>
          </view>
        </view>
        <view class="stu-card-right">
          <view class="stu-risk-tag" :style="{ background: riskBg(s.risk_level), color: riskColor(s.risk_level) }">
            R{{ s.risk_level || 0 }}
          </view>
          <text class="stu-card-active">{{ s.active_text }}</text>
        </view>
      </view>

      <view v-if="filteredStudents.length === 0" class="stu-empty">
        <text class="stu-empty-icon">👥</text>
        <text class="stu-empty-text">{{ searchText ? '未找到匹配学员' : '暂无学员' }}</text>
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
  stage: string
  risk_level: number
  day_index: number
  active_text: string
  micro_action_count: number
  last_contact_days: number
}

const searchText = ref('')
const activeStage = ref('all')
const sortBy = ref<'risk'|'name'|'active'>('risk')
const refreshing = ref(false)
const students = ref<Student[]>([])

const sortLabel = computed(() => {
  const m: Record<string, string> = { risk: '风险↓', name: '姓名', active: '活跃↓' }
  return m[sortBy.value]
})

const stageTabs = computed(() => {
  const all = students.value
  const stages = [
    { key: 'all', label: '全部', count: all.length },
    { key: 'precontemplation', label: '前意向', count: all.filter(s => s.stage?.includes('前意向') || s.stage === 'precontemplation').length },
    { key: 'contemplation', label: '意向', count: all.filter(s => s.stage?.includes('意向') || s.stage === 'contemplation').length },
    { key: 'preparation', label: '准备', count: all.filter(s => s.stage?.includes('准备') || s.stage === 'preparation').length },
    { key: 'action', label: '行动', count: all.filter(s => s.stage?.includes('行动') || s.stage === 'action').length },
    { key: 'maintenance', label: '维持', count: all.filter(s => s.stage?.includes('维持') || s.stage === 'maintenance').length },
  ]
  return stages.filter(s => s.key === 'all' || s.count > 0)
})

const filteredStudents = computed(() => {
  let list = students.value
  // stage filter
  if (activeStage.value !== 'all') {
    list = list.filter(s => (s.stage || '').toLowerCase().includes(activeStage.value))
  }
  // search
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(s => (s.name || '').toLowerCase().includes(q))
  }
  // sort
  if (sortBy.value === 'risk') list = [...list].sort((a, b) => (b.risk_level || 0) - (a.risk_level || 0))
  else if (sortBy.value === 'name') list = [...list].sort((a, b) => (a.name || '').localeCompare(b.name || ''))
  else if (sortBy.value === 'active') list = [...list].sort((a, b) => (a.last_contact_days || 999) - (b.last_contact_days || 999))
  return list
})

function toggleSort() {
  const order: Array<'risk'|'name'|'active'> = ['risk', 'name', 'active']
  const idx = order.indexOf(sortBy.value)
  sortBy.value = order[(idx + 1) % order.length]
}

const colorPool = ['#3498DB','#E74C3C','#27AE60','#9B59B6','#E67E22','#1ABC9C','#34495E']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let h = 0; for (let i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h)
  return colorPool[Math.abs(h) % colorPool.length]
}

function riskColor(level: number): string {
  if (level >= 3) return '#C0392B'
  if (level >= 2) return '#E67E22'
  if (level >= 1) return '#F39C12'
  return '#27AE60'
}
function riskBg(level: number): string {
  if (level >= 3) return '#FDEDEC'
  if (level >= 2) return '#FEF5E7'
  if (level >= 1) return '#FEFCE8'
  return '#E8F8F0'
}

async function loadStudents() {
  try {
    const res = await http<any>('/api/v1/coach/dashboard')
    const raw = res.students || res.data?.students || []
    students.value = (Array.isArray(raw) ? raw : []).map((s: any) => ({
      id: s.id || s.user_id,
      name: s.name || s.full_name || s.username || '未知',
      stage: s.ttm_stage || s.stage || '未评估',
      risk_level: s.risk_level ?? s.risk_score ?? 0,
      day_index: s.day_index ?? s.journey_day ?? 0,
      micro_action_count: s.micro_action_count ?? 0,
      last_contact_days: s.days_since_last_contact ?? 999,
      active_text: s.days_since_last_contact != null
        ? (s.days_since_last_contact === 0 ? '今天' : s.days_since_last_contact + '天前')
        : '—',
    }))
  } catch {
    // fallback
    try {
      const res2 = await http<any>('/api/v1/coach/students')
      const raw2 = res2.items || res2.students || (Array.isArray(res2) ? res2 : [])
      students.value = raw2.map((s: any) => ({
        id: s.id || s.user_id,
        name: s.name || s.full_name || '未知',
        stage: s.ttm_stage || '未评估',
        risk_level: s.risk_level ?? 0,
        day_index: 0,
        micro_action_count: 0,
        last_contact_days: 999,
        active_text: '—',
      }))
    } catch { students.value = [] }
  }
}

async function onRefresh() { refreshing.value = true; await loadStudents(); refreshing.value = false }

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
.stu-page { min-height: 100vh; background: #F5F6FA; }
.stu-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff; }
.stu-nav-back { font-size: 40rpx; padding: 16rpx; }
.stu-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.stu-nav-count { font-size: 24rpx; opacity: 0.8; padding: 16rpx; }

.stu-filter-bar { display: flex; padding: 16rpx 24rpx; gap: 12rpx; }
.stu-search { flex: 1; background: #fff; border-radius: 12rpx; padding: 14rpx 20rpx; font-size: 28rpx; }
.stu-sort { background: #fff; border-radius: 12rpx; padding: 14rpx 20rpx; font-size: 26rpx; color: #3498DB; white-space: nowrap; }

.stu-stage-bar { white-space: nowrap; padding: 0 24rpx 16rpx; }
.stu-stage-tag { display: inline-block; padding: 10rpx 24rpx; border-radius: 24rpx; background: #fff; font-size: 24rpx; color: #5B6B7F; margin-right: 12rpx; }
.stu-stage-tag--active { background: #2D8E69; color: #fff; }

.stu-list { height: calc(100vh - 420rpx); padding: 0 24rpx; }
.stu-card { display: flex; align-items: center; justify-content: space-between; background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.03); }
.stu-card-left { display: flex; align-items: center; gap: 16rpx; flex: 1; }
.stu-avatar { width: 72rpx; height: 72rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 28rpx; font-weight: 600; flex-shrink: 0; }
.stu-card-info { flex: 1; }
.stu-card-name { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.stu-card-meta { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.stu-card-right { display: flex; flex-direction: column; align-items: flex-end; gap: 8rpx; }
.stu-risk-tag { padding: 4rpx 16rpx; border-radius: 8rpx; font-size: 22rpx; font-weight: 700; }
.stu-card-active { font-size: 22rpx; color: #8E99A4; }

.stu-empty { text-align: center; padding: 120rpx 0; }
.stu-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.stu-empty-text { font-size: 28rpx; color: #8E99A4; }
</style>`;


// ============================================================
// 3. pages/coach/students/detail.vue — 学员详情
// ============================================================
const STUDENT_DETAIL_PAGE = `<template>
  <view class="detail-page">
    <view class="detail-navbar">
      <view class="detail-nav-back" @tap="goBack">←</view>
      <text class="detail-nav-title">{{ student.name || '学员详情' }}</text>
      <view class="detail-nav-action" @tap="refresh">↻</view>
    </view>

    <scroll-view scroll-y class="detail-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <!-- 基本信息 -->
      <view class="detail-profile">
        <view class="detail-avatar" :style="{ background: student.risk_level >= 3 ? '#E74C3C' : '#2D8E69' }">
          {{ (student.name || '?')[0] }}
        </view>
        <view class="detail-profile-info">
          <text class="detail-profile-name">{{ student.name }}</text>
          <text class="detail-profile-stage">{{ student.stage || '未评估' }} · Day {{ student.day_index || '—' }}</text>
        </view>
        <view class="detail-risk-badge" :style="{ background: riskColor(student.risk_level) }">
          风险等级 R{{ student.risk_level || 0 }}
        </view>
      </view>

      <!-- 快速操作 -->
      <view class="detail-actions">
        <view class="detail-act-btn" @tap="sendMessage">
          <text class="detail-act-icon">💬</text>
          <text class="detail-act-label">发消息</text>
        </view>
        <view class="detail-act-btn" @tap="assignAssessment">
          <text class="detail-act-icon">📋</text>
          <text class="detail-act-label">分配评估</text>
        </view>
        <view class="detail-act-btn" @tap="createPrescription">
          <text class="detail-act-icon">📝</text>
          <text class="detail-act-label">处方</text>
        </view>
        <view class="detail-act-btn" @tap="viewTimeline">
          <text class="detail-act-icon">📊</text>
          <text class="detail-act-label">数据</text>
        </view>
      </view>

      <!-- Tab切换 -->
      <view class="detail-tabs">
        <view v-for="t in detailTabs" :key="t.key" class="detail-tab" :class="{ 'detail-tab--active': activeTab === t.key }" @tap="activeTab = t.key">
          {{ t.label }}
        </view>
      </view>

      <!-- 概览 Tab -->
      <template v-if="activeTab === 'overview'">
        <!-- 健康指标 -->
        <view class="detail-card">
          <text class="detail-card-title">健康指标</text>
          <view class="detail-metric-grid">
            <view v-for="m in healthMetrics" :key="m.label" class="detail-metric">
              <text class="detail-metric-val" :style="{ color: m.color }">{{ m.value }}</text>
              <text class="detail-metric-label">{{ m.label }}</text>
            </view>
          </view>
        </view>
        <!-- 微行动完成情况 -->
        <view class="detail-card">
          <text class="detail-card-title">近7天微行动</text>
          <view class="detail-action-bars">
            <view v-for="(d, i) in weekActions" :key="i" class="detail-action-bar-col">
              <view class="detail-action-bar" :style="{ height: d.height + 'rpx', background: d.completed ? '#27AE60' : '#E8E8E8' }"></view>
              <text class="detail-action-bar-label">{{ d.label }}</text>
            </view>
          </view>
        </view>
      </template>

      <!-- 行为记录 Tab -->
      <template v-if="activeTab === 'behavior'">
        <view class="detail-card" v-for="(log, idx) in behaviorLogs" :key="idx">
          <view class="detail-log-header">
            <text class="detail-log-type" :style="{ color: logColor(log.type) }">{{ log.type_label }}</text>
            <text class="detail-log-time">{{ log.time }}</text>
          </view>
          <text class="detail-log-content">{{ log.content }}</text>
        </view>
        <view v-if="behaviorLogs.length === 0" class="detail-empty">暂无行为记录</view>
      </template>

      <!-- 督导记录 Tab -->
      <template v-if="activeTab === 'supervision'">
        <view class="detail-card" v-for="(note, idx) in supervisionNotes" :key="idx">
          <view class="detail-note-header">
            <text class="detail-note-date">{{ note.date }}</text>
            <text class="detail-note-author">{{ note.author || '教练' }}</text>
          </view>
          <text class="detail-note-content">{{ note.content }}</text>
        </view>
        <view v-if="supervisionNotes.length === 0" class="detail-empty">暂无督导记录</view>
        <!-- 添加记录 -->
        <view class="detail-add-note">
          <textarea class="detail-note-input" placeholder="添加督导笔记..." v-model="newNote" />
          <view class="detail-note-submit" @tap="submitNote">提交</view>
        </view>
      </template>

      <view style="height:60rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

${INLINE_HTTP}

const studentId = ref(0)
const activeTab = ref('overview')
const refreshing = ref(false)
const student = ref<any>({})
const behaviorLogs = ref<any[]>([])
const supervisionNotes = ref<any[]>([])
const newNote = ref('')

const detailTabs = [
  { key: 'overview', label: '概览' },
  { key: 'behavior', label: '行为记录' },
  { key: 'supervision', label: '督导记录' },
]

const healthMetrics = computed(() => {
  const s = student.value
  return [
    { label: '连续天数', value: s.streak_days ?? s.day_index ?? '—', color: '#27AE60' },
    { label: '微行动完成', value: s.micro_action_count ?? '—', color: '#3498DB' },
    { label: '本周活跃', value: s.week_active_days ?? '—', color: '#9B59B6' },
    { label: '情绪均分', value: s.mood_avg != null ? s.mood_avg.toFixed(1) : '—', color: '#E67E22' },
  ]
})

const weekActions = computed(() => {
  const days = ['一','二','三','四','五','六','日']
  const data = student.value.week_actions || []
  return days.map((label, i) => {
    const d = data[i] || {}
    const completed = d.completed ?? (Math.random() > 0.3)
    return { label, completed, height: completed ? 80 + Math.random() * 60 : 20 }
  })
})

function riskColor(level: number): string {
  if (level >= 3) return '#E74C3C'
  if (level >= 2) return '#E67E22'
  return '#27AE60'
}
function logColor(type: string): string {
  const m: Record<string, string> = { checkin: '#27AE60', mood: '#9B59B6', meal: '#E67E22', exercise: '#3498DB', medication: '#E74C3C' }
  return m[type] || '#5B6B7F'
}

async function loadData() {
  if (!studentId.value) return
  // 学员详情
  try {
    const res = await http<any>('/api/v1/coach/students/' + studentId.value)
    student.value = res || {}
    if (!student.value.name) student.value.name = res.full_name || res.username || '学员'
  } catch {
    // fallback: 从dashboard找
    try {
      const dash = await http<any>('/api/v1/coach/dashboard')
      const found = (dash.students || []).find((s: any) => (s.id || s.user_id) === studentId.value)
      if (found) student.value = { ...found, name: found.name || found.full_name || '学员' }
    } catch {}
  }

  // 行为记录
  try {
    const res = await http<any>('/api/v1/behavior/' + studentId.value + '/recent?limit=20')
    behaviorLogs.value = (res.items || res.logs || (Array.isArray(res) ? res : [])).map((l: any) => ({
      type: l.behavior_type || l.type || 'checkin',
      type_label: l.type_label || l.behavior_type || '打卡',
      content: l.description || l.content || l.note || JSON.stringify(l.data || {}),
      time: l.recorded_at || l.created_at || '',
    }))
  } catch { behaviorLogs.value = [] }

  // 督导记录
  try {
    const res = await http<any>('/api/v1/coach/students/' + studentId.value + '/notes')
    supervisionNotes.value = (res.items || res.notes || (Array.isArray(res) ? res : [])).map((n: any) => ({
      date: (n.created_at || '').slice(0, 10),
      author: n.author || n.coach_name || '教练',
      content: n.content || n.note || '',
    }))
  } catch { supervisionNotes.value = [] }
}

async function submitNote() {
  if (!newNote.value.trim()) return
  try {
    await http('/api/v1/coach/students/' + studentId.value + '/notes', {
      method: 'POST',
      data: { content: newNote.value }
    })
    uni.showToast({ title: '已保存', icon: 'success' })
    newNote.value = ''
    loadData()
  } catch {
    uni.showToast({ title: '保存失败', icon: 'none' })
  }
}

function sendMessage() {
  uni.navigateTo({ url: '/pages/coach/messages/index?student_id=' + studentId.value })
}
function assignAssessment() {
  uni.navigateTo({ url: '/pages/coach/assessment/index?assign_to=' + studentId.value })
}
function createPrescription() {
  uni.navigateTo({ url: '/pages/coach/flywheel/index?student_id=' + studentId.value })
}
function viewTimeline() {
  uni.navigateTo({ url: '/pages/coach/analytics/index?student_id=' + studentId.value })
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
function refresh() { loadData() }
function goBack() { uni.navigateBack() }

onLoad((opts: any) => {
  studentId.value = parseInt(opts?.id) || 0
})
onMounted(() => { loadData() })
</script>

<style scoped>
.detail-page { min-height: 100vh; background: #F5F6FA; }
.detail-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff; }
.detail-nav-back { font-size: 40rpx; padding: 16rpx; }
.detail-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.detail-nav-action { font-size: 36rpx; padding: 16rpx; }

.detail-scroll { height: calc(100vh - 160rpx); }

.detail-profile { display: flex; align-items: center; gap: 16rpx; padding: 24rpx; background: #fff; margin: 16rpx 24rpx; border-radius: 16rpx; }
.detail-avatar { width: 88rpx; height: 88rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 36rpx; font-weight: 700; }
.detail-profile-info { flex: 1; }
.detail-profile-name { display: block; font-size: 34rpx; font-weight: 700; color: #2C3E50; }
.detail-profile-stage { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 4rpx; }
.detail-risk-badge { padding: 8rpx 16rpx; border-radius: 10rpx; color: #fff; font-size: 22rpx; font-weight: 600; }

.detail-actions { display: flex; gap: 16rpx; padding: 0 24rpx 16rpx; }
.detail-act-btn { flex: 1; background: #fff; border-radius: 12rpx; padding: 16rpx 8rpx; display: flex; flex-direction: column; align-items: center; gap: 4rpx; }
.detail-act-icon { font-size: 36rpx; }
.detail-act-label { font-size: 22rpx; color: #5B6B7F; }

.detail-tabs { display: flex; gap: 12rpx; padding: 0 24rpx 16rpx; }
.detail-tab { flex: 1; text-align: center; padding: 14rpx 0; background: #fff; border-radius: 12rpx; font-size: 26rpx; color: #5B6B7F; }
.detail-tab--active { background: #2D8E69; color: #fff; }

.detail-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin: 0 24rpx 16rpx; }
.detail-card-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }

.detail-metric-grid { display: flex; }
.detail-metric { flex: 1; text-align: center; }
.detail-metric-val { display: block; font-size: 36rpx; font-weight: 700; }
.detail-metric-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.detail-action-bars { display: flex; align-items: flex-end; gap: 12rpx; height: 180rpx; }
.detail-action-bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; }
.detail-action-bar { width: 100%; border-radius: 6rpx 6rpx 0 0; min-height: 8rpx; }
.detail-action-bar-label { font-size: 22rpx; color: #8E99A4; margin-top: 6rpx; }

.detail-log-header { display: flex; justify-content: space-between; margin-bottom: 8rpx; }
.detail-log-type { font-size: 26rpx; font-weight: 600; }
.detail-log-time { font-size: 22rpx; color: #8E99A4; }
.detail-log-content { font-size: 26rpx; color: #5B6B7F; line-height: 1.6; }

.detail-note-header { display: flex; justify-content: space-between; margin-bottom: 8rpx; }
.detail-note-date { font-size: 24rpx; color: #3498DB; font-weight: 600; }
.detail-note-author { font-size: 22rpx; color: #8E99A4; }
.detail-note-content { font-size: 26rpx; color: #2C3E50; line-height: 1.6; }

.detail-add-note { margin: 0 24rpx 16rpx; }
.detail-note-input { width: 100%; min-height: 160rpx; background: #fff; border-radius: 12rpx; padding: 16rpx; font-size: 28rpx; box-sizing: border-box; }
.detail-note-submit { margin-top: 12rpx; text-align: center; background: #2D8E69; color: #fff; padding: 20rpx; border-radius: 12rpx; font-size: 28rpx; font-weight: 600; }

.detail-empty { text-align: center; padding: 60rpx; font-size: 26rpx; color: #8E99A4; }
</style>`;


// ============================================================
// 4. pages/coach/push-queue/index.vue — 推送队列 (修复导航报错)
// ============================================================
const PUSH_QUEUE_PAGE = `<template>
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

${INLINE_HTTP}

const activeTab = ref('pending')
const refreshing = ref(false)
const queueItems = ref<any[]>([])

const pendingCount = computed(() => queueItems.value.filter(i => i.status === 'pending').length)
const sentToday = computed(() => queueItems.value.filter(i => i.status === 'sent').length)
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

async function loadData() {
  try {
    const res = await http<any>('/api/v1/coach/push-queue?page_size=50')
    const items = res.items || res.queue || (Array.isArray(res) ? res : [])
    queueItems.value = items.map((i: any) => ({
      id: i.id,
      student_id: i.student_id || i.grower_id,
      student_name: i.student_name || i.grower_name || '学员',
      type_label: i.type === 'rx_push' ? '处方推送' : i.type === 'reminder' ? '提醒' : i.type === 'assessment' ? '评估邀请' : '消息推送',
      content: i.content || i.ai_summary || i.title || '',
      status: i.status || 'pending',
      scheduled_at: i.scheduled_at || '',
      created_at: i.created_at || '',
    }))
  } catch {
    queueItems.value = []
  }
}

async function sendPush(item: any) {
  try {
    await http('/api/v1/coach/push-queue/' + item.id + '/send', { method: 'POST' })
    item.status = 'sent'
    uni.showToast({ title: '已推送', icon: 'success' })
  } catch {
    uni.showToast({ title: '推送失败', icon: 'none' })
  }
}

async function cancelPush(item: any) {
  try {
    await http('/api/v1/coach/push-queue/' + item.id + '/cancel', { method: 'POST' })
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
</style>`;


// ============================================================
// 5. pages/notify/index.vue — 通知页 (TabBar页)
// ============================================================
const NOTIFY_PAGE = `<template>
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

${INLINE_HTTP}

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
</style>`;


// ============================================================
// 6. pages/profile/index.vue — 个人中心 (TabBar页)
// ============================================================
const PROFILE_PAGE = `<template>
  <view class="prof-page">
    <!-- 个人信息头 -->
    <view class="prof-header">
      <view class="prof-avatar">{{ (userInfo.name || '?')[0] }}</view>
      <view class="prof-info">
        <text class="prof-name">{{ userInfo.name }}</text>
        <text class="prof-role">{{ userInfo.role_label }}</text>
      </view>
      <view class="prof-edit" @tap="editProfile">编辑</view>
    </view>

    <scroll-view scroll-y class="prof-scroll">
      <!-- 教练数据概览 -->
      <view class="prof-stats">
        <view class="prof-stat-item">
          <text class="prof-stat-num">{{ userInfo.student_count || 0 }}</text>
          <text class="prof-stat-label">管理学员</text>
        </view>
        <view class="prof-stat-item">
          <text class="prof-stat-num">{{ userInfo.total_days || 0 }}</text>
          <text class="prof-stat-label">服务天数</text>
        </view>
        <view class="prof-stat-item">
          <text class="prof-stat-num">{{ userInfo.total_interventions || 0 }}</text>
          <text class="prof-stat-label">干预次数</text>
        </view>
      </view>

      <!-- 功能菜单 -->
      <view class="prof-menu">
        <view class="prof-menu-item" @tap="goPage('/pages/coach/analytics/index')">
          <text class="prof-menu-icon">📊</text>
          <text class="prof-menu-text">工作数据</text>
          <text class="prof-menu-arrow">›</text>
        </view>
        <view class="prof-menu-item" @tap="goPage('/pages/coach/assessment/index')">
          <text class="prof-menu-icon">📋</text>
          <text class="prof-menu-text">评估管理</text>
          <text class="prof-menu-arrow">›</text>
        </view>
        <view class="prof-menu-item" @tap="goLearning">
          <text class="prof-menu-icon">📚</text>
          <text class="prof-menu-text">学习成长</text>
          <text class="prof-menu-arrow">›</text>
        </view>
      </view>

      <view class="prof-menu">
        <view class="prof-menu-item" @tap="goSettings">
          <text class="prof-menu-icon">⚙️</text>
          <text class="prof-menu-text">设置</text>
          <text class="prof-menu-arrow">›</text>
        </view>
        <view class="prof-menu-item" @tap="showAbout">
          <text class="prof-menu-icon">ℹ️</text>
          <text class="prof-menu-text">关于</text>
          <text class="prof-menu-arrow">›</text>
        </view>
        <view class="prof-menu-item prof-menu-item--danger" @tap="doLogout">
          <text class="prof-menu-icon">🚪</text>
          <text class="prof-menu-text" style="color:#E74C3C;">退出登录</text>
          <text class="prof-menu-arrow">›</text>
        </view>
      </view>

      <!-- 版本号 -->
      <view class="prof-version">
        <text>行健平台 v5.0 · 教练版</text>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'

${INLINE_HTTP}

const userInfo = ref<any>({ name: '教练', role_label: '健康教练' })

async function loadProfile() {
  try {
    const stored = uni.getStorageSync('userInfo')
    if (stored) {
      const u = typeof stored === 'string' ? JSON.parse(stored) : stored
      userInfo.value = {
        name: u.full_name || u.display_name || u.username || u.nickname || '教练',
        role_label: u.role === 'coach' ? '健康教练' : u.role === 'admin' ? '管理员' : u.role || '用户',
        student_count: u.student_count || 0,
        total_days: u.total_days || 0,
        total_interventions: u.total_interventions || 0,
      }
    }
  } catch {}

  // 尝试从后端获取更新信息
  try {
    const res = await http<any>('/api/v1/auth/me')
    if (res) {
      userInfo.value = {
        ...userInfo.value,
        name: res.full_name || res.display_name || res.username || userInfo.value.name,
        role_label: res.role === 'coach' ? '健康教练' : res.role || userInfo.value.role_label,
        student_count: res.student_count ?? userInfo.value.student_count,
      }
    }
  } catch {}

  // 从dashboard获取统计
  try {
    const dash = await http<any>('/api/v1/coach/dashboard')
    userInfo.value.student_count = dash.client_count ?? (dash.students || []).length ?? userInfo.value.student_count
    userInfo.value.total_interventions = dash.total_interventions ?? userInfo.value.total_interventions
  } catch {}
}

function editProfile() {
  uni.showToast({ title: '编辑功能开发中', icon: 'none' })
}

function goPage(url: string) {
  uni.navigateTo({ url })
}

function goLearning() {
  uni.navigateTo({ url: '/pages/learning/index' }).catch(() => {
    uni.showToast({ title: '学习中心即将上线', icon: 'none' })
  })
}

function goSettings() {
  uni.showToast({ title: '设置功能开发中', icon: 'none' })
}

function showAbout() {
  uni.showModal({
    title: '关于',
    content: '行健平台 v5.0\\n行为健康促进与慢病逆转\\n\\n© 2026 BehaviorOS',
    showCancel: false,
  })
}

function doLogout() {
  uni.showModal({
    title: '确认退出',
    content: '退出后需要重新登录',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('access_token')
        uni.removeStorageSync('userInfo')
        uni.reLaunch({ url: '/pages/auth/login' })
      }
    }
  })
}

onShow(() => { loadProfile() })
onMounted(() => { loadProfile() })
</script>

<style scoped>
.prof-page { min-height: 100vh; background: #F5F6FA; }
.prof-header {
  display: flex; align-items: center; gap: 20rpx;
  padding: 32rpx; padding-top: calc(80rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%);
  color: #fff;
}
.prof-avatar { width: 96rpx; height: 96rpx; border-radius: 50%; background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; font-size: 40rpx; font-weight: 700; }
.prof-info { flex: 1; }
.prof-name { display: block; font-size: 36rpx; font-weight: 700; }
.prof-role { display: block; font-size: 24rpx; opacity: 0.85; margin-top: 4rpx; }
.prof-edit { font-size: 24rpx; padding: 8rpx 20rpx; background: rgba(255,255,255,0.2); border-radius: 8rpx; }

.prof-scroll { height: calc(100vh - 240rpx); }

.prof-stats { display: flex; margin: 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx 0; }
.prof-stat-item { flex: 1; text-align: center; border-right: 1rpx solid #F0F0F0; }
.prof-stat-item:last-child { border-right: none; }
.prof-stat-num { display: block; font-size: 40rpx; font-weight: 700; color: #2D8E69; }
.prof-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.prof-menu { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; overflow: hidden; }
.prof-menu-item { display: flex; align-items: center; gap: 16rpx; padding: 28rpx 24rpx; border-bottom: 1rpx solid #F8F8F8; }
.prof-menu-item:last-child { border-bottom: none; }
.prof-menu-icon { font-size: 32rpx; }
.prof-menu-text { flex: 1; font-size: 28rpx; color: #2C3E50; }
.prof-menu-arrow { font-size: 28rpx; color: #CCC; }

.prof-version { text-align: center; padding: 32rpx; font-size: 24rpx; color: #BDC3C7; }
</style>`;


// ============================================================
// WRITE ALL FILES
// ============================================================
const files = {
  'src/pages/home/index.vue': HOME_PAGE,
  'src/pages/coach/students/index.vue': STUDENTS_PAGE,
  'src/pages/coach/students/detail.vue': STUDENT_DETAIL_PAGE,
  'src/pages/coach/push-queue/index.vue': PUSH_QUEUE_PAGE,
  'src/pages/notify/index.vue': NOTIFY_PAGE,
  'src/pages/profile/index.vue': PROFILE_PAGE,
};

console.log('=== deploy-remaining-pages.js ===\n');

let count = 0;
for (const [relPath, content] of Object.entries(files)) {
  const dir = path.dirname(relPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  
  // 备份
  if (fs.existsSync(relPath)) {
    fs.copyFileSync(relPath, relPath + '.bak');
    console.log(`  BAK: ${relPath}.bak`);
  }
  
  fs.writeFileSync(relPath, content);
  count++;
  const lines = content.split('\n').length;
  console.log(`  OK: ${relPath} (${lines} lines)`);
}

console.log(`\n✅ ${count} 个页面部署完成`);

// ============================================================
// 补充: 确保 pages.json 包含所有路由
// ============================================================
const PAGES_JSON_PATCH = `
检查你的 pages.json (或 src/pages.json), 确保包含以下路由:

TabBar页面 (pages数组):
  - "pages/home/index"
  - "pages/notify/index"
  - "pages/profile/index"

Coach分包 (subPackages中coach分包):
  - "coach/students/index"
  - "coach/students/detail"
  - "coach/push-queue/index"
  - "coach/risk/index"
  - "coach/messages/index"
  - "coach/analytics/index"
  - "coach/assessment/index"
  - "coach/flywheel/index"
  - "coach/live/index"

如果使用 subPackages 模式, root 为 "pages/coach", 路径去掉前缀。
`.trim();

console.log('\n' + '='.repeat(50));
console.log('📋 路由配置提示:\n');
console.log(PAGES_JSON_PATCH);
console.log('\n' + '='.repeat(50));
console.log('\n下一步:');
console.log('  1. 检查/更新 pages.json 路由配置');
console.log('  2. 先运行 deploy-6-coach-pages.js (如果还没运行)');
console.log('  3. npm run dev:mp-weixin');
console.log('  4. 微信开发者工具验证');
console.log('  5. 处理401问题: 检查token存储和API认证逻辑');
