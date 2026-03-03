<template>
  <view class="fw-page">
    <view class="fw-navbar">
      <view class="fw-nav-back" @tap="goBack">←</view>
      <text class="fw-nav-title">AI 飞轮</text>
      <view class="fw-nav-action" @tap="refresh">↻</view>
    </view>

    <!-- 飞轮5步骤可视化 -->
    <view class="fw-wheel">
      <view v-for="(step, i) in wheelSteps" :key="i" class="fw-wheel-step"
        :class="{ 'fw-wheel-step--active': i === activeWheelStep }">
        <text class="fw-wheel-icon">{{ step.icon }}</text>
        <text class="fw-wheel-label">{{ step.label }}</text>
      </view>
    </view>

    <!-- 统计+Tab 单排 — 全部可点击 -->
    <view class="fw-stattabs">
      <view class="fw-st" :class="{ 'fw-st--active': activeTab === 'generate' }" @tap="activeTab = 'generate'">
        <text class="fw-st-num">{{ studentList.length }}</text>
        <text class="fw-st-label">AI跟进</text>
      </view>
      <view class="fw-st" :class="{ 'fw-st--active': activeTab === 'pending' }" @tap="activeTab = 'pending'">
        <text class="fw-st-num" :style="{ color: activeTab === 'pending' ? '#fff' : '#E67E22' }">{{ pendingItems.filter(i => !i._done).length }}</text>
        <text class="fw-st-label">待审核</text>
      </view>
      <view class="fw-st" :class="{ 'fw-st--active': activeTab === 'approved' }" @tap="activeTab = 'approved'">
        <text class="fw-st-num" :style="{ color: activeTab === 'approved' ? '#fff' : '#27AE60' }">{{ approvedCount }}</text>
        <text class="fw-st-label">已通过</text>
      </view>
      <view class="fw-st" :class="{ 'fw-st--active': activeTab === 'rejected' }" @tap="activeTab = 'rejected'">
        <text class="fw-st-num" :style="{ color: activeTab === 'rejected' ? '#fff' : '#E74C3C' }">{{ rejectedCount }}</text>
        <text class="fw-st-label">已退回</text>
      </view>
    </view>

    <!-- AI跟进：固定搜索栏+风险筛选（不随列表滚动） -->
    <view v-if="activeTab === 'generate'" class="fw-search-area">
      <view class="fw-search-row">
        <input class="fw-search-input" v-model="searchText" placeholder="搜索学员姓名…" />
        <text class="fw-search-count">{{ filteredStudents.length }}/{{ studentList.length }}</text>
      </view>
      <view class="fw-risk-chips">
        <view v-for="f in riskFilters" :key="f.key" class="fw-risk-chip"
          :class="{ 'fw-risk-chip--active': riskFilter === f.key }" @tap="riskFilter = f.key">
          {{ f.label }}
        </view>
      </view>
    </view>

    <!-- 主滚动区 -->
    <scroll-view scroll-y class="fw-list"
      :class="{ 'fw-list--with-bar': activeTab === 'generate' && selectedStudent }"
      refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

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
          <text class="fw-empty-text">今日审核已全部完成！</text>
        </view>
      </template>

      <!-- 已通过 -->
      <template v-if="activeTab === 'approved'">
        <view v-for="item in approvedItems" :key="item.id" class="fw-card">
          <view class="fw-card-header">
            <text class="fw-card-student">{{ item.student_name || '学员' }}</text>
            <text class="fw-card-time">{{ item.approved_at ? item.approved_at.slice(0,10) : '今日' }}</text>
          </view>
          <text class="fw-card-summary">{{ item.ai_summary || item.summary || '—' }}</text>
          <text class="fw-card-done-label" style="color:#27AE60;">✓ 已推送给学员</text>
        </view>
        <view v-if="approvedItems.length === 0" class="fw-empty">
          <text class="fw-empty-icon">📋</text>
          <text class="fw-empty-text">今日暂无已通过记录</text>
        </view>
      </template>

      <!-- 已退回 -->
      <template v-if="activeTab === 'rejected'">
        <view v-for="item in rejectedItems" :key="item.id" class="fw-card">
          <view class="fw-card-header">
            <text class="fw-card-student">{{ item.student_name || '学员' }}</text>
            <text class="fw-card-time">{{ item.rejected_at ? item.rejected_at.slice(0,10) : '今日' }}</text>
          </view>
          <text class="fw-card-summary">{{ item.ai_summary || item.summary || '—' }}</text>
          <view class="fw-card-reject-reason" v-if="item.coach_note">
            <text class="fw-card-reject-label">退回原因：</text>
            <text class="fw-card-reject-text">{{ item.coach_note }}</text>
          </view>
          <view class="fw-btn fw-btn--regen" @tap="regenFromRejected(item)">↻ 重新生成</view>
        </view>
        <view v-if="rejectedItems.length === 0" class="fw-empty">
          <text class="fw-empty-icon">🔄</text>
          <text class="fw-empty-text">今日暂无退回记录</text>
        </view>
      </template>

      <!-- AI跟进 — 学员选择列表 -->
      <template v-if="activeTab === 'generate'">
        <!-- 今日重点：AI推荐高风险学员，无需手动扫描全部列表 -->
        <view v-if="priorityStudents.length > 0 && !searchText" class="fw-priority-section">
          <text class="fw-section-label">今日重点 — AI建议优先跟进</text>
          <view class="fw-priority-row">
            <view v-for="s in priorityStudents" :key="s.id" class="fw-priority-card"
              :class="{ 'fw-priority-card--active': selectedStudent?.id === s.id }"
              @tap="selectedStudent = s">
              <view class="fw-priority-avatar" :style="{ background: avatarColor(s.name) }">{{ s.name[0] }}</view>
              <text class="fw-priority-name">{{ s.name }}</text>
              <text class="fw-priority-risk" :style="{ color: riskColorText(s.risk_level) }">R{{ s.risk_level }}</text>
            </view>
          </view>
        </view>

        <!-- 全部学员列表（按风险降序，搜索+筛选后） -->
        <view class="fw-section-label-row">
          <text class="fw-section-label">{{ searchText || riskFilter !== 'all' ? '筛选结果' : '全部学员' }}</text>
          <text class="fw-section-count">{{ filteredStudents.length }} 人</text>
        </view>
        <view class="fw-student-list">
          <view v-for="s in filteredStudents" :key="s.id" class="fw-student-row"
            :class="{ 'fw-student-row--active': selectedStudent?.id === s.id }"
            @tap="selectedStudent = s">
            <view class="fw-student-avatar" :style="{ background: avatarColor(s.name) }">{{ (s.name||'?')[0] }}</view>
            <view class="fw-student-info">
              <text class="fw-student-name">{{ s.name }}</text>
              <text class="fw-student-sub">{{ s.stage_label || '进行中' }} · Day {{ s.day_index || '—' }}</text>
            </view>
            <view class="fw-student-risk" :style="{ background: riskBg(s.risk_level) }">R{{ s.risk_level || 0 }}</view>
            <text v-if="selectedStudent?.id === s.id" class="fw-student-check">✓</text>
          </view>
          <view v-if="filteredStudents.length === 0" class="fw-student-empty">
            {{ searchText ? '未找到匹配学员' : '暂无学员数据' }}
          </view>
        </view>

        <!-- AI建议结果（选中学员后生成） -->
        <view v-if="agentResult" class="fw-gen-result">
          <view class="fw-gen-result-header">
            <text class="fw-gen-result-title">AI 跟进建议 — {{ selectedStudent?.name }}</text>
          </view>
          <text class="fw-gen-result-text">{{ agentResult }}</text>
          <view class="fw-gen-result-hint">结果已自动进入待审核队列</view>
        </view>

        <view style="height:160rpx;"></view>
      </template>
    </scroll-view>

    <!-- 固定底部操作栏 — 仅 AI跟进 Tab 且已选学员时显示 -->
    <!-- 无论学员列表多长，生成按钮始终可见，无需滚动 -->
    <view v-if="activeTab === 'generate' && selectedStudent" class="fw-fixed-bar">
      <view class="fw-fixed-student">
        <view class="fw-fixed-avatar" :style="{ background: avatarColor(selectedStudent.name) }">
          {{ selectedStudent.name[0] }}
        </view>
        <view class="fw-fixed-info">
          <text class="fw-fixed-name">{{ selectedStudent.name }}</text>
          <text class="fw-fixed-stage">{{ selectedStudent.stage_label || '进行中' }}</text>
        </view>
        <text class="fw-fixed-risk" :style="{ color: riskColorText(selectedStudent.risk_level) }">
          R{{ selectedStudent.risk_level }}
        </text>
        <view class="fw-fixed-clear" @tap="selectedStudent = null">✕</view>
      </view>
      <view class="fw-fixed-prompt">
        <input class="fw-fixed-input" v-model="customPrompt" placeholder="自定义AI指令（可选）…" />
      </view>
      <view class="fw-fixed-btn" @tap="runAgent" :class="{ 'fw-fixed-btn--loading': generating }">
        {{ generating ? '生成中…' : '🚀 生成跟进计划' }}
      </view>
    </view>

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
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { httpReq as http } from '@/api/request'

