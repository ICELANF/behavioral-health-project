<template>
  <view class="fw-page">
    <view class="fw-navbar">
      <view class="fw-nav-back" @tap="goBack">←</view>
      <text class="fw-nav-title">AI 飞轮</text>
      <view class="fw-nav-action" @tap="refresh">↻</view>
    </view>

    <!-- 飞轮可视化 -->
    <view class="fw-wheel">
      <view v-for="(step, i) in wheelSteps" :key="i" class="fw-wheel-step" :class="{ 'fw-wheel-step--active': i === activeWheelStep }">
        <text class="fw-wheel-icon">{{ step.icon }}</text>
        <text class="fw-wheel-label">{{ step.label }}</text>
      </view>
    </view>

    <!-- 今日统计 -->
    <view class="fw-stats">
      <view class="fw-stat" v-for="s in todayStats" :key="s.label">
        <text class="fw-stat-num" :style="{ color: s.color }">{{ s.value }}</text>
        <text class="fw-stat-label">{{ s.label }}</text>
      </view>
    </view>

    <!-- Tab -->
    <view class="fw-tabs">
      <view v-for="tab in fwTabs" :key="tab.key" class="fw-tab" :class="{ 'fw-tab--active': activeTab === tab.key }" @tap="activeTab = tab.key">
        {{ tab.label }}
      </view>
    </view>

    <scroll-view scroll-y class="fw-list" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <!-- 待审核 -->
      <template v-if="activeTab === 'pending'">
        <view v-for="item in pendingItems" :key="item.id" class="fw-card" :class="{ 'fw-card--done': item._done }">
          <view class="fw-card-header">
            <text class="fw-card-student">{{ item.student_name || '学员' }}</text>
            <view class="fw-card-type" :style="{ background: typeColor(item.type) }">{{ item.type || '推送' }}</view>
          </view>
          <text class="fw-card-summary">{{ item.ai_summary || item.summary || '—' }}</text>
          <view class="fw-card-draft" v-if="item._expanded">
            <text class="fw-card-draft-text">{{ item.ai_draft || item.content || item.title || '无草稿' }}</text>
          </view>
          <view class="fw-card-toggle" @tap="item._expanded = !item._expanded">
            {{ item._expanded ? '收起 ▲' : '查看草稿 ▼' }}
          </view>
          <view v-if="!item._done" class="fw-card-actions">
            <view class="fw-btn fw-btn--approve" @tap="approveItem(item)">✓ 通过</view>
            <view class="fw-btn fw-btn--reject" @tap="showReject(item)">✗ 退回</view>
          </view>
          <view v-else class="fw-card-done-label" :style="{ color: item._done === 'approved' ? '#27AE60' : '#E74C3C' }">
            {{ item._done === 'approved' ? '✓ 已通过' : '✗ 已退回' }}
          </view>
        </view>
        <view v-if="pendingItems.length === 0" class="fw-empty">
          <text class="fw-empty-icon">✅</text>
          <text class="fw-empty-text">今日审核已全部完成!</text>
        </view>
      </template>

      <!-- AI跟进计划 -->
      <template v-if="activeTab === 'generate'">
        <view class="fw-gen-section">
          <text class="fw-gen-title">选择学员生成AI跟进计划</text>
          <scroll-view scroll-x class="fw-student-picker">
            <view v-for="s in studentList" :key="s.id" class="fw-student-chip" :class="{ 'fw-student-chip--active': selectedStudent?.id === s.id }" @tap="selectedStudent = s">
              {{ s.name }}
            </view>
          </scroll-view>
          <view v-if="selectedStudent" class="fw-gen-form">
            <textarea class="fw-gen-input" placeholder="自定义AI指令（可选）" v-model="customPrompt" />
            <view class="fw-gen-btn" @tap="runAgent" :class="{ 'fw-gen-btn--loading': generating }">
              {{ generating ? '生成中...' : '🚀 生成跟进计划' }}
            </view>
          </view>
          <view v-if="agentResult" class="fw-gen-result">
            <text class="fw-gen-result-title">AI 建议:</text>
            <text class="fw-gen-result-text">{{ agentResult }}</text>
          </view>
        </view>
      </template>
    </scroll-view>

    <!-- 退回原因弹窗 -->
    <view v-if="rejectModal" class="fw-modal-mask" @tap="rejectModal = null">
      <view class="fw-modal" @tap.stop>
        <text class="fw-modal-title">退回原因</text>
        <textarea class="fw-modal-input" v-model="rejectReason" placeholder="请输入退回原因" />
        <view class="fw-modal-actions">
          <view class="fw-modal-btn fw-modal-cancel" @tap="rejectModal = null">取消</view>
          <view class="fw-modal-btn fw-modal-confirm" @tap="doReject">确认退回</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const activeTab = ref('pending')
