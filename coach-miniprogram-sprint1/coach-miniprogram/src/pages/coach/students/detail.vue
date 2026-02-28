<template>
  <view class="detail-page">

    <!-- 学员档案头部 -->
    <view class="sd-header">
      <view class="sd-header__avatar" :style="{ background: riskColor(student?.risk_level || 'none') }">
        <text class="sd-header__avatar-text">{{ displayInitial }}</text>
      </view>
      <view class="sd-header__info">
        <text class="sd-header__name">{{ student?.full_name || student?.username || '加载中…' }}</text>
        <view class="sd-header__badges">
          <view class="sd-badge sd-badge--risk" :style="{ background: riskColor(student?.risk_level || 'none') }">
            <text>{{ RISK_LABEL[student?.risk_level || 'none'] }}</text>
          </view>
          <view class="sd-badge sd-badge--ttm">
            <text>{{ TTM_LABEL[student?.ttm_stage || 'S0'] }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 骨架屏 -->
    <template v-if="loading">
      <view class="px-4">
        <view v-for="i in 4" :key="i" class="bhp-skeleton" style="height: 120rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </view>
    </template>

    <template v-else>
      <!-- 健康快照 -->
      <view class="sd-health px-4">
        <text class="sd-section-title">健康快照</text>
        <view class="sd-health__grid">
          <view class="sd-health__item" :class="glucoseClass">
            <text class="sd-health__icon">💉</text>
            <text class="sd-health__val">{{ health.latest_glucose ?? '—' }}</text>
            <text class="sd-health__unit">血糖(mmol/L)</text>
            <text class="sd-health__trend" v-if="health.glucose_trend">
              {{ TREND_ICON[health.glucose_trend] }}
            </text>
          </view>
          <view class="sd-health__item">
            <text class="sd-health__icon">😴</text>
            <text class="sd-health__val">{{ health.sleep_score ?? '—' }}</text>
            <text class="sd-health__unit">睡眠评分</text>
          </view>
          <view class="sd-health__item">
            <text class="sd-health__icon">🏃</text>
            <text class="sd-health__val">{{ health.active_minutes ?? '—' }}</text>
            <text class="sd-health__unit">活动(分钟)</text>
          </view>
          <view class="sd-health__item" v-if="health.heart_rate">
            <text class="sd-health__icon">❤️</text>
            <text class="sd-health__val">{{ health.heart_rate }}</text>
            <text class="sd-health__unit">心率(bpm)</text>
          </view>
        </view>
        <text class="sd-health__updated text-xs text-tertiary-color" v-if="health.updated_at">
          更新于 {{ formatDate(health.updated_at) }}
        </text>
      </view>

      <!-- 互动状态 -->
      <view class="sd-status px-4">
        <view class="sd-status__card bhp-card bhp-card--flat">
          <view class="sd-status__item">
            <text class="sd-status__label text-xs text-tertiary-color">互动状态</text>
            <view class="sd-status__val" :class="`stu-interaction--${student?.interaction_status}`">
              <text>{{ INTERACTION_LABEL[student?.interaction_status || ''] || '—' }}</text>
            </view>
          </view>
          <view class="sd-status__divider"></view>
          <view class="sd-status__item">
            <text class="sd-status__label text-xs text-tertiary-color">最近互动</text>
            <text class="sd-status__val-text">{{ relativeTime(student?.last_interaction || '') }}</text>
          </view>
        </view>
      </view>

      <!-- 发送消息 -->
      <view class="sd-message px-4">
        <text class="sd-section-title">发送指导消息</text>
        <view class="sd-message__card bhp-card bhp-card--flat">
          <!-- 消息类型 -->
          <view class="sd-msg-types">
            <view
              v-for="t in MSG_TYPES"
              :key="t.key"
              class="sd-msg-type"
              :class="{ 'sd-msg-type--active': msgType === t.key }"
              @tap="msgType = t.key"
            >
              <text>{{ t.label }}</text>
            </view>
          </view>

          <!-- 输入框 -->
          <textarea
            class="sd-message__input"
            v-model="msgContent"
            placeholder="输入指导内容，将经过审批后推送给学员..."
            placeholder-class="sd-msg-placeholder"
            :maxlength="500"
            auto-height
          />
          <view class="sd-message__footer">
            <text class="text-xs text-tertiary-color">{{ msgContent.length }}/500</text>
            <view
              class="sd-message__send"
              :class="{ 'sd-message__send--active': msgContent.trim() && !sending }"
              @tap="sendMessage"
            >
              <text v-if="!sending">发送审批</text>
              <text v-else>发送中...</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 消息历史 -->
      <view class="sd-history px-4" v-if="messages.length">
        <text class="sd-section-title">消息记录</text>
        <view
          v-for="m in messages"
          :key="m.id"
          class="sd-msg-record bhp-card bhp-card--flat"
        >
          <view class="sd-msg-record__header">
            <view class="sd-msg-type-badge" :class="`sd-msg-badge--${m.message_type}`">
              <text>{{ MSG_TYPE_LABEL[m.message_type] || m.message_type }}</text>
            </view>
            <view class="sd-msg-status-badge" :class="`sd-status-badge--${m.status}`">
              <text>{{ MSG_STATUS_LABEL[m.status] || m.status }}</text>
            </view>
          </view>
          <text class="sd-msg-record__content">{{ m.content }}</text>
          <text class="text-xs text-tertiary-color">{{ formatDate(m.created_at) }}</text>
        </view>
      </view>

      <!-- 评估入口 -->
      <view class="sd-actions px-4">
        <view class="sd-action-btn bhp-card bhp-card--flat" @tap="goAssignAssessment">
          <text class="sd-action-btn__icon">📋</text>
          <view class="sd-action-btn__body">
            <text class="sd-action-btn__title">分配评估</text>
            <text class="sd-action-btn__desc text-xs text-secondary-color">为学员分配健康评估任务</text>
          </view>
          <text class="sd-action-btn__arrow">›</text>
        </view>
      </view>
    </template>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useCoachStore, type Student } from '@/stores/coach'
