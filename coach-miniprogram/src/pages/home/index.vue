<template>
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
        else reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail: (err: any) => reject(err)
    })
  })
}

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

// 统计数据（对齐 /v1/coach/dashboard 响应：{coach, today_stats, students}）
const stats = computed(() => {
  const d = dashboard.value
  const ts = d.today_stats || {}
  const students = d.students || []
  return {
    clientCount:   ts.total_students   ?? students.length ?? 0,
    riskCount:     ts.alert_students   ?? 0,
    pendingRx:     ts.pending_followups ?? 0,
    pendingAssess: ts.pending_followups ?? 0,
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
  // 1. coach name (key matches stores/user.ts: 'user_info')
  try {
    const raw = uni.getStorageSync('user_info')
    if (raw) {
      const u = typeof raw === 'string' ? JSON.parse(raw) : raw
      coachName.value = u.full_name || u.username || '教练'
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
</style>