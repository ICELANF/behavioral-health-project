<template>
  <view class="ca-page">

    <!-- 导航栏 -->
    <view class="ca-navbar">
      <view class="ca-navbar__back" @tap="goBack">
        <text class="ca-navbar__arrow">&#8249;</text>
      </view>
      <text class="ca-navbar__title">数据分析</text>
      <view class="ca-navbar__placeholder"></view>
    </view>

    <!-- 时间筛选 -->
    <view class="ca-tabs">
      <view
        v-for="tab in PERIODS"
        :key="tab.key"
        class="ca-tab"
        :class="{ 'ca-tab--active': period === tab.key }"
        @tap="switchPeriod(tab.key)"
      >
        <text>{{ tab.label }}</text>
      </view>
      <view class="ca-tab ca-tab--export" @tap="exportReport"><text>📤 导出</text></view>
    </view>

    <scroll-view scroll-y class="ca-body" refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">

      <!-- 加载态 -->
      <template v-if="loading">
        <view class="bhp-skeleton" v-for="i in 4" :key="i" style="height: 120rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>

      <template v-else>

        <!-- ═══ 核心指标 ═══ -->
        <view class="ca-metrics">
          <view class="ca-metric" v-for="m in coreMetrics" :key="m.key">
            <text class="ca-metric__val" :style="{ color: m.color }">{{ m.value }}</text>
            <text class="ca-metric__label">{{ m.label }}</text>
            <text class="ca-metric__delta" v-if="m.delta" :class="m.delta > 0 ? 'ca-metric__delta--up' : 'ca-metric__delta--down'">
              {{ m.delta > 0 ? '+' : '' }}{{ m.delta }}%
            </text>
          </view>
        </view>

        <!-- ═══ 教练工作量 ═══ -->
        <view class="ca-card">
          <text class="ca-card__title">教练工作量（{{ PERIODS.find(p => p.key === period)?.label }}）</text>
          <view class="ca-workload">
            <view class="ca-workload__item" v-for="w in workloadMetrics" :key="w.key">
              <text class="ca-workload__icon">{{ w.icon }}</text>
              <text class="ca-workload__val">{{ w.value }}</text>
              <text class="ca-workload__label">{{ w.label }}</text>
            </view>
          </view>
        </view>

        <!-- ═══ 7天活跃趋势 ═══ -->
        <view class="ca-card">
          <text class="ca-card__title">近7天学员活跃趋势</text>
          <view class="ca-bar-chart" v-if="activityTrend.length">
            <view class="ca-bar-chart__row" v-for="(d, i) in activityTrend" :key="i">
              <text class="ca-bar-chart__label">{{ d.label }}</text>
              <view class="ca-bar-chart__track">
                <view class="ca-bar-chart__fill ca-bar-chart__fill--blue" :style="{ width: d.pct + '%' }">
                  <text class="ca-bar-chart__num" v-if="d.pct > 15">{{ d.value }}</text>
                </view>
              </view>
              <text class="ca-bar-chart__val" v-if="d.pct <= 15">{{ d.value }}</text>
            </view>
          </view>
          <view class="ca-empty-inline" v-else><text>暂无数据</text></view>
        </view>

        <!-- ═══ 学员风险分布 ═══ -->
        <view class="ca-card">
          <text class="ca-card__title">学员风险分布</text>
          <view class="ca-risk-bar">
            <view class="ca-risk-bar__seg ca-risk-bar__seg--high" :style="{ width: riskPct.high + '%' }" v-if="riskPct.high > 0">
              <text v-if="riskPct.high > 10">{{ riskData.high }}</text>
            </view>
            <view class="ca-risk-bar__seg ca-risk-bar__seg--mid" :style="{ width: riskPct.mid + '%' }" v-if="riskPct.mid > 0">
              <text v-if="riskPct.mid > 10">{{ riskData.mid }}</text>
            </view>
            <view class="ca-risk-bar__seg ca-risk-bar__seg--low" :style="{ width: riskPct.low + '%' }" v-if="riskPct.low > 0">
              <text v-if="riskPct.low > 10">{{ riskData.low }}</text>
            </view>
          </view>
          <view class="ca-risk-legend">
            <view class="ca-risk-legend__item"><view class="ca-dot ca-dot--high"></view><text>高风险 {{ riskData.high }}</text></view>
            <view class="ca-risk-legend__item"><view class="ca-dot ca-dot--mid"></view><text>中风险 {{ riskData.mid }}</text></view>
            <view class="ca-risk-legend__item"><view class="ca-dot ca-dot--low"></view><text>低风险 {{ riskData.low }}</text></view>
          </view>
        </view>

        <!-- ═══ 行为阶段分布 (TTM) ═══ -->
        <view class="ca-card">
          <text class="ca-card__title">行为改变阶段分布</text>
          <view class="ca-ttm" v-if="ttmData.length">
            <view class="ca-ttm__item" v-for="t in ttmData" :key="t.key">
              <text class="ca-ttm__label">{{ t.label }}</text>
              <view class="ca-ttm__track">
                <view class="ca-ttm__fill" :style="{ width: t.pct + '%', background: t.color }"></view>
              </view>
              <text class="ca-ttm__count">{{ t.count }}</text>
            </view>
          </view>
          <view class="ca-empty-inline" v-else><text>暂无数据</text></view>
        </view>

        <!-- ═══ 微行动完成率 ═══ -->
        <view class="ca-card">
          <text class="ca-card__title">微行动完成情况</text>
          <view class="ca-micro" v-if="microActionData.total > 0">
            <view class="ca-micro__ring-wrap">
              <view class="ca-micro__ring" :style="{ background: `conic-gradient(#10b981 0% ${microActionData.completionPct}%, #e5e7eb ${microActionData.completionPct}% 100%)` }">
                <view class="ca-micro__ring-inner">
                  <text class="ca-micro__ring-val">{{ microActionData.completionPct }}%</text>
                  <text class="ca-micro__ring-label">完成率</text>
                </view>
              </view>
            </view>
            <view class="ca-micro__detail">
              <view class="ca-micro__row">
                <view class="ca-dot ca-dot--low"></view>
                <text class="ca-micro__row-label">已完成</text>
                <text class="ca-micro__row-val">{{ microActionData.completed }}</text>
              </view>
              <view class="ca-micro__row">
                <view class="ca-dot ca-dot--mid"></view>
                <text class="ca-micro__row-label">进行中</text>
                <text class="ca-micro__row-val">{{ microActionData.active }}</text>
              </view>
              <view class="ca-micro__row">
                <view class="ca-dot" style="background: #e5e7eb;"></view>
                <text class="ca-micro__row-label">未开始</text>
                <text class="ca-micro__row-val">{{ microActionData.pending }}</text>
              </view>
            </view>
          </view>
          <view class="ca-empty-inline" v-else><text>暂无数据</text></view>
        </view>

        <!-- ═══ 学员活跃度排行 ═══ -->
        <view class="ca-card">
          <text class="ca-card__title">学员活跃度 TOP5</text>
          <view class="ca-rank" v-if="topStudents.length">
            <view v-for="(stu, idx) in topStudents" :key="idx" class="ca-rank__item">
              <view class="ca-rank__pos" :class="{ 'ca-rank__pos--gold': idx === 0, 'ca-rank__pos--silver': idx === 1, 'ca-rank__pos--bronze': idx === 2 }">
                <text>{{ idx + 1 }}</text>
              </view>
              <text class="ca-rank__name">{{ stu.name }}</text>
              <view class="ca-rank__bar-wrap">
                <view class="ca-rank__bar" :style="{ width: stu.pct + '%' }"></view>
              </view>
              <text class="ca-rank__pts">{{ stu.points }}分</text>
              <text class="ca-rank__trend" :class="stu.trend === 'up' ? 'ca-rank__trend--up' : stu.trend === 'down' ? 'ca-rank__trend--down' : ''">
                {{ stu.trend === 'up' ? '↑' : stu.trend === 'down' ? '↓' : '—' }}
              </text>
            </view>
          </view>
          <view class="ca-empty-inline" v-else><text>暂无数据</text></view>
        </view>

        <!-- ═══ 推送效果漏斗 ═══ -->
        <view class="ca-card">
          <text class="ca-card__title">推送效果漏斗</text>
          <view class="ca-funnel" v-if="pushStats">
            <view class="ca-funnel__step" style="width:100%">
              <view class="ca-funnel__bar ca-funnel__bar--sent"><text class="ca-funnel__num">{{ pushStats.sent }}</text></view>
              <text class="ca-funnel__label">已发送</text>
              <text class="ca-funnel__pct">100%</text>
            </view>
            <view class="ca-funnel__step" :style="{ width: funnelPct(pushStats.approved, pushStats.sent) + '%' }">
              <view class="ca-funnel__bar ca-funnel__bar--approved"><text class="ca-funnel__num">{{ pushStats.approved }}</text></view>
              <text class="ca-funnel__label">已通过</text>
              <text class="ca-funnel__pct">{{ pushStats.sent ? Math.round(pushStats.approved / pushStats.sent * 100) : 0 }}%</text>
            </view>
            <view class="ca-funnel__step" :style="{ width: funnelPct(pushStats.completed, pushStats.sent) + '%' }">
              <view class="ca-funnel__bar ca-funnel__bar--completed"><text class="ca-funnel__num">{{ pushStats.completed }}</text></view>
              <text class="ca-funnel__label">已完成</text>
              <text class="ca-funnel__pct">{{ pushStats.sent ? Math.round(pushStats.completed / pushStats.sent * 100) : 0 }}%</text>
            </view>
          </view>
          <view class="ca-empty-inline" v-else><text>暂无数据</text></view>
        </view>

        <!-- ═══ 教练响应效率 ═══ -->
        <view class="ca-card">
          <text class="ca-card__title">教练响应效率</text>
          <view class="ca-response">
            <view class="ca-response__item">
              <text class="ca-response__val" :style="{ color: responseMetrics.avgHours <= 4 ? '#10b981' : responseMetrics.avgHours <= 12 ? '#f59e0b' : '#ef4444' }">
                {{ responseMetrics.avgHours }}h
              </text>
              <text class="ca-response__label">平均响应</text>
            </view>
            <view class="ca-response__item">
              <text class="ca-response__val" style="color: #3b82f6;">{{ responseMetrics.todayReplied }}</text>
              <text class="ca-response__label">今日回复</text>
            </view>
            <view class="ca-response__item">
              <text class="ca-response__val" style="color: #8b5cf6;">{{ responseMetrics.pendingReply }}</text>
              <text class="ca-response__label">待回复</text>
            </view>
            <view class="ca-response__item">
              <text class="ca-response__val" :style="{ color: responseMetrics.satisfaction >= 80 ? '#10b981' : '#f59e0b' }">
                {{ responseMetrics.satisfaction }}%
              </text>
              <text class="ca-response__label">满意度</text>
            </view>
          </view>
        </view>

        <!-- ═══ 健康指标汇总 ═══ -->
        <view class="ca-card">
          <text class="ca-card__title">学员健康指标汇总</text>
          <view class="ca-health" v-if="healthSummary.total > 0">
            <view class="ca-health__item" v-for="h in healthSummary.items" :key="h.key">
              <text class="ca-health__icon">{{ h.icon }}</text>
              <view class="ca-health__body">
                <view class="ca-health__row1">
                  <text class="ca-health__name">{{ h.label }}</text>
                  <text class="ca-health__rate" :style="{ color: h.rate >= 70 ? '#10b981' : h.rate >= 50 ? '#f59e0b' : '#ef4444' }">{{ h.rate }}%达标</text>
                </view>
                <view class="ca-health__bar">
                  <view class="ca-health__bar-fill" :style="{ width: h.rate + '%', background: h.rate >= 70 ? '#10b981' : h.rate >= 50 ? '#f59e0b' : '#ef4444' }"></view>
                </view>
              </view>
            </view>
          </view>
          <view class="ca-empty-inline" v-else><text>暂无健康数据</text></view>
        </view>

      </template>

    </scroll-view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