import { coachApi, type HealthSnapshot, type CoachMessage } from '@/api/coach'

const coachStore = useCoachStore()

const studentId = ref(0)
const student   = ref<Student | null>(null)
const health    = ref<HealthSnapshot>({})
const messages  = ref<CoachMessage[]>([])
const loading   = ref(false)

const msgContent = ref('')
const msgType    = ref('advice')
const sending    = ref(false)

const RISK_LABEL: Record<string, string> = {
  critical: '危急', high: '高风险', moderate: '中风险', low: '低风险', none: '正常'
}
const TTM_LABEL: Record<string, string> = {
  S0: '阶段未知', S1: '前意向期', S2: '意向期',
  S3: '准备期', S4: '行动期', S5: '维持期', S6: '终止'
}
const INTERACTION_LABEL: Record<string, string> = {
  active: '活跃', needs_attention: '需关注', dormant: '休眠'
}
const TREND_ICON: Record<string, string> = { up: '↑', down: '↓', stable: '→' }
const MSG_TYPES = [
  { key: 'advice',        label: '建议' },
  { key: 'encouragement', label: '鼓励' },
  { key: 'reminder',      label: '提醒' },
  { key: 'warning',       label: '警示' },
]
const MSG_TYPE_LABEL: Record<string, string> = {
  advice: '建议', encouragement: '鼓励', reminder: '提醒', warning: '警示'
}
const MSG_STATUS_LABEL: Record<string, string> = {
  pending: '待审批', approved: '已批准', delivered: '已推送', read: '已读'
}

const displayInitial = computed(() =>
  (student.value?.full_name || student.value?.username || '用')[0]
)

const glucoseClass = computed(() => {
  const g = health.value.latest_glucose
  if (!g) return ''
  if (g > 11.1 || g < 3.9) return 'sd-health__item--danger'
  if (g > 7.8 || g < 4.4) return 'sd-health__item--warn'
  return 'sd-health__item--good'
})

function riskColor(level: string): string {
  const map: Record<string, string> = {
    critical: '#f5222d', high: '#ff4d4f', moderate: '#fa8c16', low: '#52c41a', none: '#8c8c8c'
  }
  return map[level] || '#8c8c8c'
}