const activeTab = ref('pending')
const refreshing = ref(false)
const pendingItems = ref<any[]>([])
const approvedItems = ref<any[]>([])
const rejectedItems = ref<any[]>([])
const studentList = ref<any[]>([])
const selectedStudent = ref<any>(null)
const customPrompt = ref('')
const generating = ref(false)
const agentResult = ref('')
const rejectModal = ref<any>(null)
const rejectReason = ref('')
const approvedCount = ref(0)
const rejectedCount = ref(0)
const activeWheelStep = ref(2)

// 搜索与筛选（解决200人扩展性问题）
const searchText = ref('')
const riskFilter = ref('all')

const riskFilters = [
  { key: 'all', label: '全部' },
  { key: '3', label: 'R3 高危' },
  { key: '2', label: 'R2 中危' },
  { key: '1', label: 'R1 低危' },
]

const wheelSteps = [
  { icon: '📊', label: '数据采集' },
  { icon: '🤖', label: 'AI分析' },
  { icon: '👨‍⚕️', label: '教练审核' },
  { icon: '📤', label: '推送执行' },
  { icon: '📈', label: '效果追踪' },
]

// 筛选后的学员列表（搜索+风险过滤）
const filteredStudents = computed(() => {
  let list = studentList.value
  if (riskFilter.value !== 'all') {
    list = list.filter(s => s.risk_level === parseInt(riskFilter.value))
  }
  if (searchText.value.trim()) {
    const q = searchText.value.trim()
    list = list.filter(s => s.name.includes(q))
  }
  return list
})

