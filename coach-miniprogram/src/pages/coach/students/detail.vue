<template>
  <view class="sd-page">

    <!-- 顶部学员信息 -->
    <view class="sd-header">
      <view class="sd-header__left">
        <image class="sd-header__avatar" :src="student?.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
        <view>
          <view class="sd-header__name-row">
            <text class="sd-header__name">{{ student?.full_name || student?.username || '' }}</text>
            <BHPRiskTag :level="student?.risk_level" />
          </view>
          <view class="sd-header__tags" v-if="student?.ttm_stage">
            <view class="sd-header__tag">
              <text>{{ TTM_LABEL[student.ttm_stage] || student.ttm_stage }}</text>
            </view>
          </view>
        </view>
      </view>
      <view class="sd-header__back" @tap="goBack">
        <text class="sd-header__arrow">‹</text>
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
        <!-- 大五人格 CSS 雷达 -->
        <view class="sd-card">
          <text class="sd-card__title">大五人格</text>
          <view class="sd-radar">
            <view class="sd-radar-item" v-for="dim in BIG5" :key="dim.key">
              <text class="sd-radar-item__label">{{ dim.label }}</text>
              <view class="sd-radar-item__bar">
                <view class="sd-radar-item__fill" :style="{ width: (student?.big5?.[dim.key] || 0) + '%' }"></view>
              </view>
              <text class="sd-radar-item__val">{{ student?.big5?.[dim.key] || 0 }}</text>
            </view>
          </view>
        </view>

        <!-- BPT6 行为类型 -->
        <view class="sd-card" v-if="student?.bpt6_tags?.length">
          <text class="sd-card__title">BPT6 行为类型</text>
          <view class="sd-tags">
            <view class="sd-tag" v-for="tag in student.bpt6_tags.slice(0, 6)" :key="tag">
              <text>{{ tag }}</text>
            </view>
          </view>
        </view>

        <!-- 行为改变阶段 -->
        <view class="sd-card" v-if="student?.behavior_stage_desc">
          <text class="sd-card__title">行为改变阶段</text>
          <text class="sd-card__desc">{{ student.behavior_stage_desc }}</text>
        </view>
      </view>

      <!-- ═══ 评估 Tab ═══ -->
      <view v-if="activeTab === 'assessment'" class="sd-tab-body">
        <view class="sd-card">
          <view class="sd-card__header">
            <text class="sd-card__title">评估记录</text>
            <view class="sd-card__action" @tap="assignAssessment">
              <text class="text-primary-color text-sm font-semibold">+ 分配新评估</text>
            </view>
          </view>
          <view v-if="assessments.length" class="sd-list">
            <view
              v-for="a in assessments"
              :key="a.id"
              class="sd-list-item"
              :class="{ 'sd-list-item--highlight': a.status === 'pending_review' }"
              @tap="goAssessmentReview(a)"
            >
              <view class="sd-list-item__body">
                <text class="sd-list-item__title">{{ a.scale_name || a.title }}</text>
                <text class="sd-list-item__sub">{{ a.created_at?.slice(0, 10) }}</text>
              </view>
              <view class="sd-list-item__status" :class="`sd-status--${a.status}`">
                <text>{{ ASSESS_STATUS[a.status] || a.status }}</text>
              </view>
            </view>
          </view>
          <view v-else class="sd-empty"><text class="text-secondary-color text-sm">暂无评估记录</text></view>
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
                <view class="sd-list-item__status" :class="`sd-status--${p.status}`">
                  <text>{{ RX_STATUS[p.status] || p.status }}</text>
                </view>
                <view class="sd-rx-actions" v-if="p.status === 'pending'">
                  <view class="sd-rx-btn sd-rx-btn--approve" @tap.stop="approveRx(p.id)">
                    <text>通过</text>
                  </view>
                  <view class="sd-rx-btn sd-rx-btn--reject" @tap.stop="rejectRx(p.id)">
                    <text>拒绝</text>
                  </view>
                </view>
              </view>
            </view>
          </view>
          <view v-else class="sd-empty"><text class="text-secondary-color text-sm">暂无行为处方</text></view>
        </view>
      </view>

      <!-- ═══ 健康数据 Tab ═══ -->
      <view v-if="activeTab === 'health'" class="sd-tab-body">
        <!-- 血糖趋势 -->
        <view class="sd-card">
          <text class="sd-card__title">近7天血糖趋势</text>
          <view class="sd-glucose-chart" v-if="glucoseData.length">
            <view class="sd-glucose-row" v-for="(g, i) in glucoseData" :key="i">
              <text class="sd-glucose-date">{{ g.date?.slice(5) }}</text>
              <view class="sd-glucose-bar-wrap">
                <view
                  class="sd-glucose-bar"
                  :class="{
                    'sd-glucose-bar--high': g.value > 10,
                    'sd-glucose-bar--normal': g.value >= 4 && g.value <= 10,
                    'sd-glucose-bar--low': g.value < 4,
                  }"
                  :style="{ width: Math.min((g.value / 16) * 100, 100) + '%' }"
                ></view>
              </view>
              <text class="sd-glucose-val">{{ g.value }} mmol/L</text>
            </view>
          </view>
          <view v-else class="sd-empty"><text class="text-secondary-color text-sm">暂无血糖数据</text></view>
        </view>
        <!-- 关键指标 -->
        <view class="sd-health-grid">
          <view class="sd-health-card">
            <text class="sd-health-card__icon">😴</text>
            <text class="sd-health-card__val">{{ healthMetrics.sleep_hours ?? '--' }}h</text>
            <text class="sd-health-card__label">昨夜睡眠</text>
          </view>
          <view class="sd-health-card">
            <text class="sd-health-card__icon">🏃</text>
            <text class="sd-health-card__val">{{ healthMetrics.exercise_minutes ?? '--' }}min</text>
            <text class="sd-health-card__label">今日运动</text>
          </view>
          <view class="sd-health-card">
            <text class="sd-health-card__icon">❤️</text>
            <text class="sd-health-card__val">{{ healthMetrics.heart_rate ?? '--' }}</text>
            <text class="sd-health-card__label">静息心率</text>
          </view>
          <view class="sd-health-card">
            <text class="sd-health-card__icon">🩸</text>
            <text class="sd-health-card__val">{{ healthMetrics.blood_pressure ?? '--' }}</text>
            <text class="sd-health-card__label">血压</text>
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
        <view v-else class="sd-empty" style="padding-top:60rpx;"><text class="text-secondary-color text-sm">暂无消息记录</text></view>
      </view>

    </scroll-view>

    <!-- 消息 Tab 底部输入栏 -->
    <view class="sd-msg-input safe-area-bottom" v-if="activeTab === 'message'">
      <view class="sd-msg-input__ai" @tap="getAiSuggestion">
        <text>AI建议</text>
      </view>
      <input
        class="sd-msg-input__field"
        v-model="msgInput"
        placeholder="输入消息..."
        :adjust-position="true"
        confirm-type="send"
        @confirm="sendMsg"
      />
      <view class="sd-msg-input__send" :class="{ 'sd-msg-input__send--active': msgInput.trim() }" @tap="sendMsg">
        <text>发送</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useCoachStore } from '@/stores/coach'
