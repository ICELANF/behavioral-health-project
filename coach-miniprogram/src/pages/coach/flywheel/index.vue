<template>
  <view class="cf-page">

    <!-- 导航栏 -->
    <view class="cf-navbar safe-area-top">
      <view class="cf-navbar__back" @tap="goBack">
        <text class="cf-navbar__arrow">&#8249;</text>
      </view>
      <view class="cf-navbar__center">
        <text class="cf-navbar__title">AI 跟进计划</text>
        <text class="cf-navbar__sub">基于学员数据智能生成</text>
      </view>
      <view class="cf-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="cf-body">

      <!-- 学员选择器 -->
      <view class="cf-section">
        <text class="cf-section__label">选择学员</text>
        <scroll-view scroll-x class="cf-students-scroll">
          <view class="cf-students-row">
            <view
              v-for="stu in students"
              :key="stu.id"
              class="cf-stu-card"
              :class="{ 'cf-stu-card--active': selectedStudent?.id === stu.id }"
              @tap="selectStudent(stu)"
            >
              <text class="cf-stu-card__name">{{ stu.name || stu.full_name || stu.username }}</text>
              <view class="cf-stu-card__risk" :class="`cf-stu-card__risk--${stu.risk_level || 'unknown'}`">
                <text>{{ RISK_LABEL[stu.risk_level] || '未评估' }}</text>
              </view>
            </view>
            <view class="cf-stu-card cf-stu-card--empty" v-if="!students.length && !loadingStudents">
              <text class="cf-stu-card__name" style="color: var(--text-tertiary);">暂无学员</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 三栏 AI 建议区 -->
      <template v-if="selectedStudent">

        <!-- 消息建议 -->
        <view class="cf-card">
          <view class="cf-card__header">
            <text class="cf-card__icon">💬</text>
            <text class="cf-card__title">消息建议</text>
          </view>
          <template v-if="loadingMsg">
            <view class="bhp-skeleton" v-for="i in 2" :key="i" style="height: 100rpx; border-radius: var(--radius-md); margin-bottom: 12rpx;"></view>
          </template>
          <view v-else-if="msgSuggestions.length" class="cf-suggestions">
            <view v-for="(s, idx) in msgSuggestions" :key="idx" class="cf-sug-item">
              <view class="cf-sug-item__body">
                <text class="cf-sug-item__text">{{ s.content || s.message || s.text || s }}</text>
                <text class="cf-sug-item__reason" v-if="s.rationale || s.reason">{{ s.rationale || s.reason }}</text>
              </view>
              <view class="cf-sug-item__btn" @tap="adoptMessage(s)">
                <text>采纳</text>
              </view>
            </view>
          </view>
          <view v-else class="cf-empty-inline"><text>暂无建议</text></view>
        </view>

        <!-- 微行动建议 -->
        <view class="cf-card">
          <view class="cf-card__header">
            <text class="cf-card__icon">⚡</text>
            <text class="cf-card__title">微行动建议</text>
          </view>
          <template v-if="loadingAction">
            <view class="bhp-skeleton" v-for="i in 2" :key="i" style="height: 100rpx; border-radius: var(--radius-md); margin-bottom: 12rpx;"></view>
          </template>
          <view v-else-if="actionSuggestions.length" class="cf-suggestions">
            <view v-for="(s, idx) in actionSuggestions" :key="idx" class="cf-sug-item">
              <view class="cf-sug-item__body">
                <text class="cf-sug-item__text">{{ s.title || s.content || s }}</text>
                <text class="cf-sug-item__reason" v-if="s.domain">{{ DOMAIN_LABEL[s.domain] || s.domain }}</text>
              </view>
              <view class="cf-sug-item__btn" @tap="adoptAction(s)">
                <text>采纳</text>
              </view>
            </view>
          </view>
          <view v-else class="cf-empty-inline"><text>暂无建议</text></view>
        </view>

        <!-- 评估建议 -->
        <view class="cf-card">
          <view class="cf-card__header">
            <text class="cf-card__icon">📋</text>
            <text class="cf-card__title">评估建议</text>
          </view>
          <template v-if="loadingAssess">
            <view class="bhp-skeleton" v-for="i in 2" :key="i" style="height: 100rpx; border-radius: var(--radius-md); margin-bottom: 12rpx;"></view>
          </template>
          <view v-else-if="assessSuggestions.length" class="cf-suggestions">
            <view v-for="(s, idx) in assessSuggestions" :key="idx" class="cf-sug-item">
              <view class="cf-sug-item__body">
                <text class="cf-sug-item__text">{{ s.scale || s.title || s }}</text>
                <text class="cf-sug-item__reason" v-if="s.rationale || s.reason">{{ s.rationale || s.reason }}</text>
              </view>
              <view class="cf-sug-item__btn" @tap="adoptAssessment(s)">
                <text>采纳</text>
              </view>
            </view>
          </view>
          <view v-else class="cf-empty-inline"><text>暂无建议</text></view>
        </view>

      </template>

      <!-- 未选择学员提示 -->
      <view v-else class="cf-placeholder">
        <text class="cf-placeholder__icon">👆</text>
        <text class="cf-placeholder__text">请先选择一位学员</text>
      </view>

    </scroll-view>

    <!-- 底部按钮 -->
    <view class="cf-footer" v-if="selectedStudent">
      <view class="cf-gen-btn" @tap="generatePlan" :class="{ 'cf-gen-btn--loading': generating }">
        <text class="cf-gen-btn__text">{{ generating ? '生成中...' : '一键生成跟进计划' }}</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/api/request'