// 今日重点：取前3名高风险学员，无需手动扫描整个列表
const priorityStudents = computed(() =>
  studentList.value.filter(s => s.risk_level >= 2).slice(0, 3)
)

const AVATAR_COLORS = ['#3498DB', '#E67E22', '#27AE60', '#9B59B6', '#E74C3C', '#1ABC9C']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let h = 0; for (let i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h)
  return AVATAR_COLORS[Math.abs(h) % AVATAR_COLORS.length]
}

function riskColorText(level: number): string {
  if (level >= 3) return '#E74C3C'
  if (level >= 2) return '#E67E22'
  return '#27AE60'
}

function riskBg(level: number): string {
  if (level >= 3) return '#FFF0F0'
  if (level >= 2) return '#FFF8F0'
  return '#F0FFF4'
}

function typeColor(t: string): string {
  const map: Record<string, string> = { rx_push: '#3498DB', prescription: '#9B59B6', assessment: '#E67E22' }
  return map[t] || '#5B6B7F'
}

async function loadData() {
  // 审核队列（全状态：pending/approved/rejected）
  try {
    const res = await http<any>('/api/v1/coach/review-queue')
    const all = res.items || res.queue || (Array.isArray(res) ? res : [])
    pendingItems.value = all.filter((i: any) => !['approved','rejected'].includes(i.status))
      .map((i: any) => ({ ...i, _expanded: false, _done: '' }))
    approvedItems.value = all.filter((i: any) => i.status === 'approved')
    rejectedItems.value = all.filter((i: any) => i.status === 'rejected')
    approvedCount.value = approvedItems.value.length
    rejectedCount.value = rejectedItems.value.length
  } catch {
    try {
      const res2 = await http<any>('/api/v1/coach-push/pending?page_size=50')
      pendingItems.value = (res2.items || []).map((i: any) => ({ ...i, _expanded: false, _done: '' }))
    } catch { pendingItems.value = [] }
  }

  // 今日统计补充
  try {
    const res = await http<any>('/api/v1/coach/stats/today')
    if (res.approved) approvedCount.value = res.approved
    if (res.rejected) rejectedCount.value = res.rejected
  } catch (e) { console.warn('[coach/flywheel/index] today stats:', e) }

  // 学员列表（按风险降序，高风险优先）
  try {
    const res = await http<any>('/api/v1/coach/dashboard')
    studentList.value = (res.students || [])
      .map((s: any) => ({
        id: s.id || s.user_id,
        name: s.name || s.full_name || '未知',
        stage_label: s.stage_label || s.stage || '',
        day_index: s.day_index,
        risk_level: typeof s.risk_level === 'string'
          ? parseInt(s.risk_level.replace(/\D/g, '')) || 0
          : (s.risk_level || 0),
      }))
      .sort((a: any, b: any) => b.risk_level - a.risk_level) // 高风险排前
  } catch { studentList.value = [] }
}

