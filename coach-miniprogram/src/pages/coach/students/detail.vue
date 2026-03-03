<template>
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
import { httpReq as http } from '@/api/request'

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

function riskColor(level: number | string): string {
  const n = typeof level === 'string' ? parseInt(level.replace(/\D/g, '')) : (level || 0)
  if (n >= 3) return '#E74C3C'
  if (n >= 2) return '#E67E22'
  return '#27AE60'
}
function logColor(type: string): string {
  const m: Record<string, string> = { checkin: '#27AE60', mood: '#9B59B6', meal: '#E67E22', exercise: '#3498DB', medication: '#E74C3C' }
  return m[type] || '#5B6B7F'
}

async function loadData() {
  if (!studentId.value) return

  // 主数据来源：dashboard students 数组（含 risk_level/stage/health_data/micro_action_7d）
  try {
    const dash = await http<any>('/api/v1/coach/dashboard')
    const found = (dash.students || []).find((s: any) => (s.id || s.user_id) === studentId.value)
    if (found) {
      const ma = found.micro_action_7d || {}
      student.value = {
        ...found,
        name: found.name || found.full_name || found.username || '学员',
        // 解析 "R3" → 3
        risk_level: typeof found.risk_level === 'string'
          ? parseInt(found.risk_level.replace(/\D/g, '')) || 0
          : (found.risk_level || 0),
        micro_action_count: ma.completed ?? 0,
        micro_action_total: ma.total ?? 0,
        week_active_days: ma.completed != null ? Math.min(ma.completed, 7) : undefined,
        // 从 health_data 展开
        fasting_glucose: found.health_data?.fasting_glucose,
        weight: found.health_data?.weight,
        exercise_minutes: found.health_data?.exercise_minutes,
      }
    }
  } catch (e) { console.warn('[coach/students/detail] dashboard:', e) }

  // 补充：profile 端点有 height/weight/goals 等字段
  try {
    const res = await http<any>('/api/v1/coach/students/' + studentId.value)
    const profile = res?.profile || {}
    student.value = {
      ...student.value,
      name: student.value.name || res.full_name || res.username || '学员',
      height: profile.height || student.value.height,
      weight: profile.weight || student.value.weight,
      goals: profile.goals || [],
    }
  } catch (e) { console.warn('[coach/students/detail] api:', e) }

  // 行为记录
  try {
    const bRes = await http<any>('/api/v1/coach/behavior/' + studentId.value + '/recent?limit=20')
    behaviorLogs.value = (bRes.items || []).map((r: any) => ({
      type: r.behavior_type,
      type_label: r.type_label || r.behavior_type,
      content: r.description || r.note || '完成微行动',
      time: r.recorded_at ? r.recorded_at.slice(0, 10) : '',
    }))
  } catch { behaviorLogs.value = [] }

  // 督导记录
  try {
    const nRes = await http<any>('/api/v1/coach/students/' + studentId.value + '/notes')
    supervisionNotes.value = nRes.items || []
  } catch { supervisionNotes.value = [] }
}

async function submitNote() {
  if (!newNote.value.trim()) return
  try {
    await http('/api/v1/coach/students/' + studentId.value + '/notes', {
      method: 'POST',
      data: { content: newNote.value.trim() },
    })
    newNote.value = ''
    uni.showToast({ title: '已记录', icon: 'success' })
    // 重新拉取笔记列表
    const nRes = await http<any>('/api/v1/coach/students/' + studentId.value + '/notes')
    supervisionNotes.value = nRes.items || []
  } catch {
    uni.showToast({ title: '提交失败', icon: 'none' })
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
</style>