function relativeTime(dateStr: string): string {
  if (!dateStr) return '暂无记录'
  try {
    const diff = Date.now() - new Date(dateStr).getTime()
    const days = Math.floor(diff / 86400000)
    if (days === 0) return '今天'
    if (days === 1) return '昨天'
    if (days < 7) return `${days}天前`
    return `${Math.floor(days / 7)}周前`
  } catch { return dateStr }
}

function formatDate(s: string): string {
  if (!s) return ''
  try {
    const d = new Date(s)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch { return s }
}

onMounted(async () => {
  // 从 URL query 读取 id
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  studentId.value = Number(cur?.options?.id || 0)

  if (!studentId.value) return

  // 先从 store 缓存中找
  student.value = coachStore.students.find(s => s.id === studentId.value) || null

  loading.value = true
  try {
    const [detail, healthData, msgs] = await Promise.allSettled([
      coachApi.studentDetail(studentId.value),
      coachApi.studentHealth(studentId.value),
      coachApi.messages(studentId.value)
    ])
    if (detail.status === 'fulfilled') student.value = { ...student.value, ...detail.value } as Student
    if (healthData.status === 'fulfilled') health.value = healthData.value
    if (msgs.status === 'fulfilled') messages.value = msgs.value.items || []
  } catch { /* 静默 */ } finally {
    loading.value = false
  }
})

async function sendMessage() {
  if (!msgContent.value.trim() || sending.value) return
  sending.value = true
  try {
    await coachStore.sendMessage(studentId.value, msgContent.value, msgType.value)
    msgContent.value = ''
    uni.showToast({ title: '消息已提交审批', icon: 'success' })
    // 刷新消息列表
    const msgs = await coachApi.messages(studentId.value)
    messages.value = msgs.items || []
  } catch (e: any) {
    uni.showToast({ title: e?.data?.detail || '发送失败', icon: 'none' })
  } finally {
    sending.value = false
  }
}

function goAssignAssessment() {
  uni.navigateTo({ url: '/pages/coach/assessment/index' })
}
</script>

<style scoped>
.detail-page { background: var(--surface-secondary); min-height: 100vh; }

/* 头部 */
.sd-header {
  display: flex; align-items: center; gap: 20rpx;
  padding: 24rpx 32rpx;
  background: var(--surface);
  border-bottom: 1px solid var(--border-light);
}
.sd-header__avatar {
  width: 96rpx; height: 96rpx; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.sd-header__avatar-text { font-size: 40rpx; color: #fff; font-weight: 700; }
.sd-header__info { flex: 1; display: flex; flex-direction: column; gap: 10rpx; }
.sd-header__name { font-size: 34rpx; font-weight: 700; color: var(--text-primary); }
.sd-header__badges { display: flex; gap: 10rpx; }
.sd-badge {
  font-size: 20rpx; font-weight: 700;
  padding: 4rpx 14rpx; border-radius: var(--radius-full);
}
.sd-badge--risk { color: #fff; }
.sd-badge--ttm  { background: var(--bhp-gray-100); color: var(--text-secondary); }

.sd-section-title { display: block; font-size: 26rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 12rpx; }

/* 健康快照 */
.sd-health { padding-top: 20rpx; }
.sd-health__grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10rpx; margin-bottom: 8rpx; }
.sd-health__item {
  background: var(--surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  padding: 16rpx 8rpx;
  display: flex; flex-direction: column; align-items: center; gap: 6rpx;
  position: relative;
}
.sd-health__item--danger { border-color: #ff4d4f40; background: #fff1f0; }
.sd-health__item--warn   { border-color: #fa8c1640; background: #fff7e6; }
.sd-health__item--good   { border-color: #52c41a40; background: #f6ffed; }
.sd-health__icon  { font-size: 28rpx; }
.sd-health__val   { font-size: 30rpx; font-weight: 700; color: var(--text-primary); }
.sd-health__unit  { font-size: 17rpx; color: var(--text-tertiary); text-align: center; }
.sd-health__trend { position: absolute; top: 6rpx; right: 8rpx; font-size: 20rpx; }
.sd-health__updated { display: block; }

/* 状态 */
.sd-status { padding-top: 12rpx; }
.sd-status__card { display: flex; align-items: center; padding: 20rpx 24rpx; }
.sd-status__item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8rpx; }
.sd-status__label { }
.sd-status__val {
  font-size: 22rpx; font-weight: 600;
  padding: 4rpx 14rpx; border-radius: var(--radius-full);
}
.sd-status__val-text { font-size: 26rpx; color: var(--text-primary); font-weight: 500; }
.sd-status__divider { width: 1px; height: 56rpx; background: var(--border-light); }
.stu-interaction--active          { background: var(--bhp-success-50); color: var(--bhp-success-600, #16a34a); }
.stu-interaction--needs_attention { background: var(--bhp-warn-50, #fffbeb); color: var(--bhp-warn-600, #d97706); }
.stu-interaction--dormant         { background: var(--bhp-gray-100); color: var(--text-tertiary); }

/* 发消息 */
.sd-message { padding-top: 20rpx; }
.sd-message__card { padding: 20rpx 24rpx; }
.sd-msg-types { display: flex; gap: 8rpx; margin-bottom: 16rpx; flex-wrap: wrap; }
.sd-msg-type {
  padding: 8rpx 20rpx;
  border-radius: var(--radius-full);
  font-size: 22rpx; color: var(--text-secondary);
  background: var(--bhp-gray-100);
  cursor: pointer;
}
.sd-msg-type--active {
  background: var(--bhp-primary-500); color: #fff; font-weight: 600;
}
.sd-message__input {
  width: 100%; min-height: 140rpx;
  background: var(--bhp-gray-50, #f9fafb);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 16rpx 20rpx;
  font-size: 26rpx; color: var(--text-primary);
  box-sizing: border-box; line-height: 1.6;
}
.sd-msg-placeholder { color: var(--text-tertiary); font-size: 26rpx; }
.sd-message__footer { display: flex; justify-content: space-between; align-items: center; margin-top: 12rpx; }
.sd-message__send {
  padding: 10rpx 28rpx;
  border-radius: var(--radius-full);
  background: var(--bhp-gray-200); color: var(--text-tertiary);
  font-size: 24rpx; font-weight: 600;
}
.sd-message__send--active {
  background: var(--bhp-primary-500); color: #fff; cursor: pointer;
}
.sd-message__send--active:active { opacity: 0.8; }

/* 消息记录 */
.sd-history { padding-top: 20rpx; }
.sd-msg-record { padding: 16rpx 20rpx; margin-bottom: 10rpx; }
.sd-msg-record__header { display: flex; gap: 10rpx; margin-bottom: 10rpx; }
.sd-msg-type-badge, .sd-msg-status-badge {
  font-size: 18rpx; padding: 2rpx 10rpx;
  border-radius: var(--radius-full);
}
.sd-msg-badge--advice        { background: var(--bhp-primary-50); color: var(--bhp-primary-600, #059669); }
.sd-msg-badge--encouragement { background: #fff7e6; color: #d97706; }
.sd-msg-badge--reminder      { background: var(--bhp-gray-100); color: var(--text-secondary); }
.sd-msg-badge--warning       { background: #fff1f0; color: #cf1322; }
.sd-status-badge--pending   { background: var(--bhp-warn-50); color: var(--bhp-warn-600, #d97706); }
.sd-status-badge--approved  { background: var(--bhp-success-50); color: var(--bhp-success-600, #16a34a); }
.sd-status-badge--delivered { background: var(--bhp-primary-50); color: var(--bhp-primary-600); }
.sd-status-badge--read      { background: var(--bhp-gray-100); color: var(--text-tertiary); }
.sd-msg-record__content {
  font-size: 26rpx; color: var(--text-primary); line-height: 1.5;
  display: block; margin-bottom: 8rpx;
}

/* 操作入口 */
.sd-actions { padding-top: 12rpx; }
.sd-action-btn {
  display: flex; align-items: center; gap: 16rpx;
  padding: 20rpx 24rpx; cursor: pointer;
}
.sd-action-btn:active { opacity: 0.8; }
.sd-action-btn__icon { font-size: 36rpx; }
.sd-action-btn__body { flex: 1; }
.sd-action-btn__title { display: block; font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.sd-action-btn__arrow { font-size: 32rpx; color: var(--text-tertiary); }
</style>