const RISK_LABEL: Record<string, string> = {
  critical: '危急', high: '高风险', medium: '中风险', low: '低风险', unknown: '未评估',
}
const DOMAIN_LABEL: Record<string, string> = {
  nutrition: '营养', exercise: '运动', sleep: '睡眠', emotion: '情绪',
  stress: '压力', cognitive: '认知', social: '社交', tcm: '中医',
}

const students         = ref<any[]>([])
const selectedStudent  = ref<any>(null)
const loadingStudents  = ref(false)
const loadingMsg       = ref(false)
const loadingAction    = ref(false)
const loadingAssess    = ref(false)
const generating       = ref(false)
const msgSuggestions   = ref<any[]>([])
const actionSuggestions = ref<any[]>([])
const assessSuggestions = ref<any[]>([])

onMounted(() => loadStudents())

async function loadStudents() {
  loadingStudents.value = true
  try {
    const res = await http.get<any>('/v1/coach/dashboard')
    students.value = (res.students || []).map((s: any) => ({
      ...s,
      name: s.name || s.full_name || s.username,
    }))
  } catch {
    students.value = []
  } finally {
    loadingStudents.value = false
  }
}

function selectStudent(stu: any) {
  if (selectedStudent.value?.id === stu.id) return
  selectedStudent.value = stu
  loadAllSuggestions(stu.id)
}

async function loadAllSuggestions(studentId: number) {
  msgSuggestions.value = []
  actionSuggestions.value = []
  assessSuggestions.value = []
  loadingMsg.value = true
  loadingAction.value = true
  loadingAssess.value = true

  const [msgRes, actionRes, assessRes] = await Promise.allSettled([
    http.get<any>(`/v1/coach/messages/ai-suggestions/${studentId}`),
    http.get<any>(`/v1/coach/micro-actions/ai-suggestions/${studentId}`),
    http.get<any>(`/v1/coach/assessment/ai-suggestions/${studentId}`),
  ])

  if (msgRes.status === 'fulfilled') {
    const d = msgRes.value
    msgSuggestions.value = d.suggestions || d.items || (Array.isArray(d) ? d : [])
  }
  loadingMsg.value = false

  if (actionRes.status === 'fulfilled') {
    const d = actionRes.value
    actionSuggestions.value = d.suggestions || d.items || (Array.isArray(d) ? d : [])
  }
  loadingAction.value = false

  if (assessRes.status === 'fulfilled') {
    const d = assessRes.value
    assessSuggestions.value = d.suggestions || d.scales || d.items || (Array.isArray(d) ? d : [])
  }
  loadingAssess.value = false
}

function adoptMessage(s: any) {
  const content = encodeURIComponent(s.content || s.message || s.text || String(s))
  uni.navigateTo({
    url: `/pages/coach/push-queue?prefill=${content}&student_id=${selectedStudent.value.id}`,
  })
}

async function adoptAction(s: any) {
  try {
    await http.post('/v1/micro-actions', {
      student_id: selectedStudent.value.id,
      title: s.title || s.content || String(s),
      domain: s.domain || 'nutrition',
      source: 'ai_recommended',
    })
    uni.showToast({ title: '已创建微行动', icon: 'success' })
    // Remove from list
    const idx = actionSuggestions.value.indexOf(s)
    if (idx >= 0) actionSuggestions.value.splice(idx, 1)
  } catch (e: any) {
    uni.showToast({ title: e?.message || '创建失败', icon: 'none' })
  }
}

function adoptAssessment(_s: any) {
  uni.navigateTo({ url: '/pages/coach/assessment/index' })
}