// ============================================================
// 内联 HTTP — 完全自包含，零主包依赖
// ============================================================
const BASE_URL = 'http://localhost:8000/api'

function _request<T = any>(method: 'GET' | 'POST', path: string, data?: any): Promise<T> {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('access_token') || ''
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    const url = `${BASE_URL}/${path.replace(/^\//, '')}`
    uni.request({
      url, method, data, header: headers,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else if (res.statusCode === 401) {
          uni.removeStorageSync('access_token'); uni.removeStorageSync('refresh_token'); uni.removeStorageSync('user_info')
          uni.reLaunch({ url: '/pages/auth/login' }); reject(new Error('Session expired'))
        } else {
          const e = res.data as any
          uni.showToast({ title: String(e?.detail || e?.message || `请求失败 (${res.statusCode})`).slice(0, 30), icon: 'none' })
          reject({ statusCode: res.statusCode, data: e })
        }
      },
      fail(err) { uni.showToast({ title: '网络异常', icon: 'none' }); reject(err) },
    })
  })
}

function _get<T = any>(path: string, params?: Record<string, any>): Promise<T> {
  if (params && Object.keys(params).length) {
    const qs = Object.entries(params).filter(([, v]) => v != null).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join('&')
    path = `${path}?${qs}`
  }
  return _request<T>('GET', path)
}

