<template>
  <view class="sd-page">

    <!-- 导航栏 -->
    <view class="sd-navbar">
      <view class="sd-navbar__back" @tap="goBack"><text class="sd-navbar__arrow">&#8249;</text></view>
      <text class="sd-navbar__title">学员详情</text>
      <view class="sd-navbar__placeholder"></view>
    </view>

    <!-- 顶部学员信息 -->
    <view class="sd-header">
      <image class="sd-header__avatar" :src="student?.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
      <view class="sd-header__info">
        <view class="sd-header__name-row">
          <text class="sd-header__name">{{ student?.full_name || student?.username || '' }}</text>
          <view class="sd-risk-tag" :class="`sd-risk-tag--${normalizeRisk(student?.risk_level)}`">
            <text>{{ RISK_LABEL[student?.risk_level] || '未评估' }}</text>
          </view>
        </view>
        <view class="sd-header__tags">
          <view class="sd-header__tag" v-if="student?.ttm_stage">
            <text>{{ TTM_LABEL[student.ttm_stage] || student.ttm_stage }}</text>
          </view>
          <text class="sd-header__contact" v-if="student?.days_since_contact != null">
            {{ student.days_since_contact <= 0 ? '今日已联系' : student.days_since_contact + '天未联系' }}
          </text>
        </view>
      </view>
    </view>

    <!-- Tab 栏 -->
    <view class="sd-tabs">
      <view
        v-for="tab in TABS"
        :key="tab.key"
        class="sd-tab"
        :class="{ 'sd-tab--active': activeTab === tab.key }"
        @tap="activeTab = tab.key"
      >
        <text>{{ tab.label }}</text>
      </view>
    </view>

    <!-- Tab 内容 -->
    <scroll-view scroll-y class="sd-content">

      <!-- ═══ 画像 Tab ═══ -->
      <view v-if="activeTab === 'profile'" class="sd-tab-body">
        <view class="sd-card">
          <text class="sd-card__title">🧠 大五人格</text>
          <view class="sd-bars">
            <view v-for="dim in BIG5" :key="dim.key" class="sd-bar-row">
              <text class="sd-bar-row__label">{{ dim.label }}</text>
              <view class="sd-bar-row__track">
                <view class="sd-bar-row__fill" :style="{ width: (student?.big5?.[dim.key] || 0) + '%', background: dim.color }"></view>
              </view>
              <text class="sd-bar-row__val">{{ student?.big5?.[dim.key] || 0 }}</text>
            </view>
          </view>
        </view>

        <view class="sd-card" v-if="student?.bpt6_tags?.length">
          <text class="sd-card__title">🏷 BPT6 行为类型</text>
          <view class="sd-tags">
            <view class="sd-tag" v-for="tag in student.bpt6_tags.slice(0, 6)" :key="tag"><text>{{ tag }}</text></view>
          </view>
        </view>

        <view class="sd-card" v-if="student?.behavior_stage_desc">
          <text class="sd-card__title">🔄 行为改变阶段</text>
          <text class="sd-card__desc">{{ student.behavior_stage_desc }}</text>
        </view>
      </view>

      <!-- ═══ 风险 Tab ═══ -->
      <view v-if="activeTab === 'risk'" class="sd-tab-body">
        <!-- 风险概览 -->
        <view class="sd-card">
          <text class="sd-card__title">⚠ 当前风险状态</text>
          <view class="sd-risk-overview">
            <view class="sd-risk-overview__level">
              <view class="sd-risk-circle" :class="`sd-risk-circle--${normalizeRisk(student?.risk_level)}`">
                <text>{{ RISK_LABEL[student?.risk_level] || '未评估' }}</text>
              </view>
            </view>
            <view class="sd-risk-overview__factors" v-if="student?.risk_factors?.length">
              <text class="sd-risk-overview__subtitle">风险因素</text>
              <view class="sd-risk-factor" v-for="(f, i) in student.risk_factors" :key="i">
                <text class="sd-risk-factor__dot">•</text>
                <text class="sd-risk-factor__text">{{ f }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 风险变化时间线 -->
        <view class="sd-card">
          <text class="sd-card__title">📈 风险变化记录</text>
          <view class="sd-timeline" v-if="riskHistory.length">
            <view v-for="(h, i) in riskHistory" :key="i" class="sd-timeline__item">
              <view class="sd-timeline__dot" :class="`sd-timeline__dot--${normalizeRisk(h.risk_level)}`"></view>
              <view class="sd-timeline__line" v-if="i < riskHistory.length - 1"></view>
              <view class="sd-timeline__body">
                <view class="sd-timeline__row">
                  <view class="sd-risk-tag-sm" :class="`sd-risk-tag--${normalizeRisk(h.risk_level)}`">
                    <text>{{ RISK_LABEL[h.risk_level] || h.risk_level }}</text>
                  </view>
                  <text class="sd-timeline__date">{{ formatDate(h.created_at) }}</text>
                </view>
                <text class="sd-timeline__reason" v-if="h.reason">{{ h.reason }}</text>
              </view>
            </view>
          </view>
          <view v-else class="sd-empty"><text>暂无风险变化记录</text></view>
        </view>

        <!-- 干预记录 -->
        <view class="sd-card">
          <view class="sd-card__header-row">
            <text class="sd-card__title" style="margin-bottom:0">📋 干预记录</text>
            <view class="sd-add-btn" @tap="showInterventionModal = true"><text>+ 添加</text></view>
          </view>
          <view class="sd-interventions" v-if="interventions.length">
            <view v-for="iv in interventions" :key="iv.id" class="sd-intervention">
              <view class="sd-intervention__header">
                <view class="sd-intervention__type-tag" :class="`sd-intervention__type--${iv.type}`">
                  <text>{{ INTERVENTION_LABEL[iv.type] || iv.type }}</text>
                </view>
                <text class="sd-intervention__date">{{ formatDate(iv.created_at) }}</text>
              </view>
              <text class="sd-intervention__content">{{ iv.content }}</text>
              <text class="sd-intervention__result" v-if="iv.result">结果：{{ iv.result }}</text>
            </view>
          </view>
          <view v-else class="sd-empty"><text>暂无干预记录</text></view>
        </view>
      </view>

      <!-- ═══ 评估 Tab ═══ -->
      <view v-if="activeTab === 'assessment'" class="sd-tab-body">
        <view class="sd-card">
          <view class="sd-card__header-row">
            <text class="sd-card__title" style="margin-bottom:0">评估记录</text>
            <view class="sd-add-btn" @tap="assignAssessment"><text>+ 分配新评估</text></view>
          </view>
          <view v-if="assessments.length" class="sd-list">
            <view v-for="a in assessments" :key="a.id" class="sd-list-item" :class="{ 'sd-list-item--highlight': a.status === 'pending_review' }" @tap="goAssessmentReview(a)">
              <view class="sd-list-item__body">
                <text class="sd-list-item__title">{{ a.scale_name || a.title || '综合评估' }}</text>
                <text class="sd-list-item__sub">{{ a.created_at?.slice(0, 10) }}</text>
              </view>
              <view class="sd-status" :class="`sd-status--${a.status}`">
                <text>{{ ASSESS_STATUS[a.status] || a.status }}</text>
              </view>
            </view>
          </view>
          <view v-else class="sd-empty"><text>暂无评估记录</text></view>
        </view>
      </view>

      <!-- ═══ 处方 Tab ═══ -->
      <view v-if="activeTab === 'prescription'" class="sd-tab-body">
        <view class="sd-card">
          <text class="sd-card__title">行为处方</text>
          <view v-if="prescriptions.length" class="sd-list">
            <view v-for="p in prescriptions" :key="p.id" class="sd-list-item">
              <view class="sd-list-item__body">
                <text class="sd-list-item__title">{{ p.content_title || p.summary }}</text>
                <text class="sd-list-item__sub">{{ p.ai_summary || '' }}</text>
              </view>
              <view class="sd-list-item__right">
                <view class="sd-status" :class="`sd-status--${p.status}`">
                  <text>{{ RX_STATUS[p.status] || p.status }}</text>
                </view>
                <view class="sd-rx-actions" v-if="p.status === 'pending'">
                  <view class="sd-rx-btn sd-rx-btn--approve" @tap.stop="approveRx(p)"><text>通过</text></view>
                  <view class="sd-rx-btn sd-rx-btn--reject" @tap.stop="rejectRx(p)"><text>拒绝</text></view>
                </view>
              </view>
            </view>
          </view>
          <view v-else class="sd-empty"><text>暂无行为处方</text></view>
        </view>
      </view>

      <!-- ═══ 健康数据 Tab ═══ -->
      <view v-if="activeTab === 'health'" class="sd-tab-body">
        <view class="sd-card">
          <text class="sd-card__title">📊 近7天血糖趋势</text>
          <view class="sd-glucose-chart" v-if="glucoseData.length">
            <view class="sd-glucose-row" v-for="(g, i) in glucoseData" :key="i">
              <text class="sd-glucose-date">{{ g.date?.slice(5) }}</text>
              <view class="sd-glucose-bar-wrap">
                <view class="sd-glucose-bar" :class="{ 'sd-glucose-bar--high': g.value > 10, 'sd-glucose-bar--normal': g.value >= 4 && g.value <= 10, 'sd-glucose-bar--low': g.value < 4 }" :style="{ width: Math.min((g.value / 16) * 100, 100) + '%' }"></view>
              </view>
              <text class="sd-glucose-val">{{ g.value }} mmol/L</text>
            </view>
          </view>
          <view v-else class="sd-empty"><text>暂无血糖数据</text></view>
        </view>
        <view class="sd-health-grid">
          <view class="sd-health-card" v-for="hm in healthCards" :key="hm.key">
            <text class="sd-health-card__icon">{{ hm.icon }}</text>
            <text class="sd-health-card__val">{{ healthMetrics[hm.key] ?? '--' }}{{ hm.unit }}</text>
            <text class="sd-health-card__label">{{ hm.label }}</text>
          </view>
        </view>
      </view>

      <!-- ═══ 消息 Tab ═══ -->
      <view v-if="activeTab === 'message'" class="sd-tab-body sd-msg-body">
        <view class="sd-msg-list" v-if="messages.length">
          <view v-for="msg in messages" :key="msg.id" class="sd-msg-item" :class="`sd-msg-item--${msg.direction}`">
            <view class="sd-msg-bubble" :class="`sd-msg-bubble--${msg.direction}`">
              <text>{{ msg.content }}</text>
            </view>
            <text class="sd-msg-time">{{ msg.created_at?.slice(11, 16) }}</text>
          </view>
        </view>
        <view v-else class="sd-empty" style="padding-top:60rpx;"><text>暂无消息记录</text></view>
      </view>

    </scroll-view>

    <!-- 消息输入栏 -->
    <view class="sd-msg-input" v-if="activeTab === 'message'">
      <view class="sd-msg-input__ai" @tap="getAiSuggestion"><text>🤖 AI</text></view>
      <input class="sd-msg-input__field" v-model="msgInput" placeholder="输入消息..." confirm-type="send" @confirm="sendMsg" />
      <view class="sd-msg-input__send" :class="{ 'sd-msg-input__send--active': msgInput.trim() }" @tap="sendMsg"><text>发送</text></view>
    </view>

    <!-- 干预记录弹窗 -->
    <view class="sd-modal-mask" v-if="showInterventionModal" @tap="showInterventionModal = false">
      <view class="sd-modal" @tap.stop>
        <text class="sd-modal__title">添加干预记录</text>
        <view class="sd-modal__field">
          <text class="sd-modal__label">干预类型</text>
          <view class="sd-modal__type-list">
            <view v-for="t in INTERVENTION_TYPES" :key="t.key" class="sd-modal__type" :class="{ 'sd-modal__type--active': newIntervention.type === t.key }" @tap="newIntervention.type = t.key">
              <text>{{ t.icon }} {{ t.label }}</text>
            </view>
          </view>
        </view>
        <view class="sd-modal__field">
          <text class="sd-modal__label">干预内容</text>
          <textarea class="sd-modal__textarea" v-model="newIntervention.content" placeholder="描述干预措施..." :maxlength="500" />
        </view>
        <view class="sd-modal__field">
          <text class="sd-modal__label">结果/备注（选填）</text>
          <textarea class="sd-modal__textarea" v-model="newIntervention.result" placeholder="干预结果..." :maxlength="300" style="min-height: 100rpx;" />
        </view>
        <view class="sd-modal__actions">
          <view class="sd-modal__btn sd-modal__btn--cancel" @tap="showInterventionModal = false"><text>取消</text></view>
          <view class="sd-modal__btn sd-modal__btn--ok" @tap="submitIntervention"><text>保存</text></view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

// ============================================================
// 内联 HTTP — 零主包依赖
// ============================================================
const BASE_URL = 'http://localhost:8000/api'

function _request<T = any>(method: 'GET' | 'POST' | 'PUT', path: string, data?: any): Promise<T> {
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
        } else reject({ statusCode: res.statusCode, data: res.data })
      },
      fail(err) { reject(err) },
    })
  })
}