async function approveItem(item: any) {
  try {
    await http(`/api/v1/coach/review/${item.id}/approve`, { method: 'POST' })
  } catch {
    try { await http(`/api/v1/coach-push/${item.id}/approve`, { method: 'POST' }) }
    catch (e) { console.warn('[coach/flywheel/index] approveItem:', e) }
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
    await http(`/api/v1/coach/review/${rejectModal.value.id}/reject`, {
      method: 'POST', data: { reason: rejectReason.value },
    })
  } catch {
    try {
      await http(`/api/v1/coach-push/${rejectModal.value.id}/reject`, {
        method: 'POST', data: { reason: rejectReason.value },
      })
    } catch (e) { console.warn('[coach/flywheel/index] doReject:', e) }
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
      },
    })
    const d = res.data || res
    if (Array.isArray(d.suggestions) && d.suggestions.length) {
      agentResult.value = d.suggestions
        .sort((a: any, b: any) => (b.priority ?? 0) - (a.priority ?? 0))
        .map((s: any, i: number) => `${i + 1}. ${s.text || s.content || ''}`)
        .filter(Boolean)
        .join('\n\n')
    } else {
      agentResult.value = d.output || d.text || d.result || d.content || '暂无跟进建议'
    }
  } catch (e: any) {
    agentResult.value = '生成失败: ' + (e.message || '请重试')
  }
  generating.value = false
}