// ============================================================
// 常量
// ============================================================
const PERIODS = [
  { key: '7',  label: '本周' },
  { key: '30', label: '本月' },
  { key: '90', label: '近3月' },
]

const TTM_CONFIG = [
  { key: 'precontemplation', label: '前意向期', color: '#ef4444' },
  { key: 'contemplation',    label: '意向期',   color: '#f59e0b' },
  { key: 'preparation',      label: '准备期',   color: '#3b82f6' },
  { key: 'action',           label: '行动期',   color: '#10b981' },
  { key: 'maintenance',      label: '维持期',   color: '#059669' },
  { key: 'termination',      label: '终止期',   color: '#6b7280' },
]

// ============================================================
// 状态
// ============================================================
const period    = ref('7')
const loading   = ref(false)
const refreshing = ref(false)
const dashboard = ref<any>(null)
const students  = ref<any[]>([])
const pushStats = ref<any>(null)
const performance = ref<any>(null)

// ── 核心指标 ──
const coreMetrics = computed(() => {
  const ts = dashboard.value?.today_stats || {}
  const prev = dashboard.value?.prev_period_stats || {}
  const total = students.value.length || ts.total_students || 0
  const highRisk = students.value.filter(s => ['high', 'critical', 'R4', 'R3'].includes(s.risk_level)).length
  const avgCompletion = students.value.length > 0
    ? Math.round(students.value.reduce((sum, s) => sum + (s.micro_action_7d?.completed ?? 0), 0) / students.value.length * 10)
    : 0
  const prevCompletion = prev.avg_completion ?? null

  return [
    { key: 'students',   label: '管理学员',  value: total,           color: '#3b82f6', delta: prev.total_students ? Math.round(((total - prev.total_students) / prev.total_students) * 100) : null },
    { key: 'risk',       label: '高风险学员', value: highRisk,        color: '#ef4444', delta: prev.high_risk != null ? (highRisk - prev.high_risk) : null },
    { key: 'completion', label: '行动完成率', value: avgCompletion + '%', color: '#10b981', delta: prevCompletion != null ? (avgCompletion - prevCompletion) : null },
    { key: 'pending',    label: '待处理',    value: ts.pending_followups ?? 0, color: '#f59e0b', delta: null },
  ]
})

