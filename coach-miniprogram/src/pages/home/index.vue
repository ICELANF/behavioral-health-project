<template>
  <view class="home-page">
    <!-- ═══ COACH 首页 ═══ -->
    <template v-if="userRole === 'coach'">
      <view class="home-header home-header--coach">
        <view class="home-greeting">
          <text class="home-hello">{{ greetText }}</text>
          <text class="home-name">{{ userName }}</text>
        </view>
        <view class="home-date">{{ todayStr }}</view>
      </view>
      <scroll-view scroll-y class="home-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
        <view class="home-stats">
          <view class="home-stat-card" @tap="goPage('/pages/coach/students/index')">
            <text class="home-stat-icon">👥</text>
            <text class="home-stat-num">{{ coachStats.clientCount }}</text>
            <text class="home-stat-label">我的学员</text>
          </view>
          <view class="home-stat-card home-stat-card--warn" @tap="goPage('/pages/coach/risk/index')">
            <text class="home-stat-icon">⚠️</text>
            <text class="home-stat-num">{{ coachStats.riskCount }}</text>
            <text class="home-stat-label">风险预警</text>
          </view>
          <view class="home-stat-card home-stat-card--blue" @tap="goPage('/pages/coach/push-queue/index')">
            <text class="home-stat-icon">📤</text>
            <text class="home-stat-num">{{ coachStats.pendingRx }}</text>
            <text class="home-stat-label">待审处方</text>
          </view>
          <view class="home-stat-card home-stat-card--purple" @tap="goPage('/pages/coach/assessment/index')">
            <text class="home-stat-icon">📊</text>
            <text class="home-stat-num">{{ coachStats.pendingAssess }}</text>
            <text class="home-stat-label">待审评估</text>
          </view>
        </view>
        <view class="home-section">
          <view class="home-section-header">
            <text class="home-section-title">📌 今日待办</text>
            <text class="home-section-more" @tap="goPage('/pages/coach/flywheel/index')">查看全部 ›</text>
          </view>
          <view v-if="todos.length > 0" class="home-todo-list">
            <view v-for="(item, idx) in todos.slice(0,5)" :key="idx" class="home-todo-item" @tap="handleTodo(item)">
              <view class="home-todo-dot" :style="{ background: priorityColor(item.priority) }"></view>
              <view class="home-todo-body">
                <text class="home-todo-title">{{ item.title }}</text>
                <text class="home-todo-sub">{{ item.student_name || '' }} · {{ item.type_label || '任务' }}</text>
              </view>
              <text class="home-todo-arrow">›</text>
            </view>
          </view>
          <view v-else class="home-empty-hint"><text>✅ 今日待办已清空，辛苦了！</text></view>
        </view>
        <view class="home-section">
          <view class="home-section-header">
            <text class="home-section-title">🔔 学员动态</text>
            <text class="home-section-more" @tap="goPage('/pages/coach/messages/index')">更多 ›</text>
          </view>
          <view v-if="activities.length > 0" class="home-activity-list">
            <view v-for="(a, idx) in activities.slice(0,6)" :key="idx" class="home-activity-item">
              <view class="home-activity-avatar" :style="{ background: avatarColor(a.student_name) }">{{ (a.student_name||'?')[0] }}</view>
              <view class="home-activity-body">
                <text class="home-activity-text"><text style="font-weight:600;">{{ a.student_name }}</text> {{ a.action_text || '完成了一项任务' }}</text>
                <text class="home-activity-time">{{ a.time_ago || '' }}</text>
              </view>
            </view>
          </view>
          <view v-else class="home-empty-hint"><text>暂无新动态</text></view>
        </view>
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
            <view class="home-shortcut" @tap="goPage('/pages/coach/health-review/index')">
              <view class="home-sc-icon" style="background:#FFF0E6;">🩺</view>
              <text class="home-sc-label">健康审核</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/coach/push-queue/index')">
              <view class="home-sc-icon" style="background:#F0FFF0;">📤</view>
              <text class="home-sc-label">推送队列</text>
            </view>
          </view>
        </view>
        <view style="height:120rpx;"></view>
      </scroll-view>
    </template>

    <!-- ═══ GROWER 首页 ═══ -->
    <template v-else-if="userRole === 'grower'">
      <view class="home-header home-header--grower">
        <view class="home-greeting">
          <text class="home-hello">{{ greetText }}</text>
          <text class="home-name">{{ userName }}</text>
        </view>
        <view class="home-date">{{ todayStr }}</view>
      </view>
      <scroll-view scroll-y class="home-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
        <!-- 健康数据快览 -->
        <view class="home-health-cards">
          <view class="home-health-card" @tap="goPage('/pages/health/blood-glucose')">
            <text class="home-health-icon">🩸</text>
            <text class="home-health-val">{{ growerHealth.glucose || '—' }}</text>
            <text class="home-health-unit">mmol/L</text>
            <text class="home-health-label">血糖</text>
          </view>
          <view class="home-health-card" @tap="goPage('/pages/health/weight')">
            <text class="home-health-icon">⚖️</text>
            <text class="home-health-val">{{ growerHealth.weight || '—' }}</text>
            <text class="home-health-unit">kg</text>
            <text class="home-health-label">体重</text>
          </view>
          <view class="home-health-card" @tap="goPage('/pages/health/exercise')">
            <text class="home-health-icon">👟</text>
            <text class="home-health-val">{{ growerHealth.steps || '—' }}</text>
            <text class="home-health-unit">步</text>
            <text class="home-health-label">今日步数</text>
          </view>
        </view>

        <!-- 今日任务 -->
        <view class="home-section">
          <view class="home-section-header">
            <text class="home-section-title">📋 今日任务</text>
            <text class="home-section-more" @tap="goPage('/pages/journey/progress')">全部 ›</text>
          </view>
          <view v-if="growerTasks.length > 0">
            <view v-for="(t, i) in growerTasks.slice(0,4)" :key="i" class="home-task-item">
              <view class="home-task-check" :class="{ 'home-task-check--done': t.done }" @tap="toggleTask(t)">{{ t.done ? '✓' : '' }}</view>
              <text class="home-task-text" :class="{ 'home-task-text--done': t.done }">{{ t.title }}</text>
              <text class="home-task-pts">+{{ t.points || 10 }}分</text>
            </view>
            <view class="home-task-progress">
              <view class="home-task-bar">
                <view class="home-task-fill" :style="{ width: growerTaskProgress + '%' }"></view>
              </view>
              <text class="home-task-pct">{{ growerTaskProgress }}% 完成</text>
            </view>
          </view>
          <view v-else class="home-empty-hint"><text>📭 今日无任务，教练还未分配</text></view>
        </view>

        <!-- 待完成评估 -->
        <view class="home-section" v-if="growerPendingAssess > 0">
          <view class="home-assess-banner" @tap="goPage('/pages/assessment/pending')">
            <text class="home-assess-icon">📝</text>
            <view class="home-assess-body">
              <text class="home-assess-title">您有 {{ growerPendingAssess }} 份评估待完成</text>
              <text class="home-assess-sub">教练已为您安排评估，完成后获得积分</text>
            </view>
            <text class="home-assess-arrow">›</text>
          </view>
        </view>

        <!-- 快捷入口 -->
        <view class="home-section">
          <text class="home-section-title">⚡ 快捷入口</text>
          <view class="home-shortcuts">
            <view class="home-shortcut" @tap="goPage('/pages/health/blood-glucose')">
              <view class="home-sc-icon" style="background:#FFF0F5;">🩸</view>
              <text class="home-sc-label">记录血糖</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/food/scan')">
              <view class="home-sc-icon" style="background:#F0FFF4;">🥗</view>
              <text class="home-sc-label">记录饮食</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/health/exercise')">
              <view class="home-sc-icon" style="background:#EEF6FF;">🏃</view>
              <text class="home-sc-label">运动记录</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/learning/index')">
              <view class="home-sc-icon" style="background:#FFF8EE;">📚</view>
              <text class="home-sc-label">学习中心</text>
            </view>
          </view>
        </view>

        <view style="height:120rpx;"></view>
      </scroll-view>
    </template>

    <!-- ═══ SHARER 首页 ═══ -->
    <template v-else-if="userRole === 'sharer'">
      <view class="home-header home-header--sharer">
        <view class="home-greeting">
          <text class="home-hello">{{ greetText }}</text>
          <text class="home-name">{{ userName }}</text>
        </view>
        <view class="home-role-badge">分享者</view>
      </view>
      <scroll-view scroll-y class="home-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
        <!-- 同道者概览 -->
        <view class="home-stats">
          <view class="home-stat-card" @tap="goPage('/pages/sharer/mentees')">
            <text class="home-stat-icon">👤</text>
            <text class="home-stat-num">{{ sharerData.menteeCount }}</text>
            <text class="home-stat-label">我的学员</text>
          </view>
          <view class="home-stat-card home-stat-card--blue" @tap="goPage('/pages/sharer/mentees')">
            <text class="home-stat-icon">🔥</text>
            <text class="home-stat-num">{{ sharerData.activeToday }}</text>
            <text class="home-stat-label">今日活跃</text>
          </view>
          <view class="home-stat-card home-stat-card--purple" @tap="goPage('/pages/sharer/share-content')">
            <text class="home-stat-icon">📢</text>
            <text class="home-stat-num">{{ sharerData.published }}</text>
            <text class="home-stat-label">已发布</text>
          </view>
          <view class="home-stat-card home-stat-card--warn">
            <text class="home-stat-icon">⭐</text>
            <text class="home-stat-num">{{ sharerData.influence }}</text>
            <text class="home-stat-label">影响力</text>
          </view>
        </view>

        <!-- 学员动态 -->
        <view class="home-section">
          <view class="home-section-header">
            <text class="home-section-title">🔔 学员动态</text>
            <text class="home-section-more" @tap="goPage('/pages/sharer/mentees')">查看全部 ›</text>
          </view>
          <view v-if="sharerMentees.length > 0">
            <view v-for="m in sharerMentees.slice(0,5)" :key="m.id" class="home-activity-item">
              <view class="home-activity-avatar" :style="{ background: avatarColor(m.name) }">{{ (m.name||'?')[0] }}</view>
              <view class="home-activity-body">
                <text class="home-activity-text" style="font-weight:600;">{{ m.name }}</text>
                <text class="home-activity-time">连续打卡 {{ m.streak || 0 }} 天 · {{ m.status === 'active' ? '今日已打卡' : '未打卡' }}</text>
              </view>
              <text :style="{ color: m.status === 'active' ? '#27AE60' : '#E74C3C', fontSize: '24rpx' }">{{ m.today_pct || 0 }}%</text>
            </view>
          </view>
          <view v-else class="home-empty-hint"><text>暂无学员动态</text></view>
        </view>

        <!-- 快捷入口 -->
        <view class="home-section">
          <text class="home-section-title">⚡ 快捷入口</text>
          <view class="home-shortcuts">
            <view class="home-shortcut" @tap="goPage('/pages/sharer/mentees')">
              <view class="home-sc-icon" style="background:#EEF6FF;">👥</view>
              <text class="home-sc-label">我的学员</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/sharer/share-content')">
              <view class="home-sc-icon" style="background:#F0FFF4;">📝</view>
              <text class="home-sc-label">内容分享</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/health/index')">
              <view class="home-sc-icon" style="background:#FFF0F5;">❤️</view>
              <text class="home-sc-label">我的健康</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/learning/index')">
              <view class="home-sc-icon" style="background:#FFF8EE;">📚</view>
              <text class="home-sc-label">学习中心</text>
            </view>
          </view>
        </view>
        <view style="height:120rpx;"></view>
      </scroll-view>
    </template>

    <!-- ═══ SUPERVISOR 首页 ═══ -->
    <template v-else-if="userRole === 'supervisor'">
      <view class="home-header home-header--supervisor">
        <view class="home-greeting">
          <text class="home-hello">{{ greetText }}</text>
          <text class="home-name">{{ userName }}</text>
        </view>
        <view class="home-role-badge">督导</view>
      </view>
      <scroll-view scroll-y class="home-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
        <view class="home-stats">
          <view class="home-stat-card" @tap="goPage('/pages/supervisor/coaches')">
            <text class="home-stat-icon">👨‍🏫</text>
            <text class="home-stat-num">{{ supervisorData.coachCount }}</text>
            <text class="home-stat-label">管理教练</text>
          </view>
          <view class="home-stat-card home-stat-card--warn" @tap="goPage('/pages/supervisor/review-queue')">
            <text class="home-stat-icon">🔍</text>
            <text class="home-stat-num">{{ supervisorData.pendingReview }}</text>
            <text class="home-stat-label">待审核</text>
          </view>
          <view class="home-stat-card home-stat-card--warn">
            <text class="home-stat-icon">⚠️</text>
            <text class="home-stat-num">{{ supervisorData.highRisk }}</text>
            <text class="home-stat-label">高风险学员</text>
          </view>
          <view class="home-stat-card home-stat-card--blue">
            <text class="home-stat-icon">✅</text>
            <text class="home-stat-num">{{ supervisorData.approvedToday }}</text>
            <text class="home-stat-label">今日审批</text>
          </view>
        </view>
        <view class="home-section">
          <text class="home-section-title">⚡ 快捷入口</text>
          <view class="home-shortcuts">
            <view class="home-shortcut" @tap="goPage('/pages/supervisor/coaches')">
              <view class="home-sc-icon" style="background:#EEF6FF;">👨‍🏫</view>
              <text class="home-sc-label">教练管理</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/supervisor/review-queue')">
              <view class="home-sc-icon" style="background:#FFF0E6;">🔍</view>
              <text class="home-sc-label">审核队列</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/coach/analytics/index')">
              <view class="home-sc-icon" style="background:#F0FFF4;">📈</view>
              <text class="home-sc-label">数据分析</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/notifications/index')">
              <view class="home-sc-icon" style="background:#FFF8EE;">🔔</view>
              <text class="home-sc-label">消息中心</text>
            </view>
          </view>
        </view>
        <view style="height:120rpx;"></view>
      </scroll-view>
    </template>

    <!-- ═══ MASTER 首页 ═══ -->
    <template v-else-if="userRole === 'master'">
      <view class="home-header home-header--master">
        <view class="home-greeting">
          <text class="home-hello">{{ greetText }}</text>
          <text class="home-name">{{ userName }}</text>
        </view>
        <view class="home-role-badge">专家</view>
      </view>
      <scroll-view scroll-y class="home-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
        <view class="home-stats">
          <view class="home-stat-card home-stat-card--warn" @tap="goPage('/pages/master/critical-review')">
            <text class="home-stat-icon">🚨</text>
            <text class="home-stat-num">{{ masterData.critical }}</text>
            <text class="home-stat-label">危急病例</text>
          </view>
          <view class="home-stat-card home-stat-card--blue">
            <text class="home-stat-icon">🤖</text>
            <text class="home-stat-num">{{ masterData.aiPending }}</text>
            <text class="home-stat-label">AI分析待审</text>
          </view>
          <view class="home-stat-card home-stat-card--purple" @tap="goPage('/pages/master/knowledge')">
            <text class="home-stat-icon">📚</text>
            <text class="home-stat-num">{{ masterData.knowledgePending }}</text>
            <text class="home-stat-label">知识待发布</text>
          </view>
          <view class="home-stat-card">
            <text class="home-stat-icon">✅</text>
            <text class="home-stat-num">{{ masterData.reviewedToday }}</text>
            <text class="home-stat-label">今日审核</text>
          </view>
        </view>
        <view class="home-section">
          <text class="home-section-title">⚡ 快捷入口</text>
          <view class="home-shortcuts">
            <view class="home-shortcut" @tap="goPage('/pages/master/critical-review')">
              <view class="home-sc-icon" style="background:#FFF2F2;">🚨</view>
              <text class="home-sc-label">危急审核</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/master/dashboard')">
              <view class="home-sc-icon" style="background:#EEF6FF;">🤖</view>
              <text class="home-sc-label">AI分析</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/master/knowledge')">
              <view class="home-sc-icon" style="background:#F5F0FF;">📚</view>
              <text class="home-sc-label">知识库</text>
            </view>
            <view class="home-shortcut" @tap="goPage('/pages/coach/analytics/index')">
              <view class="home-sc-icon" style="background:#F0FFF4;">📊</view>
              <text class="home-sc-label">数据概览</text>
            </view>
          </view>
        </view>
        <view style="height:120rpx;"></view>
      </scroll-view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { httpReq as http } from '@/api/request'