function _get<T = any>(path: string): Promise<T> { return _request<T>('GET', path) }
function _post<T = any>(path: string, data?: any): Promise<T> { return _request<T>('POST', path, data) }

// ============================================================
// 常量
// ============================================================
const TABS = [
  { key: 'profile',      label: '画像' },
  { key: 'risk',         label: '风险' },
  { key: 'assessment',   label: '评估' },
  { key: 'prescription', label: '处方' },
  { key: 'health',       label: '健康数据' },
  { key: 'message',      label: '消息' },
]

const TTM_LABEL: Record<string, string> = {
  precontemplation: '前意向期', contemplation: '意向期', preparation: '准备期',
  action: '行动期', maintenance: '维持期', termination: '终止期',
}
const RISK_LABEL: Record<string, string> = {
  critical: '危急', high: '高风险', medium: '中风险', low: '低风险', unknown: '未评估',
  R4: '高危', R3: '警惕', R2: '关注', R1: '正常',
}
const ASSESS_STATUS: Record<string, string> = {
  assigned: '待完成', submitted: '已提交', pending_review: '待审核', reviewed: '已审核',
}
const RX_STATUS: Record<string, string> = {
  pending: '待审批', approved: '已发送', rejected: '已拒绝', sent: '已发送',
}
const BIG5 = [
  { key: 'openness',          label: '开放性', color: '#8b5cf6' },
  { key: 'conscientiousness', label: '尽责性', color: '#10b981' },
  { key: 'extraversion',      label: '外向性', color: '#f59e0b' },
  { key: 'agreeableness',     label: '宜人性', color: '#3b82f6' },
  { key: 'neuroticism',       label: '神经质', color: '#ef4444' },
]
const INTERVENTION_TYPES = [
  { key: 'phone',    label: '电话', icon: '📞' },
  { key: 'message',  label: '消息', icon: '💬' },
  { key: 'meeting',  label: '面谈', icon: '🤝' },
  { key: 'plan',     label: '方案调整', icon: '📝' },
  { key: 'referral', label: '转介', icon: '🏥' },
]
const INTERVENTION_LABEL: Record<string, string> = {
  phone: '电话干预', message: '消息干预', meeting: '面谈',
  plan: '方案调整', referral: '转介', ai: 'AI干预',
}
const healthCards = [
  { key: 'sleep_hours',      icon: '😴', label: '昨夜睡眠', unit: 'h' },
  { key: 'exercise_minutes', icon: '🏃', label: '今日运动', unit: 'min' },
  { key: 'heart_rate',       icon: '❤️', label: '静息心率', unit: '' },
  { key: 'blood_pressure',   icon: '🩸', label: '血压', unit: '' },
]