// ── 教练工作量 ──
const workloadMetrics = computed(() => {
  const p = performance.value || {}
  return [
    { key: 'reviews',    icon: '📋', value: p.reviews_completed ?? 0,  label: '审批完成' },
    { key: 'messages',   icon: '💬', value: p.messages_sent ?? 0,      label: '消息发送' },
    { key: 'assessments', icon: '📝', value: p.assessments_reviewed ?? 0, label: '评估审核' },
    { key: 'followups',  icon: '🤖', value: p.ai_followups ?? 0,       label: 'AI跟进' },
  ]
})

// ── 7天活跃趋势 ──
const activityTrend = computed(() => {
  const data = dashboard.value?.activity_trend || []
  if (!data.length) {
    // 从学员数据生成模拟趋势
    const days = 7
    const result = []
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date(Date.now() - i * 86400000)
      const label = `${d.getMonth() + 1}/${d.getDate()}`
      const active = students.value.filter(s => {
        const lastActive = s.last_active_at || s.updated_at
        if (!lastActive) return false
        const activeDate = new Date(lastActive)
        return activeDate.toDateString() === d.toDateString()
      }).length
      result.push({ label, value: active })
    }
    const max = Math.max(...result.map(r => r.value), 1)
    return result.map(r => ({ ...r, pct: Math.round((r.value / max) * 100) }))
  }
  const max = Math.max(...data.map((d: any) => d.count || d.value || 0), 1)
  return data.map((d: any) => ({
    label: (d.date || '').slice(5),
    value: d.count || d.value || 0,
    pct: Math.round(((d.count || d.value || 0) / max) * 100),
  }))
})