const refreshing = ref(false)
const pendingItems = ref<any[]>([])
const studentList = ref<any[]>([])
const selectedStudent = ref<any>(null)
const customPrompt = ref('')
const generating = ref(false)
const agentResult = ref('')
const rejectModal = ref<any>(null)
const rejectReason = ref('')
const approvedCount = ref(0)
const rejectedCount = ref(0)
const activeWheelStep = ref(2) // 审核阶段

const wheelSteps = [
  { icon: '📊', label: '数据采集' },
  { icon: '🤖', label: 'AI分析' },
  { icon: '👨‍⚕️', label: '教练审核' },
  { icon: '📤', label: '推送执行' },
  { icon: '📈', label: '效果追踪' },
]

const fwTabs = [
  { key: 'pending', label: '待审核' },
  { key: 'generate', label: 'AI跟进' },
]

const todayStats = computed(() => [
  { label: '待审核', value: pendingItems.value.filter(i => !i._done).length, color: '#E67E22' },
  { label: '已通过', value: approvedCount.value, color: '#27AE60' },
  { label: '已退回', value: rejectedCount.value, color: '#E74C3C' },
])

function typeColor(t: string): string {
  const map: Record<string, string> = { rx_push: '#3498DB', prescription: '#9B59B6', assessment: '#E67E22' }
  return map[t] || '#5B6B7F'
}

async function loadData() {
  // 飞轮审核队列 (多端点fallback)
  try {
    const res = await http<any>('/api/v1/coach/review-queue')
    pendingItems.value = (res.items || res.queue || (Array.isArray(res) ? res : [])).map((i: any) => ({ ...i, _expanded: false, _done: '' }))
  } catch {
    try {
      const res2 = await http<any>('/api/v1/coach-push/pending?page_size=50')
      pendingItems.value = (res2.items || []).map((i: any) => ({ ...i, _expanded: false, _done: '' }))
    } catch { pendingItems.value = [] }
  }

  // 今日统计
  try {
    const res = await http<any>('/api/v1/coach/stats/today')
    approvedCount.value = res.approved || 0
    rejectedCount.value = res.rejected || 0
  } catch {}

  // 学员列表
  try {
    const res = await http<any>('/api/v1/coach/dashboard')
    studentList.value = (res.students || []).map((s: any) => ({
      id: s.id || s.user_id,
      name: s.name || s.full_name || '未知',
    }))
  } catch { studentList.value = [] }
}

async function approveItem(item: any) {
  try {
    await http(`/api/v1/coach/review/${item.id}/approve`, { method: 'POST' })
  } catch {
    try { await http(`/api/v1/coach-push/${item.id}/approve`, { method: 'POST' }) } catch {}
  }
  item._done = 'approved'
  approvedCount.value++
}

function showReject(item: any) {
  rejectModal.value = item
  rejectReason.value = ''
}

async function doReject() {
  if (!rejectModal.value) return
  try {
    await http(`/api/v1/coach/review/${rejectModal.value.id}/reject`, { method: 'POST', data: { reason: rejectReason.value } })
  } catch {
    try { await http(`/api/v1/coach-push/${rejectModal.value.id}/reject`, { method: 'POST', data: { reason: rejectReason.value } }) } catch {}
  }
  rejectModal.value._done = 'rejected'
  rejectedCount.value++
  rejectModal.value = null
}