// ── 通用 ──────────────────────────────────────────────
const userRole = ref('coach')
const userName = ref('用户')
const refreshing = ref(false)

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
  const wds = ['日','一','二','三','四','五','六']
  return `${d.getMonth()+1}月${d.getDate()}日 周${wds[d.getDay()]}`
})

function detectRole() {
  try {
    const raw = uni.getStorageSync('user_info')
    if (raw) {
      const u = typeof raw === 'string' ? JSON.parse(raw) : raw
      userRole.value = (u.role || 'coach').toLowerCase()
      userName.value = u.full_name || u.display_name || u.username || '用户'
    }
  } catch {}
}

function goPage(url: string) { uni.navigateTo({ url }) }
function priorityColor(p: string): string {
  const m: Record<string,string> = { urgent:'#E74C3C', high:'#E67E22', normal:'#3498DB', low:'#27AE60' }
  return m[p] || '#8E99A4'
}
const colorPool = ['#3498DB','#E74C3C','#27AE60','#9B59B6','#E67E22','#1ABC9C','#34495E']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let h = 0; for (let i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h)
  return colorPool[Math.abs(h) % colorPool.length]
}

// ── COACH 数据 ─────────────────────────────────────────
const coachStats = ref({ clientCount:0, riskCount:0, pendingRx:0, pendingAssess:0 })
const todos = ref<any[]>([])
const activities = ref<any[]>([])