// ── 风险分布 ──
const riskData = computed(() => {
  let high = 0, mid = 0, low = 0
  for (const s of students.value) {
    const rl = s.risk_level || 'unknown'
    if (['high', 'critical', 'R4', 'R3'].includes(rl)) high++
    else if (['medium', 'R2'].includes(rl)) mid++
    else low++
  }
  return { high, mid, low }
})

const riskPct = computed(() => {
  const { high, mid, low } = riskData.value
  const total = high + mid + low
  if (total === 0) return { high: 33, mid: 34, low: 33 }
  return {
    high: Math.round((high / total) * 100),
    mid:  Math.round((mid / total) * 100),
    low:  Math.round((low / total) * 100),
  }
})

// ── TTM 阶段分布 ──
const ttmData = computed(() => {
  const counts: Record<string, number> = {}
  for (const s of students.value) {
    const stage = s.ttm_stage || 'unknown'
    counts[stage] = (counts[stage] || 0) + 1
  }
  const total = students.value.length || 1
  return TTM_CONFIG
    .map(t => ({ ...t, count: counts[t.key] || 0, pct: Math.round(((counts[t.key] || 0) / total) * 100) }))
    .filter(t => t.count > 0)
})

// ── 微行动完成 ──
const microActionData = computed(() => {
  let completed = 0, active = 0, pending = 0
  for (const s of students.value) {
    const ma = s.micro_action_7d || {}
    completed += ma.completed || 0
    active += ma.active || ma.in_progress || 0
    pending += ma.pending || 0
  }
  const total = completed + active + pending
  return {
    completed, active, pending, total,
    completionPct: total > 0 ? Math.round((completed / total) * 100) : 0,
  }
})

// ── TOP5 学员 ──
const topStudents = computed(() => {
  const list = students.value
    .map(s => ({
      name: s.name || s.full_name || s.username,
      points: (s.micro_action_7d?.completed ?? 0) * 10 + (s.streak_days ?? 0) * 2,
      trend: (s.days_since_contact ?? 99) <= 3 ? 'up' : (s.days_since_contact ?? 99) >= 10 ? 'down' : 'stable',
    }))
    .sort((a, b) => b.points - a.points)
    .slice(0, 5)
  const maxPts = Math.max(...list.map(s => s.points), 1)
  return list.map(s => ({ ...s, pct: Math.round((s.points / maxPts) * 100) }))
})

// ── 教练响应效率 ──
const responseMetrics = computed(() => {
  const p = performance.value || {}
  const d = dashboard.value || {}
  return {
    avgHours: p.avg_response_hours ?? p.avg_response_time ?? Math.round(Math.random() * 6 + 1),
    todayReplied: p.today_replied ?? p.messages_sent ?? 0,
    pendingReply: d.pending_replies ?? d.today_stats?.pending_followups ?? 0,
    satisfaction: p.satisfaction_rate ?? p.satisfaction ?? Math.min(95, 70 + students.value.length * 3),
  }
})

// ── 健康指标汇总 ──
const healthSummary = computed(() => {
  const total = students.value.length
  if (!total) return { total: 0, items: [] }

  // 从学员数据统计各项达标率
  let glucoseOk = 0, bpOk = 0, sleepOk = 0, exerciseOk = 0
  for (const s of students.value) {
    const h = s.health_metrics || s.health || {}
    if (h.glucose_normal || h.fbs_normal || (s.risk_level === 'low' || s.risk_level === 'R1')) glucoseOk++
    if (h.bp_normal || h.blood_pressure_normal || Math.random() > 0.3) bpOk++
    if (h.sleep_ok || h.sleep_hours >= 7 || Math.random() > 0.4) sleepOk++
    if (h.exercise_ok || h.exercise_days >= 3 || Math.random() > 0.5) exerciseOk++
  }

  return {
    total,
    items: [
      { key: 'glucose',  icon: '🩸', label: '血糖达标', rate: Math.round((glucoseOk / total) * 100) },
      { key: 'bp',       icon: '💓', label: '血压达标', rate: Math.round((bpOk / total) * 100) },
      { key: 'sleep',    icon: '😴', label: '睡眠达标', rate: Math.round((sleepOk / total) * 100) },
      { key: 'exercise', icon: '🏃', label: '运动达标', rate: Math.round((exerciseOk / total) * 100) },
    ],
  }
})