async function runAgent() {
  if (!selectedStudent.value || generating.value) return
  generating.value = true
  agentResult.value = ''
  try {
    const res = await http<any>('/api/v1/agent/run', {
      method: 'POST',
      data: {
        agent_type: 'coach_flywheel',
        user_id: String(selectedStudent.value.id),
        input: customPrompt.value || '请为该学员生成个性化跟进计划',
      }
    })
    agentResult.value = res.result || res.output || res.text || JSON.stringify(res)
  } catch (e: any) {
    agentResult.value = '生成失败: ' + (e.message || '请重试')
  }
  generating.value = false
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
.fw-page { min-height: 100vh; background: #F5F6FA; }
.fw-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #27AE60 0%, #2ECC71 100%); color: #fff; }
.fw-nav-back { font-size: 40rpx; padding: 16rpx; }
.fw-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.fw-nav-action { font-size: 36rpx; padding: 16rpx; }

.fw-wheel { display: flex; padding: 20rpx 16rpx; gap: 4rpx; }
.fw-wheel-step { flex: 1; text-align: center; padding: 12rpx 4rpx; border-radius: 12rpx; background: #fff; }
.fw-wheel-step--active { background: #27AE60; }
.fw-wheel-step--active .fw-wheel-label { color: #fff; }
.fw-wheel-icon { display: block; font-size: 28rpx; }
.fw-wheel-label { display: block; font-size: 18rpx; color: #5B6B7F; margin-top: 4rpx; }

.fw-stats { display: flex; padding: 0 24rpx 16rpx; gap: 12rpx; }
.fw-stat { flex: 1; text-align: center; background: #fff; border-radius: 12rpx; padding: 16rpx; }
.fw-stat-num { display: block; font-size: 40rpx; font-weight: 700; }
.fw-stat-label { display: block; font-size: 22rpx; color: #8E99A4; }

.fw-tabs { display: flex; padding: 0 24rpx 12rpx; gap: 12rpx; }
.fw-tab { flex: 1; text-align: center; padding: 14rpx 0; background: #fff; border-radius: 12rpx; font-size: 26rpx; color: #5B6B7F; }
.fw-tab--active { background: #27AE60; color: #fff; }

.fw-list { height: calc(100vh - 580rpx); padding: 0 24rpx; }
.fw-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; }
.fw-card--done { opacity: 0.6; }
.fw-card-header { display: flex; align-items: center; justify-content: space-between; }
.fw-card-student { font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.fw-card-type { padding: 4rpx 12rpx; border-radius: 6rpx; color: #fff; font-size: 22rpx; }
.fw-card-summary { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 12rpx; }
.fw-card-draft { background: #F8F9FA; border-radius: 12rpx; padding: 16rpx; margin-top: 12rpx; }
.fw-card-draft-text { font-size: 26rpx; color: #2C3E50; line-height: 1.6; }
.fw-card-toggle { text-align: center; font-size: 24rpx; color: #3498DB; margin-top: 8rpx; padding: 8rpx; }
.fw-card-actions { display: flex; gap: 16rpx; margin-top: 16rpx; }
.fw-btn { flex: 1; text-align: center; padding: 16rpx 0; border-radius: 10rpx; font-size: 28rpx; font-weight: 600; }
.fw-btn--approve { background: #27AE60; color: #fff; }
.fw-btn--reject { background: #FFF5F5; color: #E74C3C; border: 1rpx solid #E74C3C; }
.fw-card-done-label { text-align: center; margin-top: 12rpx; font-size: 26rpx; font-weight: 600; }

.fw-gen-section { background: #fff; border-radius: 16rpx; padding: 24rpx; }
.fw-gen-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }
.fw-student-picker { display: flex; white-space: nowrap; gap: 12rpx; padding-bottom: 16rpx; }
.fw-student-chip { display: inline-block; padding: 12rpx 24rpx; border-radius: 24rpx; background: #F0F0F0; font-size: 26rpx; color: #5B6B7F; }
.fw-student-chip--active { background: #27AE60; color: #fff; }
.fw-gen-form { margin-top: 16rpx; }
.fw-gen-input { width: 100%; height: 120rpx; padding: 16rpx; background: #F8F9FA; border-radius: 12rpx; font-size: 26rpx; box-sizing: border-box; }
.fw-gen-btn { text-align: center; padding: 20rpx; background: #27AE60; color: #fff; border-radius: 12rpx; font-size: 30rpx; font-weight: 600; margin-top: 16rpx; }
.fw-gen-btn--loading { opacity: 0.6; }
.fw-gen-result { margin-top: 20rpx; background: #F0FFF0; border-radius: 12rpx; padding: 20rpx; border-left: 4rpx solid #27AE60; }
.fw-gen-result-title { display: block; font-size: 26rpx; font-weight: 600; color: #27AE60; margin-bottom: 8rpx; }
.fw-gen-result-text { font-size: 26rpx; color: #2C3E50; line-height: 1.6; }

.fw-empty { text-align: center; padding: 120rpx 0; }
.fw-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.fw-empty-text { font-size: 28rpx; color: #8E99A4; }

.fw-modal-mask { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 999; }
.fw-modal { width: 85%; background: #fff; border-radius: 24rpx; padding: 32rpx; }
.fw-modal-title { display: block; font-size: 32rpx; font-weight: 600; text-align: center; margin-bottom: 20rpx; }
.fw-modal-input { width: 100%; height: 160rpx; padding: 16rpx; background: #F8F9FA; border-radius: 12rpx; font-size: 28rpx; box-sizing: border-box; }
.fw-modal-actions { display: flex; gap: 16rpx; margin-top: 24rpx; }
.fw-modal-btn { flex: 1; text-align: center; padding: 20rpx 0; border-radius: 12rpx; font-size: 28rpx; }
.fw-modal-cancel { background: #F0F0F0; color: #5B6B7F; }
.fw-modal-confirm { background: #E74C3C; color: #fff; }
</style>