async function loadCoach() {
  try {
    const res = await http<any>('/api/v1/coach/dashboard')
    const ts = res.today_stats || {}
    const students = res.students || []
    coachStats.value = {
      clientCount:   ts.total_students ?? students.length ?? 0,
      riskCount:     ts.alert_students ?? 0,
      pendingRx:     ts.pending_followups ?? 0,
      pendingAssess: ts.pending_followups ?? 0,
    }
    activities.value = students.slice(0,10).map((s: any) => ({
      student_name: s.name || s.full_name || s.username || '未知',
      action_text: s.micro_action_count ? `完成了${s.micro_action_count}个微行动` : (s.days_since_last_contact === 0 ? '今天活跃' : `${s.days_since_last_contact ?? '?'}天未活跃`),
      time_ago: s.last_active_time || '',
    }))
  } catch {}
  try {
    const res = await http<any>('/api/v1/coach/push-queue?status=pending&page_size=10')
    todos.value = (res.items || []).map((i: any) => ({
      id: i.id, title: i.title || i.content?.slice(0,30) || '待处理',
      student_name: i.student_name || '', type: i.source_type || 'rx_push',
      type_label: i.source_type === 'rx_push' ? '处方推送' : '待办', priority: i.priority || 'normal',
    }))
  } catch {}
}

