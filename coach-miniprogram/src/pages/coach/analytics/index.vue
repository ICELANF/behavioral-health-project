<template>
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
        <view class="ana-metric" v-for="m in coreMetrics" :key="m.label"
          @tap="m.url && navigate(m.url)">
          <text class="ana-metric-val" :style="{ color: m.color }">{{ m.value }}</text>
          <text class="ana-metric-label">{{ m.url ? m.label + ' ›' : m.label }}</text>
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
          <view class="ana-ring" :style="{ background: `conic-gradient(#27AE60 ${actionRate * 3.6}deg, #E8E8E8 0deg)` }">
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
import { httpReq as http } from '@/api/request'

function navigate(url: string) { uni.navigateTo({ url }) }

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
    { label: '管理学员', value: students.value.length, color: '#3498DB', url: '/pages/coach/students/index' },
    { label: '高风险', value: students.value.filter(s => (s.risk_level || 0) >= 3).length, color: '#E74C3C', url: '/pages/coach/risk/index' },
    { label: '行动完成率', value: actionRate.value + '%', color: '#27AE60', url: '' },
    { label: '待处理', value: stats.pending_reviews || stats.pending_followups || 0, color: '#E67E22', url: '/pages/coach/assessment/index' },
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

const weeklyTrend = ref<{date:string;label:string;count:number}[]>([])
const activityTrend = computed(() => {
  const todayDow = (new Date().getDay() + 6) % 7  // 0=Mon
  const source = weeklyTrend.value.length === 7 ? weeklyTrend.value
    : ['一','二','三','四','五','六','日'].map(l => ({ date: '', label: l, count: 0 }))
  const maxCnt = Math.max(...source.map(d => d.count), 1)
  return source.map((d, i) => ({
    label: d.label,
    height: Math.round((d.count / maxCnt) * 160) + 20,
    color: i === todayDow ? '#3498DB' : '#D5E8D4',
  }))
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
    const count = students.value.filter(s =>
      s.ttm_stage === stage || s.stage === stage || s.stage_label === stage
    ).length
    return { stage, count, percent: Math.round(count / total * 100), color: colors[i] }
  })
})

const actionCompleted = ref(0)
const actionTotal = ref(0)
const actionRate = computed(() => actionTotal.value > 0 ? Math.round(actionCompleted.value / actionTotal.value * 100) : 0)

const funnelRaw = ref({ sent: 0, approved: 0, completed: 0 })
const funnelData = computed(() => {
  const { sent, approved, completed } = funnelRaw.value
  const base = sent || 1
  return [
    { label: '已发送', value: sent, percent: 100, color: '#3498DB' },
    { label: '已通过', value: approved, percent: Math.round(approved / base * 100), color: '#27AE60' },
    { label: '已完成', value: completed, percent: Math.round(completed / base * 100), color: '#2ECC71' },
  ]
})

const activityRanking = computed(() => {
  const maxScore = Math.max(...students.value.map(s => s.activity_score || s.micro_action_count || 10), 1)
  return students.value
    .map(s => ({
      name: s.name || s.full_name || '未知',
      score: s.activity_score || s.micro_action_7d?.completed || s.micro_action_count || 0,
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
    students.value = (Array.isArray(raw) ? raw : []).map((s: any) => ({
      ...s,
      risk_level: typeof s.risk_level === 'string'
        ? parseInt(s.risk_level.replace(/\D/g, '')) || 0
        : (s.risk_level ?? 0),
    }))
  } catch { students.value = [] }
  try {
    const res2 = await http<any>('/api/v1/micro-actions/today')
    actionTotal.value = res2.total || 0
    actionCompleted.value = res2.completed || 0
  } catch (e) { console.warn('[coach/analytics/index] today:', e) }
  try {
    const trend = await http<any>('/api/v1/coach/analytics/weekly-trend')
    if (Array.isArray(trend?.trend)) weeklyTrend.value = trend.trend
  } catch { /* silent */ }
  try {
    const funnel = await http<any>('/api/v1/coach/analytics/push-funnel')
    if (funnel) funnelRaw.value = { sent: funnel.sent || 0, approved: funnel.approved || 0, completed: funnel.completed || 0 }
  } catch { /* silent */ }
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
</style>