// ============================================================
// 状态
// ============================================================
const studentId         = ref(0)
const student           = ref<any>(null)
const activeTab         = ref('profile')
const assessments       = ref<any[]>([])
const prescriptions     = ref<any[]>([])
const messages          = ref<any[]>([])
const glucoseData       = ref<any[]>([])
const healthMetrics     = ref<any>({})
const riskHistory       = ref<any[]>([])
const interventions     = ref<any[]>([])
const msgInput          = ref('')
const showInterventionModal = ref(false)
const newIntervention   = reactive({ type: 'phone', content: '', result: '' })

// ============================================================
// 生命周期
// ============================================================
onMounted(() => {
  const pages = getCurrentPages()
  const pg = pages[pages.length - 1] as any
  studentId.value = Number(pg.$page?.options?.id || pg.options?.id || 0)
  if (studentId.value) { loadStudent(); loadAllData() }
})

// ============================================================
// 数据加载
// ============================================================
async function loadStudent() {
  try {
    const res = await _get<any>(`/v1/coach/students/${studentId.value}`)
    student.value = res
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

async function loadAllData() {
  const sid = studentId.value
  await Promise.allSettled([
    _get<any>(`/v1/coach/students/${sid}/assessments`).then(r => { assessments.value = r.items || r.assessments || [] }).catch(() => {}),
    _get<any>(`/v1/coach/students/${sid}/prescriptions`).then(r => { prescriptions.value = r.items || r.prescriptions || [] }).catch(() => {}),
    _get<any>(`/v1/coach/students/${sid}/messages`).then(r => { messages.value = r.items || r.messages || [] }).catch(() => {}),
    _get<any>(`/v1/coach/students/${sid}/health-data`).then(r => { glucoseData.value = r.glucose_trend || []; healthMetrics.value = r.metrics || {} }).catch(() => {}),
    _get<any>(`/v1/coach/students/${sid}/risk-history`).then(r => { riskHistory.value = r.items || r.history || [] }).catch(() => {}),
    _get<any>(`/v1/coach/students/${sid}/interventions`).then(r => { interventions.value = r.items || r.interventions || [] }).catch(() => {}),
  ])
}

// ============================================================
// 评估操作
// ============================================================
async function assignAssessment() {
  try {
    await _post('/v1/assessment-assignments/assign', { student_id: studentId.value, scales: ['ttm7', 'big5', 'bpt6'] })
    uni.showToast({ title: '已分配', icon: 'success' })
    const res = await _get<any>(`/v1/coach/students/${studentId.value}/assessments`)
    assessments.value = res.items || res.assessments || []
  } catch (e: any) {
    uni.showToast({ title: e?.data?.detail || '分配失败', icon: 'none' })
  }
}

function goAssessmentReview(a: any) {
  if (a.status === 'pending_review') {
    uni.navigateTo({ url: `/pages/coach/assessment/review?id=${a.id}` })
  }
}

// ============================================================
// 处方操作 — 直接内联HTTP，不依赖store
// ============================================================
async function approveRx(p: any) {
  try {
    await _post(`/v1/coach-push/${p.id}/approve`, {})
    p.status = 'approved'
    uni.showToast({ title: '已通过', icon: 'success' })
  } catch { uni.showToast({ title: '操作失败', icon: 'none' }) }
}

async function rejectRx(p: any) {
  try {
    await _post(`/v1/coach-push/${p.id}/reject`, { reason: '教练退回' })
    p.status = 'rejected'
    uni.showToast({ title: '已拒绝', icon: 'none' })
  } catch { uni.showToast({ title: '操作失败', icon: 'none' }) }
}

// ============================================================
// 干预记录
// ============================================================
async function submitIntervention() {
  if (!newIntervention.content.trim()) {
    uni.showToast({ title: '请填写干预内容', icon: 'none' }); return
  }
  try {
    const payload = { ...newIntervention, student_id: studentId.value }
    await _post(`/v1/coach/students/${studentId.value}/interventions`, payload)
    // 本地追加
    interventions.value.unshift({ id: Date.now(), ...newIntervention, created_at: new Date().toISOString() })
    showInterventionModal.value = false
    newIntervention.type = 'phone'; newIntervention.content = ''; newIntervention.result = ''
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch {
    // 后端可能无此端点，本地保存
    interventions.value.unshift({ id: Date.now(), ...newIntervention, created_at: new Date().toISOString() })
    showInterventionModal.value = false
    newIntervention.type = 'phone'; newIntervention.content = ''; newIntervention.result = ''
    uni.showToast({ title: '已本地保存', icon: 'none' })
  }
}

// ============================================================
// 消息操作
// ============================================================
async function sendMsg() {
  const text = msgInput.value.trim()
  if (!text) return
  try {
    await _post(`/v1/coach/students/${studentId.value}/messages`, { content: text, message_type: 'text' })
    messages.value.push({ id: Date.now(), content: text, direction: 'coach', created_at: new Date().toISOString() })
    msgInput.value = ''
  } catch {
    uni.showToast({ title: '发送失败', icon: 'none' })
  }
}

async function getAiSuggestion() {
  uni.showLoading({ title: '获取AI建议...' })
  try {
    const res = await _get<any>(`/v1/coach/students/${studentId.value}/ai-suggestion`)
    msgInput.value = res.suggestion || res.content || ''
  } catch {
    uni.showToast({ title: '获取失败', icon: 'none' })
  } finally { uni.hideLoading() }
}

// ============================================================
// 工具
// ============================================================
function normalizeRisk(level?: string): string {
  if (!level) return 'unknown'
  if (['critical', 'R4', 'high', 'R3'].includes(level)) return 'high'
  if (['medium', 'R2'].includes(level)) return 'medium'
  if (['low', 'R1'].includes(level)) return 'low'
  return 'unknown'
}

function formatDate(dt: string): string {
  if (!dt) return ''
  return dt.slice(0, 16).replace('T', ' ')
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.sd-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

/* 导航 */
.sd-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top));
  background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.sd-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; }
.sd-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.sd-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.sd-navbar__placeholder { width: 64rpx; }

/* 顶部学员信息 */
.sd-header {
  display: flex; align-items: center; gap: 16rpx;
  padding: 20rpx 32rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.sd-header__avatar { width: 80rpx; height: 80rpx; border-radius: 50%; background: var(--bhp-gray-100, #f3f4f6); flex-shrink: 0; }
.sd-header__info { flex: 1; }
.sd-header__name-row { display: flex; align-items: center; gap: 10rpx; }
.sd-header__name { font-size: 32rpx; font-weight: 700; color: var(--text-primary); }
.sd-header__tags { display: flex; gap: 8rpx; margin-top: 6rpx; align-items: center; }
.sd-header__tag { font-size: 20rpx; font-weight: 600; color: #059669; background: rgba(16,185,129,0.1); padding: 2rpx 12rpx; border-radius: var(--radius-full); }
.sd-header__contact { font-size: 20rpx; color: var(--text-tertiary); }

/* 风险标签 */
.sd-risk-tag { font-size: 20rpx; font-weight: 600; padding: 2rpx 14rpx; border-radius: var(--radius-full); }
.sd-risk-tag--high { background: #fef2f2; color: #dc2626; }
.sd-risk-tag--medium { background: #fffbeb; color: #d97706; }
.sd-risk-tag--low { background: #f0fdf4; color: #16a34a; }
.sd-risk-tag--unknown { background: var(--bhp-gray-100, #f3f4f6); color: var(--text-tertiary); }
.sd-risk-tag-sm { font-size: 18rpx; font-weight: 600; padding: 2rpx 10rpx; border-radius: var(--radius-full); }

/* Tab */
.sd-tabs { display: flex; background: var(--surface); border-bottom: 1px solid var(--border-light); padding: 0 8rpx; overflow-x: auto; }
.sd-tab { flex-shrink: 0; text-align: center; padding: 20rpx 16rpx; font-size: 24rpx; color: var(--text-secondary); border-bottom: 3px solid transparent; font-weight: 500; }
.sd-tab--active { color: var(--bhp-primary-500, #10b981); border-bottom-color: var(--bhp-primary-500, #10b981); font-weight: 700; }

.sd-content { flex: 1; overflow-y: auto; }
.sd-tab-body { padding: 20rpx 32rpx 32rpx; }

/* 卡片 */
.sd-card { background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light); }
.sd-card__title { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 16rpx; }
.sd-card__header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16rpx; }
.sd-card__desc { font-size: 26rpx; color: var(--text-secondary); line-height: 1.6; display: block; }

/* 条形图 */
.sd-bars { display: flex; flex-direction: column; gap: 16rpx; }
.sd-bar-row { display: flex; align-items: center; gap: 12rpx; }
.sd-bar-row__label { width: 80rpx; font-size: 22rpx; color: var(--text-secondary); text-align: right; flex-shrink: 0; }
.sd-bar-row__track { flex: 1; height: 18rpx; background: var(--bhp-gray-100, #f3f4f6); border-radius: var(--radius-full); overflow: hidden; }
.sd-bar-row__fill { height: 100%; border-radius: var(--radius-full); transition: width 0.4s; }
.sd-bar-row__val { width: 48rpx; font-size: 22rpx; font-weight: 700; color: var(--text-primary); text-align: right; }

/* 标签 */
.sd-tags { display: flex; flex-wrap: wrap; gap: 12rpx; }
.sd-tag { font-size: 22rpx; font-weight: 600; color: #7c3aed; background: rgba(139,92,246,0.1); padding: 6rpx 16rpx; border-radius: var(--radius-full); }

/* ═══ 风险概览 ═══ */
.sd-risk-overview { display: flex; gap: 24rpx; align-items: flex-start; }
.sd-risk-overview__level { flex-shrink: 0; }
.sd-risk-circle { width: 120rpx; height: 120rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 22rpx; font-weight: 700; color: #fff; }
.sd-risk-circle--high { background: linear-gradient(135deg, #ef4444, #dc2626); }
.sd-risk-circle--medium { background: linear-gradient(135deg, #f59e0b, #d97706); }
.sd-risk-circle--low { background: linear-gradient(135deg, #10b981, #059669); }
.sd-risk-circle--unknown { background: var(--bhp-gray-100, #f3f4f6); color: var(--text-tertiary); }
.sd-risk-overview__factors { flex: 1; }
.sd-risk-overview__subtitle { display: block; font-size: 24rpx; font-weight: 600; color: var(--text-secondary); margin-bottom: 8rpx; }
.sd-risk-factor { display: flex; gap: 6rpx; margin-bottom: 4rpx; }
.sd-risk-factor__dot { color: #ef4444; }
.sd-risk-factor__text { font-size: 24rpx; color: var(--text-secondary); line-height: 1.5; }

/* ═══ 时间线 ═══ */
.sd-timeline { position: relative; }
.sd-timeline__item { display: flex; gap: 16rpx; position: relative; padding-bottom: 20rpx; }
.sd-timeline__dot { width: 20rpx; height: 20rpx; border-radius: 50%; flex-shrink: 0; margin-top: 6rpx; }
.sd-timeline__dot--high { background: #ef4444; }
.sd-timeline__dot--medium { background: #f59e0b; }
.sd-timeline__dot--low { background: #10b981; }
.sd-timeline__dot--unknown { background: #d1d5db; }
.sd-timeline__line { position: absolute; left: 9rpx; top: 30rpx; width: 2rpx; height: calc(100% - 26rpx); background: var(--border-light); }
.sd-timeline__body { flex: 1; }
.sd-timeline__row { display: flex; align-items: center; gap: 12rpx; }
.sd-timeline__date { font-size: 22rpx; color: var(--text-tertiary); }
.sd-timeline__reason { font-size: 24rpx; color: var(--text-secondary); margin-top: 4rpx; line-height: 1.5; }

/* ═══ 干预记录 ═══ */
.sd-add-btn { font-size: 22rpx; font-weight: 600; color: var(--bhp-primary-500, #10b981); padding: 6rpx 16rpx; border-radius: var(--radius-full); background: rgba(16,185,129,0.08); }
.sd-interventions { display: flex; flex-direction: column; gap: 16rpx; }
.sd-intervention { padding: 16rpx; background: var(--surface-secondary); border-radius: var(--radius-md); }
.sd-intervention__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8rpx; }
.sd-intervention__type-tag { font-size: 20rpx; font-weight: 600; padding: 2rpx 12rpx; border-radius: var(--radius-full); }
.sd-intervention__type--phone { background: #eff6ff; color: #2563eb; }
.sd-intervention__type--message { background: #f0fdf4; color: #16a34a; }
.sd-intervention__type--meeting { background: #fefce8; color: #ca8a04; }
.sd-intervention__type--plan { background: #faf5ff; color: #7c3aed; }
.sd-intervention__type--referral { background: #fef2f2; color: #dc2626; }
.sd-intervention__date { font-size: 20rpx; color: var(--text-tertiary); }
.sd-intervention__content { font-size: 24rpx; color: var(--text-primary); line-height: 1.5; }
.sd-intervention__result { font-size: 22rpx; color: var(--text-secondary); margin-top: 6rpx; }

/* 列表 */
.sd-list { display: flex; flex-direction: column; gap: 12rpx; }
.sd-list-item { display: flex; justify-content: space-between; align-items: center; padding: 16rpx 0; border-bottom: 1px solid var(--border-light); }
.sd-list-item:last-child { border-bottom: none; }
.sd-list-item--highlight { background: rgba(245,158,11,0.05); margin: 0 -24rpx; padding: 16rpx 24rpx; border-radius: var(--radius-md); }
.sd-list-item__body { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
.sd-list-item__title { font-size: 26rpx; font-weight: 600; color: var(--text-primary); }
.sd-list-item__sub { font-size: 22rpx; color: var(--text-tertiary); }
.sd-list-item__right { display: flex; flex-direction: column; align-items: flex-end; gap: 8rpx; flex-shrink: 0; }
.sd-status { font-size: 22rpx; font-weight: 600; padding: 4rpx 12rpx; border-radius: var(--radius-full); }
.sd-status--assigned, .sd-status--pending { background: var(--bhp-gray-100, #f3f4f6); color: var(--text-secondary); }
.sd-status--submitted, .sd-status--pending_review { background: #fffbe6; color: #d48806; }
.sd-status--reviewed, .sd-status--approved, .sd-status--sent { background: #f6ffed; color: #389e0d; }
.sd-status--rejected { background: #fff1f0; color: #cf1322; }

/* 处方 */
.sd-rx-actions { display: flex; gap: 10rpx; }
.sd-rx-btn { font-size: 22rpx; font-weight: 600; padding: 6rpx 16rpx; border-radius: var(--radius-full); }
.sd-rx-btn:active { opacity: 0.7; }
.sd-rx-btn--approve { background: var(--bhp-primary-500, #10b981); color: #fff; }
.sd-rx-btn--reject { background: var(--bhp-gray-100, #f3f4f6); color: var(--text-secondary); }

/* 血糖 */
.sd-glucose-chart { display: flex; flex-direction: column; gap: 12rpx; }
.sd-glucose-row { display: flex; align-items: center; gap: 12rpx; }
.sd-glucose-date { width: 80rpx; font-size: 22rpx; color: var(--text-tertiary); text-align: right; flex-shrink: 0; }
.sd-glucose-bar-wrap { flex: 1; height: 16rpx; background: var(--bhp-gray-100, #f3f4f6); border-radius: var(--radius-full); overflow: hidden; }
.sd-glucose-bar { height: 100%; border-radius: var(--radius-full); transition: width 0.3s; }
.sd-glucose-bar--normal { background: #10b981; } .sd-glucose-bar--high { background: #f59e0b; } .sd-glucose-bar--low { background: #ef4444; }
.sd-glucose-val { width: 140rpx; font-size: 22rpx; font-weight: 600; color: var(--text-primary); }

/* 健康 */
.sd-health-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16rpx; padding: 0 32rpx 20rpx; }
.sd-health-card { background: var(--surface); border-radius: var(--radius-lg); padding: 20rpx; display: flex; flex-direction: column; align-items: center; gap: 8rpx; border: 1px solid var(--border-light); }
.sd-health-card__icon { font-size: 40rpx; }
.sd-health-card__val { font-size: 32rpx; font-weight: 700; color: var(--text-primary); }
.sd-health-card__label { font-size: 22rpx; color: var(--text-secondary); }

/* 消息 */
.sd-msg-body { padding-bottom: 120rpx; }
.sd-msg-list { display: flex; flex-direction: column; gap: 20rpx; }
.sd-msg-item { display: flex; flex-direction: column; }
.sd-msg-item--coach { align-items: flex-end; } .sd-msg-item--student { align-items: flex-start; }
.sd-msg-bubble { max-width: 70%; padding: 16rpx 24rpx; border-radius: var(--radius-lg); font-size: 26rpx; line-height: 1.5; word-break: break-all; }
.sd-msg-bubble--coach { background: var(--bhp-primary-500, #10b981); color: #fff; border-bottom-right-radius: 4rpx; }
.sd-msg-bubble--student { background: var(--surface); color: var(--text-primary); border: 1px solid var(--border-light); border-bottom-left-radius: 4rpx; }
.sd-msg-time { font-size: 20rpx; color: var(--text-tertiary); margin-top: 4rpx; }

.sd-msg-input {
  position: fixed; bottom: 0; left: 0; right: 0; display: flex; align-items: center; gap: 12rpx;
  padding: 16rpx 24rpx; padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: var(--surface); border-top: 1px solid var(--border-light);
}
.sd-msg-input__ai { font-size: 22rpx; font-weight: 600; color: var(--bhp-primary-500, #10b981); background: rgba(16,185,129,0.1); padding: 12rpx 16rpx; border-radius: var(--radius-full); white-space: nowrap; flex-shrink: 0; }
.sd-msg-input__ai:active { opacity: 0.7; }
.sd-msg-input__field { flex: 1; height: 64rpx; background: var(--surface-secondary); border: 1px solid var(--border-light); border-radius: var(--radius-lg); padding: 0 20rpx; font-size: 26rpx; color: var(--text-primary); }
.sd-msg-input__send { font-size: 26rpx; font-weight: 600; color: var(--text-tertiary); padding: 12rpx 24rpx; border-radius: var(--radius-full); background: var(--bhp-gray-100, #f3f4f6); white-space: nowrap; flex-shrink: 0; }
.sd-msg-input__send--active { background: var(--bhp-primary-500, #10b981); color: #fff; }

/* 弹窗 */
.sd-modal-mask { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 999; }
.sd-modal { width: 88%; background: var(--surface); border-radius: var(--radius-xl); padding: 32rpx; max-height: 80vh; overflow-y: auto; }
.sd-modal__title { display: block; font-size: 30rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 24rpx; }
.sd-modal__field { margin-bottom: 20rpx; }
.sd-modal__label { display: block; font-size: 24rpx; font-weight: 600; color: var(--text-secondary); margin-bottom: 10rpx; }
.sd-modal__type-list { display: flex; flex-wrap: wrap; gap: 12rpx; }
.sd-modal__type { padding: 10rpx 20rpx; border-radius: var(--radius-full); border: 1px solid var(--border-light); font-size: 22rpx; color: var(--text-secondary); }
.sd-modal__type--active { border-color: var(--bhp-primary-500, #10b981); background: rgba(16,185,129,0.08); color: #059669; font-weight: 600; }
.sd-modal__textarea { width: 100%; min-height: 160rpx; border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 16rpx; font-size: 26rpx; color: var(--text-primary); background: var(--surface-secondary); box-sizing: border-box; }
.sd-modal__actions { display: flex; gap: 16rpx; margin-top: 8rpx; }
.sd-modal__btn { flex: 1; height: 80rpx; border-radius: var(--radius-lg); display: flex; align-items: center; justify-content: center; font-size: 28rpx; font-weight: 600; }
.sd-modal__btn--cancel { background: var(--surface-secondary); color: var(--text-secondary); }
.sd-modal__btn--ok { background: var(--bhp-primary-500, #10b981); color: #fff; }
.sd-modal__btn:active { opacity: 0.85; }

.sd-empty { padding: 24rpx 0; text-align: center; font-size: 24rpx; color: var(--text-tertiary); }
</style>