function handleTodo(item: any) {
  uni.navigateTo({ url: '/pages/coach/push-queue/index' })
}

// ── GROWER 数据 ────────────────────────────────────────
const growerHealth = ref<any>({ glucose: null, weight: null, steps: null })
const growerTasks = ref<any[]>([])
const growerPendingAssess = ref(0)

const growerTaskProgress = computed(() => {
  if (!growerTasks.value.length) return 0
  const done = growerTasks.value.filter(t => t.done).length
  return Math.round((done / growerTasks.value.length) * 100)
})

async function loadGrower() {
  try {
    const res = await http<any>('/api/v1/health-data/summary')
    growerHealth.value = {
      glucose: res.latest_glucose?.value?.toFixed(1) ?? null,
      weight:  res.latest_weight?.toFixed(1) ?? null,
      steps:   res.today_steps ?? null,
    }
  } catch {}
  try {
    const res = await http<any>('/api/v1/daily-tasks/today')
    growerTasks.value = (res.tasks || []).map((t: any) => ({
      id: t.id, title: t.title || t.description || '任务',
      done: t.status === 'completed' || t.completed === true,
      points: t.points || 10,
    }))
  } catch {}
  try {
    const res = await http<any>('/api/v1/assessment-assignments/my-pending')
    growerPendingAssess.value = (res.items || res.assignments || []).filter((a: any) => ['pending','assigned'].includes(a.status)).length
  } catch {}
}