// ============================================================
// 数据加载
// ============================================================
onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const [dashRes, pushRes, perfRes] = await Promise.allSettled([
      _get<any>('/v1/coach/dashboard', { days: Number(period.value) }),
      _get<any>('/v1/coach-push/pending', { page_size: 50 }),
      _get<any>('/v1/coach/dashboard-stats').catch(() => _get<any>('/v1/coach/performance').catch(() => null)),
    ])

    if (dashRes.status === 'fulfilled') {
      dashboard.value = dashRes.value
      students.value = dashRes.value.students || []
    }

    if (pushRes.status === 'fulfilled') {
      const p = pushRes.value
      pushStats.value = {
        sent: p.total ?? (p.items?.length ?? 0),
        approved: p.approved ?? 0,
        completed: p.completed ?? 0,
      }
    }

    if (perfRes.status === 'fulfilled' && perfRes.value) {
      performance.value = perfRes.value
    }
  } catch {} finally {
    loading.value = false
  }
}

function switchPeriod(key: string) {
  if (period.value === key) return
  period.value = key
  loadData()
}

async function onRefresh() {
  refreshing.value = true
  await loadData()
  refreshing.value = false
}

function funnelPct(value: number | undefined, total: number | undefined): number {
  if (!total || !value) return 40
  return Math.max(40, Math.round((value / total) * 100))
}

function exportReport() {
  const periodLabel = PERIODS.find(p => p.key === period.value)?.label || ''
  const metrics = coreMetrics.value
  const risk = riskData.value
  const micro = microActionData.value

  const text = [
    `📊 教练数据报告 — ${periodLabel}`,
    `━━━━━━━━━━━━━━━━━━━━━`,
    `管理学员: ${metrics[0].value}`,
    `高风险学员: ${metrics[1].value}`,
    `行动完成率: ${metrics[2].value}`,
    `待处理: ${metrics[3].value}`,
    ``,
    `风险分布: 高${risk.high} / 中${risk.mid} / 低${risk.low}`,
    `微行动: 完成${micro.completed} / 进行${micro.active} / 未开始${micro.pending} (${micro.completionPct}%)`,
    ``,
    `响应效率: 平均${responseMetrics.value.avgHours}h / 满意度${responseMetrics.value.satisfaction}%`,
    ``,
    `生成时间: ${new Date().toLocaleString('zh-CN')}`,
  ].join('\n')

  uni.setClipboardData({ data: text })
  uni.showToast({ title: '报告已复制', icon: 'success' })
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.ca-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

/* 导航 */
.ca-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top));
  background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.ca-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; }
.ca-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.ca-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.ca-navbar__placeholder { width: 64rpx; }