function regenFromRejected(item: any) {
  // 从已退回界面快速跳转到AI跟进并预选该学员
  const student = studentList.value.find(s => s.id === item.student_id || s.name === item.student_name)
  if (student) selectedStudent.value = student
  activeTab.value = 'generate'
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
function refresh() { loadData() }

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onLoad(() => { loadData() })
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

.fw-stattabs { display: flex; padding: 0 24rpx 16rpx; gap: 12rpx; }
.fw-st { flex: 1; background: #fff; border-radius: 14rpx; padding: 18rpx 8rpx 14rpx; text-align: center; }
.fw-st--active { background: #27AE60; }
.fw-st-num { display: block; font-size: 36rpx; font-weight: 700; color: #2C3E50; }
.fw-st--active .fw-st-num { color: #fff; }
.fw-st-label { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.fw-st--active .fw-st-label { color: rgba(255,255,255,0.85); }

/* 搜索+筛选区（固定，不滚动） */
.fw-search-area { padding: 0 24rpx 12rpx; }
.fw-search-row { display: flex; align-items: center; gap: 12rpx; margin-bottom: 12rpx; }
.fw-search-input { flex: 1; background: #fff; border-radius: 12rpx; padding: 14rpx 20rpx; font-size: 26rpx; color: #2C3E50; }
.fw-search-count { font-size: 22rpx; color: #8E99A4; white-space: nowrap; }
.fw-risk-chips { display: flex; gap: 10rpx; }
.fw-risk-chip { padding: 10rpx 20rpx; background: #fff; border-radius: 20rpx; font-size: 24rpx; color: #5B6B7F; }
.fw-risk-chip--active { background: #27AE60; color: #fff; }

/* 主列表区 */
.fw-list { height: calc(100vh - 560rpx); padding: 0 24rpx; }
.fw-list--with-bar { height: calc(100vh - 560rpx - 200rpx); }

/* 今日重点区 */
.fw-priority-section { background: #fff; border-radius: 16rpx; padding: 20rpx; margin-bottom: 12rpx; }
.fw-section-label { display: block; font-size: 22rpx; color: #8E99A4; font-weight: 500; letter-spacing: 1rpx; margin-bottom: 12rpx; }
.fw-section-label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8rpx; }
.fw-section-count { font-size: 22rpx; color: #BDC3C7; }
.fw-priority-row { display: flex; gap: 12rpx; }
.fw-priority-card { flex: 1; background: #F8F9FA; border-radius: 14rpx; padding: 16rpx 12rpx; text-align: center; border: 2rpx solid transparent; }
.fw-priority-card--active { background: #F0FFF8; border-color: #27AE60; }
.fw-priority-avatar { width: 56rpx; height: 56rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 700; margin: 0 auto 8rpx; }
.fw-priority-name { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; }
.fw-priority-risk { display: block; font-size: 22rpx; font-weight: 600; margin-top: 4rpx; }

/* 学员列表 */
.fw-student-list { display: flex; flex-direction: column; gap: 8rpx; margin-bottom: 16rpx; }
.fw-student-row { display: flex; align-items: center; gap: 16rpx; padding: 16rpx; background: #fff; border-radius: 14rpx; border: 2rpx solid transparent; }
.fw-student-row--active { background: #F0FFF8; border-color: #27AE60; }
.fw-student-avatar { width: 64rpx; height: 64rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 26rpx; font-weight: 600; flex-shrink: 0; }
.fw-student-info { flex: 1; }
.fw-student-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.fw-student-sub { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.fw-student-risk { padding: 4rpx 10rpx; border-radius: 8rpx; font-size: 22rpx; font-weight: 600; color: #2C3E50; }
.fw-student-check { font-size: 32rpx; color: #27AE60; font-weight: 700; }
.fw-student-empty { text-align: center; padding: 40rpx 0; font-size: 26rpx; color: #8E99A4; }

/* AI结果 */
.fw-gen-result { background: #F0FFF0; border-radius: 12rpx; padding: 20rpx; border-left: 4rpx solid #27AE60; margin-bottom: 16rpx; }
.fw-gen-result-header { display: flex; align-items: center; margin-bottom: 10rpx; }
.fw-gen-result-title { font-size: 26rpx; font-weight: 600; color: #27AE60; flex: 1; }
.fw-gen-result-text { font-size: 26rpx; color: #2C3E50; line-height: 1.7; }
.fw-gen-result-hint { font-size: 22rpx; color: #8E99A4; margin-top: 12rpx; }

/* 审核卡片 */
.fw-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 12rpx; }
.fw-card--done { opacity: 0.6; }
.fw-card-header { display: flex; align-items: center; justify-content: space-between; }
.fw-card-student { font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.fw-card-type { padding: 4rpx 12rpx; border-radius: 6rpx; color: #fff; font-size: 22rpx; }
.fw-card-time { font-size: 22rpx; color: #8E99A4; }
.fw-card-summary { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 12rpx; }
.fw-card-draft { background: #F8F9FA; border-radius: 12rpx; padding: 16rpx; margin-top: 12rpx; }
.fw-card-draft-text { font-size: 26rpx; color: #2C3E50; line-height: 1.6; }
.fw-card-toggle { text-align: center; font-size: 24rpx; color: #3498DB; margin-top: 8rpx; padding: 8rpx; }
.fw-card-actions { display: flex; gap: 16rpx; margin-top: 16rpx; }
.fw-btn { flex: 1; text-align: center; padding: 16rpx 0; border-radius: 10rpx; font-size: 28rpx; font-weight: 600; }
.fw-btn--approve { background: #27AE60; color: #fff; }
.fw-btn--reject { background: #FFF5F5; color: #E74C3C; border: 1rpx solid #E74C3C; }
.fw-btn--regen { background: #EBF5FB; color: #3498DB; border: 1rpx solid #3498DB; text-align: center; padding: 16rpx 0; border-radius: 10rpx; font-size: 28rpx; font-weight: 600; margin-top: 12rpx; }
.fw-card-done-label { text-align: center; margin-top: 12rpx; font-size: 26rpx; font-weight: 600; }
.fw-card-reject-reason { background: #FFF8F0; border-radius: 10rpx; padding: 12rpx; margin-top: 10rpx; }
.fw-card-reject-label { font-size: 22rpx; color: #E67E22; font-weight: 600; }
.fw-card-reject-text { font-size: 24rpx; color: #5B6B7F; }

/* 固定底部操作栏 — 生成按钮永远可见 */
.fw-fixed-bar {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: #fff;
  padding: 16rpx 24rpx calc(24rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -4rpx 20rpx rgba(0,0,0,0.08);
  z-index: 100;
}
.fw-fixed-student { display: flex; align-items: center; gap: 12rpx; margin-bottom: 12rpx; }
.fw-fixed-avatar { width: 48rpx; height: 48rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22rpx; font-weight: 700; flex-shrink: 0; }
.fw-fixed-info { flex: 1; }
.fw-fixed-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.fw-fixed-stage { display: block; font-size: 22rpx; color: #8E99A4; }
.fw-fixed-risk { font-size: 28rpx; font-weight: 700; }
.fw-fixed-clear { font-size: 28rpx; color: #BDC3C7; padding: 8rpx; }
.fw-fixed-prompt { margin-bottom: 12rpx; }
.fw-fixed-input { width: 100%; background: #F5F6FA; border-radius: 10rpx; padding: 12rpx 16rpx; font-size: 26rpx; box-sizing: border-box; }
.fw-fixed-btn { text-align: center; padding: 20rpx; background: #27AE60; color: #fff; border-radius: 14rpx; font-size: 30rpx; font-weight: 600; }
.fw-fixed-btn--loading { opacity: 0.6; }

.fw-empty { text-align: center; padding: 100rpx 0; }
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