import BHPRiskTag from '@/components/BHPRiskTag.vue'
import http from '@/api/request'

const coachStore = useCoachStore()

const TABS = [
  { key: 'profile',      label: '画像' },
  { key: 'assessment',   label: '评估' },
  { key: 'prescription', label: '处方' },
  { key: 'health',       label: '健康数据' },
  { key: 'message',      label: '消息' },
]

const TTM_LABEL: Record<string, string> = {
  precontemplation: '前意向期', contemplation: '意向期',
  preparation: '准备期', action: '行动期',
  maintenance: '维持期', termination: '终止期',
}
const ASSESS_STATUS: Record<string, string> = {
  assigned: '待完成', submitted: '已提交', pending_review: '待审核', reviewed: '已审核',
}
const RX_STATUS: Record<string, string> = {
  pending: '待审批', approved: '已发送', rejected: '已拒绝', sent: '已发送',
}
const BIG5 = [
  { key: 'openness',          label: '开放性' },
  { key: 'conscientiousness', label: '尽责性' },
  { key: 'extraversion',      label: '外向性' },
  { key: 'agreeableness',     label: '宜人性' },
  { key: 'neuroticism',       label: '神经质' },
]

// ── 状态 ─────────────────────────────────────────────
const studentId      = ref(0)
const student        = ref<any>(null)
const activeTab      = ref('profile')
const assessments    = ref<any[]>([])
const prescriptions  = ref<any[]>([])
const messages       = ref<any[]>([])
const glucoseData    = ref<any[]>([])
const healthMetrics  = ref<any>({})
const msgInput       = ref('')