async function toggleTask(task: any) {
  if (task.done) return
  try {
    await http(`/api/v1/daily-tasks/${task.id}/checkin`, { method: 'POST', data: {} })
    task.done = true
    uni.showToast({ title: `+${task.points}分`, icon: 'success' })
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

// ── SHARER 数据 ────────────────────────────────────────
const sharerData = ref({ menteeCount:0, activeToday:0, published:0, influence:0 })
const sharerMentees = ref<any[]>([])

async function loadSharer() {
  try {
    const res = await http<any>('/api/v1/sharer/mentee-progress')
    sharerMentees.value = res.mentees || []
    sharerData.value.menteeCount = sharerMentees.value.length
    sharerData.value.activeToday = sharerMentees.value.filter((m: any) => m.status === 'active').length
  } catch {}
  try {
    const res = await http<any>('/api/v1/sharer/contribution-stats')
    sharerData.value.published = res.published ?? 0
  } catch {}
  try {
    const res = await http<any>('/api/v1/sharer/influence-score')
    sharerData.value.influence = res.total ?? 0
  } catch {}
}

// ── SUPERVISOR 数据 ────────────────────────────────────
const supervisorData = ref({ coachCount:0, pendingReview:0, highRisk:0, approvedToday:0 })

async function loadSupervisor() {
  try {
    const res = await http<any>('/api/v1/supervisor/dashboard')
    supervisorData.value = {
      coachCount:    res.coach_count ?? 0,
      pendingReview: res.pending_review ?? 0,
      highRisk:      res.high_risk_count ?? 0,
      approvedToday: res.approved_today ?? 0,
    }
  } catch {}
}

// ── MASTER 数据 ────────────────────────────────────────
const masterData = ref({ critical:0, aiPending:0, knowledgePending:0, reviewedToday:0 })

async function loadMaster() {
  try {
    const res = await http<any>('/api/v1/master/dashboard')
    masterData.value = {
      critical:        res.critical_count ?? 0,
      aiPending:       res.ai_pending ?? 0,
      knowledgePending: res.knowledge_pending ?? 0,
      reviewedToday:   res.reviewed_today ?? 0,
    }
  } catch {}
}

// ── 主加载 ─────────────────────────────────────────────
async function loadData() {
  detectRole()
  if (userRole.value === 'coach')      await loadCoach()
  else if (userRole.value === 'grower')     await loadGrower()
  else if (userRole.value === 'sharer')     await loadSharer()
  else if (userRole.value === 'supervisor') await loadSupervisor()
  else if (userRole.value === 'master')     await loadMaster()
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }

onShow(() => { loadData() })
onMounted(() => { loadData() })
</script>

<style scoped>
.home-page { min-height: 100vh; background: #F5F6FA; }

/* 顶部 Header - 角色色 */
.home-header {
  padding: 24rpx 32rpx;
  padding-top: calc(80rpx + env(safe-area-inset-top));
  color: #fff; display: flex; justify-content: space-between; align-items: flex-end;
}
.home-header--coach      { background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); }
.home-header--grower     { background: linear-gradient(135deg, #27AE60 0%, #2ECC71 100%); }
.home-header--sharer     { background: linear-gradient(135deg, #2980B9 0%, #3498DB 100%); }
.home-header--supervisor { background: linear-gradient(135deg, #D35400 0%, #E67E22 100%); }
.home-header--master     { background: linear-gradient(135deg, #7D3C98 0%, #9B59B6 100%); }

.home-greeting { display: flex; flex-direction: column; }
.home-hello { font-size: 26rpx; opacity: 0.85; }
.home-name  { font-size: 38rpx; font-weight: 700; margin-top: 4rpx; }
.home-date  { font-size: 24rpx; opacity: 0.8; }
.home-role-badge { font-size: 22rpx; padding: 6rpx 18rpx; background: rgba(255,255,255,0.2); border-radius: 20rpx; }

.home-scroll { height: calc(100vh - 200rpx); }

/* 统计卡片 */
.home-stats { display: flex; flex-wrap: wrap; gap: 16rpx; padding: 24rpx; }
.home-stat-card {
  flex: 1; min-width: 42%; background: #fff; border-radius: 20rpx; padding: 24rpx;
  display: flex; flex-direction: column; align-items: center;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.04); position: relative; overflow: hidden;
}
.home-stat-card::after { content:''; position:absolute; top:0; left:0; right:0; height:6rpx; background:#2D8E69; }
.home-stat-card--warn::after   { background: #E74C3C; }
.home-stat-card--blue::after   { background: #3498DB; }
.home-stat-card--purple::after { background: #9B59B6; }
.home-stat-icon  { font-size: 40rpx; margin-bottom: 8rpx; }
.home-stat-num   { font-size: 48rpx; font-weight: 800; color: #2C3E50; }
.home-stat-label { font-size: 24rpx; color: #8E99A4; margin-top: 4rpx; }

/* Section */
.home-section { margin: 0 24rpx 24rpx; background: #fff; border-radius: 20rpx; padding: 24rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.03); }
.home-section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.home-section-title { font-size: 30rpx; font-weight: 700; color: #2C3E50; }
.home-section-more  { font-size: 24rpx; color: #3498DB; }

/* 待办 */
.home-todo-list { }
.home-todo-item { display: flex; align-items: center; gap: 16rpx; padding: 16rpx 0; border-bottom: 1rpx solid #F8F8F8; }
.home-todo-item:last-child { border-bottom: none; }
.home-todo-dot  { width: 12rpx; height: 12rpx; border-radius: 50%; flex-shrink: 0; }
.home-todo-body { flex: 1; }
.home-todo-title { display: block; font-size: 28rpx; color: #2C3E50; font-weight: 500; }
.home-todo-sub   { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
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
.home-shortcut  { flex: 1; min-width: 20%; display: flex; flex-direction: column; align-items: center; }
.home-sc-icon   { width: 88rpx; height: 88rpx; border-radius: 20rpx; display: flex; align-items: center; justify-content: center; font-size: 40rpx; }
.home-sc-label  { font-size: 22rpx; color: #5B6B7F; margin-top: 8rpx; }

/* GROWER 健康卡片 */
.home-health-cards { display: flex; gap: 16rpx; padding: 24rpx; }
.home-health-card {
  flex: 1; background: #fff; border-radius: 16rpx; padding: 20rpx 12rpx;
  display: flex; flex-direction: column; align-items: center; text-align: center;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04);
}
.home-health-icon { font-size: 36rpx; margin-bottom: 8rpx; }
.home-health-val  { font-size: 36rpx; font-weight: 700; color: #2C3E50; line-height: 1; }
.home-health-unit { font-size: 18rpx; color: #8E99A4; margin-top: 2rpx; }
.home-health-label { font-size: 20rpx; color: #8E99A4; margin-top: 6rpx; }

/* GROWER 任务 */
.home-task-item { display: flex; align-items: center; gap: 16rpx; padding: 16rpx 0; border-bottom: 1rpx solid #F8F8F8; }
.home-task-item:last-child { border-bottom: none; }
.home-task-check {
  width: 44rpx; height: 44rpx; border-radius: 50%; border: 3rpx solid #27AE60;
  display: flex; align-items: center; justify-content: center;
  color: #27AE60; font-size: 24rpx; font-weight: 700; flex-shrink: 0;
}
.home-task-check--done { background: #27AE60; color: #fff; }
.home-task-text { flex: 1; font-size: 28rpx; color: #2C3E50; }
.home-task-text--done { color: #BDC3C7; text-decoration: line-through; }
.home-task-pts  { font-size: 22rpx; color: #27AE60; font-weight: 600; }
.home-task-progress { margin-top: 16rpx; display: flex; align-items: center; gap: 16rpx; }
.home-task-bar  { flex: 1; height: 8rpx; background: #F0F0F0; border-radius: 4rpx; overflow: hidden; }
.home-task-fill { height: 100%; background: #27AE60; border-radius: 4rpx; }
.home-task-pct  { font-size: 22rpx; color: #8E99A4; white-space: nowrap; }

/* GROWER 评估 Banner */
.home-assess-banner { display: flex; align-items: center; gap: 16rpx; background: #FFF8E6; border-radius: 12rpx; padding: 20rpx; border-left: 6rpx solid #E67E22; }
.home-assess-icon   { font-size: 40rpx; }
.home-assess-body   { flex: 1; }
.home-assess-title  { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.home-assess-sub    { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.home-assess-arrow  { font-size: 32rpx; color: #E67E22; }

.home-empty-hint { text-align: center; padding: 32rpx 0; font-size: 26rpx; color: #8E99A4; }
</style>