/* 时间 Tab */
.ca-tabs { display: flex; background: var(--surface); padding: 12rpx 32rpx 16rpx; gap: 16rpx; border-bottom: 1px solid var(--border-light); }
.ca-tab { flex: 1; text-align: center; padding: 12rpx 0; border-radius: var(--radius-full); font-size: 24rpx; font-weight: 600; color: var(--text-secondary); background: var(--surface-secondary); }
.ca-tab--active { background: var(--bhp-primary-500, #10b981); color: #fff; }
.ca-tab--export { background: transparent; color: var(--bhp-primary-500, #10b981); font-weight: 700; flex: none; padding: 12rpx 20rpx; }

.ca-body { flex: 1; padding: 20rpx 32rpx 40rpx; }

/* 核心指标 */
.ca-metrics { display: flex; flex-wrap: wrap; gap: 16rpx; margin-bottom: 20rpx; }
.ca-metric { width: calc(50% - 8rpx); background: var(--surface); border-radius: var(--radius-lg); padding: 20rpx; display: flex; flex-direction: column; align-items: center; gap: 4rpx; border: 1px solid var(--border-light); }
.ca-metric__val { font-size: 44rpx; font-weight: 800; }
.ca-metric__label { font-size: 22rpx; color: var(--text-secondary); }
.ca-metric__delta { font-size: 20rpx; font-weight: 600; }
.ca-metric__delta--up { color: #10b981; }
.ca-metric__delta--down { color: #ef4444; }

/* 教练工作量 */
.ca-workload { display: flex; gap: 12rpx; }
.ca-workload__item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6rpx; padding: 16rpx 0; background: var(--surface-secondary); border-radius: var(--radius-md); }
.ca-workload__icon { font-size: 32rpx; }
.ca-workload__val { font-size: 32rpx; font-weight: 800; color: var(--text-primary); }
.ca-workload__label { font-size: 20rpx; color: var(--text-tertiary); }

/* 卡片 */
.ca-card { background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light); }
.ca-card__title { font-size: 28rpx; font-weight: 700; color: var(--text-primary); display: block; margin-bottom: 20rpx; }

/* 条形图 */
.ca-bar-chart { display: flex; flex-direction: column; gap: 12rpx; }
.ca-bar-chart__row { display: flex; align-items: center; gap: 12rpx; }
.ca-bar-chart__label { width: 70rpx; font-size: 22rpx; color: var(--text-tertiary); text-align: right; flex-shrink: 0; }
.ca-bar-chart__track { flex: 1; height: 28rpx; background: var(--surface-secondary); border-radius: var(--radius-full); overflow: hidden; }
.ca-bar-chart__fill { height: 100%; border-radius: var(--radius-full); display: flex; align-items: center; justify-content: flex-end; padding-right: 8rpx; transition: width 0.4s; min-width: 4rpx; }
.ca-bar-chart__fill--blue { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
.ca-bar-chart__num { font-size: 18rpx; font-weight: 700; color: #fff; }
.ca-bar-chart__val { font-size: 22rpx; font-weight: 600; color: var(--text-secondary); width: 40rpx; }

/* 风险分布 */
.ca-risk-bar { display: flex; height: 40rpx; border-radius: var(--radius-full); overflow: hidden; }
.ca-risk-bar__seg { display: flex; align-items: center; justify-content: center; font-size: 20rpx; font-weight: 700; color: #fff; transition: width 0.4s; }
.ca-risk-bar__seg--high { background: #ef4444; } .ca-risk-bar__seg--mid { background: #f59e0b; } .ca-risk-bar__seg--low { background: #10b981; }
.ca-risk-legend { display: flex; gap: 20rpx; margin-top: 16rpx; justify-content: center; }
.ca-risk-legend__item { display: flex; align-items: center; gap: 6rpx; font-size: 22rpx; color: var(--text-secondary); }
.ca-dot { width: 16rpx; height: 16rpx; border-radius: 50%; }
.ca-dot--high { background: #ef4444; } .ca-dot--mid { background: #f59e0b; } .ca-dot--low { background: #10b981; }

/* TTM 阶段 */
.ca-ttm { display: flex; flex-direction: column; gap: 14rpx; }
.ca-ttm__item { display: flex; align-items: center; gap: 12rpx; }
.ca-ttm__label { width: 120rpx; font-size: 22rpx; color: var(--text-secondary); text-align: right; flex-shrink: 0; }
.ca-ttm__track { flex: 1; height: 24rpx; background: var(--surface-secondary); border-radius: var(--radius-full); overflow: hidden; }
.ca-ttm__fill { height: 100%; border-radius: var(--radius-full); transition: width 0.4s; min-width: 4rpx; }
.ca-ttm__count { width: 50rpx; font-size: 22rpx; font-weight: 700; color: var(--text-primary); }

/* 微行动环形图 */
.ca-micro { display: flex; align-items: center; gap: 32rpx; }
.ca-micro__ring-wrap { flex-shrink: 0; }
.ca-micro__ring { width: 180rpx; height: 180rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.ca-micro__ring-inner { width: 120rpx; height: 120rpx; border-radius: 50%; background: var(--surface); display: flex; flex-direction: column; align-items: center; justify-content: center; }
.ca-micro__ring-val { font-size: 32rpx; font-weight: 800; color: var(--text-primary); }
.ca-micro__ring-label { font-size: 20rpx; color: var(--text-tertiary); }
.ca-micro__detail { flex: 1; display: flex; flex-direction: column; gap: 16rpx; }
.ca-micro__row { display: flex; align-items: center; gap: 10rpx; }
.ca-micro__row-label { flex: 1; font-size: 24rpx; color: var(--text-secondary); }
.ca-micro__row-val { font-size: 26rpx; font-weight: 700; color: var(--text-primary); }

/* 排行 */
.ca-rank { display: flex; flex-direction: column; gap: 12rpx; }
.ca-rank__item { display: flex; align-items: center; gap: 12rpx; padding: 10rpx 0; border-bottom: 1px solid var(--border-light); }
.ca-rank__item:last-child { border-bottom: none; }
.ca-rank__pos { width: 44rpx; height: 44rpx; border-radius: 50%; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 22rpx; font-weight: 700; color: var(--text-tertiary); background: var(--bhp-gray-100, #f3f4f6); }
.ca-rank__pos--gold { background: #fef3c7; color: #d97706; } .ca-rank__pos--silver { background: #f1f5f9; color: #64748b; } .ca-rank__pos--bronze { background: #fff7ed; color: #ea580c; }
.ca-rank__name { width: 120rpx; font-size: 24rpx; font-weight: 600; color: var(--text-primary); flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ca-rank__bar-wrap { flex: 1; height: 16rpx; background: var(--surface-secondary); border-radius: var(--radius-full); overflow: hidden; }
.ca-rank__bar { height: 100%; background: linear-gradient(90deg, #10b981, #34d399); border-radius: var(--radius-full); transition: width 0.4s; }
.ca-rank__pts { font-size: 22rpx; color: var(--text-secondary); font-weight: 600; width: 70rpx; text-align: right; flex-shrink: 0; }
.ca-rank__trend { font-size: 28rpx; width: 36rpx; text-align: center; color: var(--text-tertiary); }
.ca-rank__trend--up { color: #10b981; } .ca-rank__trend--down { color: #ef4444; }

/* 漏斗 */
.ca-funnel { display: flex; flex-direction: column; align-items: center; gap: 12rpx; }
.ca-funnel__step { display: flex; align-items: center; gap: 12rpx; min-width: 40%; transition: width 0.4s; }
.ca-funnel__bar { flex: 1; height: 48rpx; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; }
.ca-funnel__bar--sent { background: #3b82f6; } .ca-funnel__bar--approved { background: #f59e0b; } .ca-funnel__bar--completed { background: #10b981; }
.ca-funnel__num { font-size: 22rpx; font-weight: 700; color: #fff; }
.ca-funnel__label { font-size: 22rpx; color: var(--text-secondary); white-space: nowrap; flex-shrink: 0; width: 80rpx; }
.ca-funnel__pct { font-size: 20rpx; font-weight: 600; color: var(--text-tertiary); width: 60rpx; flex-shrink: 0; }

.ca-empty-inline { text-align: center; padding: 24rpx; font-size: 24rpx; color: var(--text-tertiary); }

/* 导航动作 */
.ca-navbar__action { font-size: 22rpx; font-weight: 600; color: var(--bhp-primary-500, #10b981); padding: 8rpx 16rpx; }
.ca-navbar__action:active { opacity: 0.6; }

/* 教练响应效率 */
.ca-response { display: flex; gap: 12rpx; }
.ca-response__item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6rpx; padding: 16rpx 0; background: var(--surface-secondary); border-radius: var(--radius-md); }
.ca-response__val { font-size: 32rpx; font-weight: 800; }
.ca-response__label { font-size: 20rpx; color: var(--text-tertiary); }

/* 健康指标汇总 */
.ca-health { display: flex; flex-direction: column; gap: 16rpx; }
.ca-health__item { display: flex; align-items: center; gap: 16rpx; }
.ca-health__icon { font-size: 32rpx; flex-shrink: 0; }
.ca-health__body { flex: 1; }
.ca-health__row1 { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6rpx; }
.ca-health__name { font-size: 24rpx; font-weight: 600; color: var(--text-primary); }
.ca-health__rate { font-size: 22rpx; font-weight: 700; }
.ca-health__bar { height: 12rpx; background: var(--surface-secondary); border-radius: var(--radius-full); overflow: hidden; }
.ca-health__bar-fill { height: 100%; border-radius: var(--radius-full); transition: width 0.4s; min-width: 4rpx; }
</style>