// ── 生命周期 ──────────────────────────────────────────
onLoad((query: any) => {
  studentId.value = Number(query?.id || 0)
})

onMounted(async () => {
  if (!studentId.value) return
  await loadStudent()
  loadTabData()
})

// ── 加载数据 ──────────────────────────────────────────
async function loadStudent() {
  try {
    const res = await http.get<any>(`/v1/coach/students/${studentId.value}`)
    student.value = res
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

async function loadTabData() {
  const fetches = [
    http.get<{ items: any[] }>(`/v1/coach/students/${studentId.value}/assessments`).then(r => { assessments.value = r.items || [] }).catch(() => {}),
    http.get<{ items: any[] }>(`/v1/coach/students/${studentId.value}/prescriptions`).then(r => { prescriptions.value = r.items || [] }).catch(() => {}),
    http.get<{ items: any[] }>(`/v1/coach/students/${studentId.value}/messages`).then(r => { messages.value = r.items || [] }).catch(() => {}),
    http.get<any>(`/v1/coach/students/${studentId.value}/health-data`).then(r => {
      glucoseData.value = r.glucose_trend || []
      healthMetrics.value = r.metrics || {}
    }).catch(() => {}),
  ]
  await Promise.allSettled(fetches)
}

// ── 评估操作 ──────────────────────────────────────────
async function assignAssessment() {
  try {
    await http.post('/v1/assessment/assignments', { student_id: studentId.value })
    uni.showToast({ title: '已分配', icon: 'success' })
    const res = await http.get<{ items: any[] }>(`/v1/coach/students/${studentId.value}/assessments`)
    assessments.value = res.items || []
  } catch {
    uni.showToast({ title: '分配失败', icon: 'none' })
  }
}

function goAssessmentReview(a: any) {
  if (a.status === 'pending_review') {
    uni.navigateTo({ url: `/pages/coach/assessment/review?id=${a.id}` })
  }
}

// ── 处方操作 ──────────────────────────────────────────
async function approveRx(id: number) {
  const ok = await coachStore.approvePush(id)
  if (ok) {
    const item = prescriptions.value.find(p => p.id === id)
    if (item) item.status = 'approved'
    uni.showToast({ title: '已通过', icon: 'success' })
  }
}

async function rejectRx(id: number) {
  const ok = await coachStore.rejectPush(id)
  if (ok) {
    const item = prescriptions.value.find(p => p.id === id)
    if (item) item.status = 'rejected'
    uni.showToast({ title: '已拒绝', icon: 'none' })
  }
}

// ── 消息操作 ──────────────────────────────────────────
async function sendMsg() {
  const text = msgInput.value.trim()
  if (!text) return
  const ok = await coachStore.sendMessage({
    student_id: studentId.value,
    content: text,
    message_type: 'text',
  })
  if (ok) {
    messages.value.push({ id: Date.now(), content: text, direction: 'coach', created_at: new Date().toISOString() })
    msgInput.value = ''
  } else {
    uni.showToast({ title: '发送失败', icon: 'none' })
  }
}

async function getAiSuggestion() {
  uni.showLoading({ title: '获取AI建议...' })
  try {
    const res = await http.get<{ suggestion: string }>(`/v1/coach/students/${studentId.value}/ai-suggestion`)
    msgInput.value = res.suggestion || ''
  } catch {
    uni.showToast({ title: '获取失败', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

// ── 导航 ─────────────────────────────────────────────
function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.sd-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

/* 顶部 */
.sd-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 24rpx 32rpx; background: var(--surface);
}
.sd-header__left { display: flex; align-items: center; gap: 16rpx; flex: 1; }
.sd-header__avatar { width: 80rpx; height: 80rpx; border-radius: 50%; background: var(--bhp-gray-100); flex-shrink: 0; }
.sd-header__name-row { display: flex; align-items: center; gap: 10rpx; }
.sd-header__name { font-size: 32rpx; font-weight: 700; color: var(--text-primary); }
.sd-header__tags { display: flex; gap: 8rpx; margin-top: 6rpx; }
.sd-header__tag {
  font-size: 20rpx; font-weight: 600; color: var(--bhp-primary-500);
  background: rgba(16,185,129,0.1); padding: 2rpx 12rpx; border-radius: var(--radius-full);
}
.sd-header__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.sd-header__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }

/* Tab栏 */
.sd-tabs {
  display: flex; background: var(--surface);
  border-bottom: 1px solid var(--border-light); padding: 0 16rpx;
}
.sd-tab {
  flex: 1; text-align: center; padding: 20rpx 0;
  font-size: 26rpx; color: var(--text-secondary); cursor: pointer;
  border-bottom: 3px solid transparent; font-weight: 500;
}
.sd-tab--active { color: var(--bhp-primary-500); border-bottom-color: var(--bhp-primary-500); font-weight: 700; }

/* 内容 */
.sd-content { flex: 1; overflow-y: auto; }
.sd-tab-body { padding: 20rpx 32rpx 32rpx; }

/* 卡片 */
.sd-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light);
}
.sd-card__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16rpx; }
.sd-card__title { font-size: 28rpx; font-weight: 700; color: var(--text-primary); display: block; margin-bottom: 16rpx; }
.sd-card__header .sd-card__title { margin-bottom: 0; }
.sd-card__action { cursor: pointer; }
.sd-card__desc { font-size: 26rpx; color: var(--text-secondary); line-height: 1.6; display: block; }

/* 大五人格 条形 */
.sd-radar { display: flex; flex-direction: column; gap: 16rpx; }
.sd-radar-item { display: flex; align-items: center; gap: 12rpx; }
.sd-radar-item__label { width: 100rpx; font-size: 24rpx; color: var(--text-secondary); text-align: right; flex-shrink: 0; }
.sd-radar-item__bar { flex: 1; height: 16rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.sd-radar-item__fill { height: 100%; background: var(--bhp-primary-500); border-radius: var(--radius-full); transition: width 0.3s; }
.sd-radar-item__val { width: 60rpx; font-size: 24rpx; font-weight: 700; color: var(--text-primary); }

/* BPT6标签 */
.sd-tags { display: flex; flex-wrap: wrap; gap: 12rpx; }
.sd-tag {
  font-size: 22rpx; font-weight: 600; color: #8b5cf6;
  background: rgba(139,92,246,0.1); padding: 6rpx 16rpx; border-radius: var(--radius-full);
}

/* 列表 */
.sd-list { display: flex; flex-direction: column; gap: 12rpx; }
.sd-list-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16rpx 0; border-bottom: 1px solid var(--border-light); cursor: pointer;
}
.sd-list-item:last-child { border-bottom: none; }
.sd-list-item--highlight { background: rgba(245,158,11,0.05); margin: 0 -24rpx; padding: 16rpx 24rpx; border-radius: var(--radius-md); }
.sd-list-item__body { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
.sd-list-item__title { font-size: 26rpx; font-weight: 600; color: var(--text-primary); }
.sd-list-item__sub { font-size: 22rpx; color: var(--text-tertiary); }
.sd-list-item__right { display: flex; flex-direction: column; align-items: flex-end; gap: 8rpx; flex-shrink: 0; }
.sd-list-item__status { font-size: 22rpx; font-weight: 600; padding: 4rpx 12rpx; border-radius: var(--radius-full); }
.sd-status--assigned,
.sd-status--pending { background: var(--bhp-gray-100); color: var(--text-secondary); }
.sd-status--submitted,
.sd-status--pending_review { background: #fffbe6; color: #d48806; }
.sd-status--reviewed,
.sd-status--approved,
.sd-status--sent { background: #f6ffed; color: #389e0d; }
.sd-status--rejected { background: #fff1f0; color: #cf1322; }

/* 处方审批按钮 */
.sd-rx-actions { display: flex; gap: 10rpx; }
.sd-rx-btn {
  font-size: 22rpx; font-weight: 600; padding: 6rpx 16rpx;
  border-radius: var(--radius-full); cursor: pointer;
}
.sd-rx-btn:active { opacity: 0.7; }
.sd-rx-btn--approve { background: var(--bhp-primary-500); color: #fff; }
.sd-rx-btn--reject { background: var(--bhp-gray-100); color: var(--text-secondary); }

/* 血糖趋势 */
.sd-glucose-chart { display: flex; flex-direction: column; gap: 12rpx; }
.sd-glucose-row { display: flex; align-items: center; gap: 12rpx; }
.sd-glucose-date { width: 80rpx; font-size: 22rpx; color: var(--text-tertiary); text-align: right; flex-shrink: 0; }
.sd-glucose-bar-wrap { flex: 1; height: 16rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; }
.sd-glucose-bar { height: 100%; border-radius: var(--radius-full); transition: width 0.3s; }
.sd-glucose-bar--normal { background: var(--bhp-primary-500); }
.sd-glucose-bar--high { background: #f59e0b; }
.sd-glucose-bar--low { background: #ef4444; }
.sd-glucose-val { width: 140rpx; font-size: 22rpx; font-weight: 600; color: var(--text-primary); }

/* 健康指标网格 */
.sd-health-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16rpx; padding: 0 32rpx 20rpx; }
.sd-health-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 20rpx; display: flex; flex-direction: column; align-items: center; gap: 8rpx;
  border: 1px solid var(--border-light);
}
.sd-health-card__icon { font-size: 40rpx; }
.sd-health-card__val { font-size: 32rpx; font-weight: 700; color: var(--text-primary); }
.sd-health-card__label { font-size: 22rpx; color: var(--text-secondary); }

/* 消息 */
.sd-msg-body { padding-bottom: 120rpx; }
.sd-msg-list { display: flex; flex-direction: column; gap: 20rpx; }
.sd-msg-item { display: flex; flex-direction: column; }
.sd-msg-item--coach { align-items: flex-end; }
.sd-msg-item--student { align-items: flex-start; }
.sd-msg-bubble {
  max-width: 70%; padding: 16rpx 24rpx; border-radius: var(--radius-lg);
  font-size: 26rpx; line-height: 1.5; word-break: break-all;
}
.sd-msg-bubble--coach { background: var(--bhp-primary-500); color: #fff; border-bottom-right-radius: 4rpx; }
.sd-msg-bubble--student { background: var(--surface); color: var(--text-primary); border: 1px solid var(--border-light); border-bottom-left-radius: 4rpx; }
.sd-msg-time { font-size: 20rpx; color: var(--text-tertiary); margin-top: 4rpx; }

/* 消息输入栏 */
.sd-msg-input {
  position: fixed; bottom: 0; left: 0; right: 0;
  display: flex; align-items: center; gap: 12rpx;
  padding: 16rpx 24rpx; background: var(--surface);
  border-top: 1px solid var(--border-light);
}
.sd-msg-input__ai {
  font-size: 22rpx; font-weight: 600; color: var(--bhp-primary-500);
  background: rgba(16,185,129,0.1); padding: 12rpx 20rpx; border-radius: var(--radius-full);
  cursor: pointer; white-space: nowrap; flex-shrink: 0;
}
.sd-msg-input__ai:active { opacity: 0.7; }
.sd-msg-input__field {
  flex: 1; height: 64rpx; background: var(--bhp-gray-50); border: 1px solid var(--border-light);
  border-radius: var(--radius-lg); padding: 0 20rpx; font-size: 26rpx; color: var(--text-primary);
}
.sd-msg-input__send {
  font-size: 26rpx; font-weight: 600; color: var(--text-tertiary);
  padding: 12rpx 24rpx; border-radius: var(--radius-full); cursor: pointer;
  background: var(--bhp-gray-100); white-space: nowrap; flex-shrink: 0;
}
.sd-msg-input__send--active { background: var(--bhp-primary-500); color: #fff; }

.sd-empty { padding: 24rpx 0; text-align: center; }
</style>