async function generatePlan() {
  if (generating.value || !selectedStudent.value) return
  generating.value = true
  try {
    await http.post('/v1/agent/run', {
      agent_type: 'behavior_rx',
      user_id: selectedStudent.value.id,
      context: { source: 'coach_flywheel', action: 'generate_followup_plan' },
    })
    uni.showToast({ title: '跟进计划已生成', icon: 'success' })
    // Reload suggestions
    loadAllSuggestions(selectedStudent.value.id)
  } catch (e: any) {
    uni.showToast({ title: e?.message || '生成失败', icon: 'none' })
  } finally {
    generating.value = false
  }
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.cf-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

.cf-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: linear-gradient(135deg, #059669 0%, #10b981 100%);
  border-bottom: 1px solid var(--border-light);
}
.cf-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.cf-navbar__arrow { font-size: 48rpx; color: #fff; font-weight: 300; }
.cf-navbar__center { text-align: center; }
.cf-navbar__title { display: block; font-size: 28rpx; font-weight: 700; color: #fff; }
.cf-navbar__sub { display: block; font-size: 20rpx; color: rgba(255,255,255,0.75); margin-top: 2rpx; }
.cf-navbar__placeholder { width: 64rpx; }

.cf-body { flex: 1; padding: 20rpx 0 160rpx; }

/* 学员选择器 */
.cf-section { padding: 0 32rpx; margin-bottom: 16rpx; }
.cf-section__label { display: block; font-size: 24rpx; font-weight: 600; color: var(--text-secondary); margin-bottom: 12rpx; }
.cf-students-scroll { white-space: nowrap; }
.cf-students-row { display: inline-flex; gap: 16rpx; padding: 4rpx 0; }
.cf-stu-card {
  display: inline-flex; flex-direction: column; align-items: center; gap: 8rpx;
  padding: 20rpx 24rpx; border-radius: var(--radius-lg);
  background: var(--surface); border: 2px solid var(--border-light);
  cursor: pointer; min-width: 140rpx;
}
.cf-stu-card--active { border-color: var(--bhp-primary-500); background: var(--bhp-primary-50); }
.cf-stu-card__name { font-size: 24rpx; font-weight: 700; color: var(--text-primary); white-space: nowrap; }
.cf-stu-card__risk {
  font-size: 18rpx; font-weight: 600; padding: 2rpx 12rpx;
  border-radius: var(--radius-full);
}
.cf-stu-card__risk--critical,
.cf-stu-card__risk--high { background: #fef2f2; color: #dc2626; }
.cf-stu-card__risk--medium { background: #fffbeb; color: #d97706; }
.cf-stu-card__risk--low { background: #f0fdf4; color: #16a34a; }
.cf-stu-card__risk--unknown { background: #f8fafc; color: #94a3b8; }

/* 卡片 */
.cf-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx 32rpx; margin: 0 32rpx 20rpx;
  border: 1px solid var(--border-light);
}
.cf-card__header { display: flex; align-items: center; gap: 10rpx; margin-bottom: 20rpx; }
.cf-card__icon { font-size: 32rpx; }
.cf-card__title { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }

/* 建议列表 */
.cf-suggestions { display: flex; flex-direction: column; gap: 16rpx; }
.cf-sug-item {
  display: flex; align-items: center; gap: 16rpx;
  padding: 16rpx 20rpx; background: var(--surface-secondary);
  border-radius: var(--radius-md);
}
.cf-sug-item__body { flex: 1; min-width: 0; }
.cf-sug-item__text {
  display: block; font-size: 26rpx; color: var(--text-primary);
  line-height: 1.5; word-break: break-all; white-space: normal;
}
.cf-sug-item__reason {
  display: block; font-size: 22rpx; color: var(--text-tertiary); margin-top: 6rpx;
  line-height: 1.4; word-break: break-all; white-space: normal;
}
.cf-sug-item__btn {
  flex-shrink: 0; padding: 10rpx 24rpx;
  background: var(--bhp-primary-500); color: #fff;
  border-radius: var(--radius-full); font-size: 22rpx; font-weight: 700;
  cursor: pointer;
}
.cf-sug-item__btn:active { opacity: 0.8; }

.cf-empty-inline { text-align: center; padding: 32rpx; font-size: 24rpx; color: var(--text-tertiary); }

/* 未选择提示 */
.cf-placeholder {
  display: flex; flex-direction: column; align-items: center;
  padding: 120rpx 0; gap: 16rpx;
}
.cf-placeholder__icon { font-size: 64rpx; }
.cf-placeholder__text { font-size: 28rpx; color: var(--text-tertiary); }

/* 底部按钮 */
.cf-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  padding: 20rpx 32rpx; padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  background: var(--surface);
  border-top: 1px solid var(--border-light);
}
.cf-gen-btn {
  height: 88rpx; border-radius: var(--radius-lg);
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; box-shadow: 0 4rpx 16rpx rgba(16,185,129,0.3);
}
.cf-gen-btn--loading { opacity: 0.7; pointer-events: none; }
.cf-gen-btn__text { font-size: 30rpx; font-weight: 700; color: #fff; }
.cf-gen-btn:active { opacity: 0.85; }
</style>
