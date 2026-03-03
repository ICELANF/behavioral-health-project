<template>
  <view class="fw-page">
    <view class="fw-navbar">
      <view class="fw-nav-back" @tap="goBack">←</view>
      <text class="fw-nav-title">AI 飞轮</text>
      <view class="fw-nav-action" @tap="refresh">↻</view>
    </view>

    <!-- 飞轮5步骤 — 每步可点击，高亮跟随当前内容 -->
    <view class="fw-wheel">
      <view v-for="(step, i) in wheelSteps" :key="i"
        class="fw-wheel-step" :class="{ 'fw-wheel-step--active': activeWheelStep === i }"
        @tap="gotoStep(i)">
        <text class="fw-wheel-icon">{{ step.icon }}</text>
        <text class="fw-wheel-label">{{ step.label }}</text>
        <view v-if="i < wheelSteps.length - 1" class="fw-wheel-arrow">›</view>
      </view>
    </view>

    <!-- 步骤说明条（当前激活步骤的一句话说明） -->
    <view class="fw-step-desc">
      <text class="fw-step-desc-text">{{ wheelSteps[activeWheelStep]?.desc }}</text>
    </view>

    <!-- Tab 统计栏（内容随步骤变化） -->
    <view class="fw-stattabs">
      <!-- 数据采集步骤：显示数据统计 -->
      <template v-if="activeWheelStep === 0">
        <view class="fw-st fw-st--active">
          <text class="fw-st-num">{{ dataItems.length }}</text>
          <text class="fw-st-label">待查看</text>
        </view>
        <view class="fw-st">
          <text class="fw-st-num" style="color:#E74C3C;">{{ dataItems.filter(d=>d.is_abnormal).length }}</text>
          <text class="fw-st-label">异常数据</text>
        </view>
        <view class="fw-st">
          <text class="fw-st-num" style="color:#27AE60;">{{ dataItems.filter(d=>!d.is_abnormal).length }}</text>
          <text class="fw-st-label">正常数据</text>
        </view>
        <view class="fw-st" @tap="gotoStep(1)">
          <text class="fw-st-num">→</text>
          <text class="fw-st-label">去AI分析</text>
        </view>
      </template>
      <!-- AI分析/教练审核步骤：显示审核统计 -->
      <template v-else-if="activeWheelStep === 1 || activeWheelStep === 2">
        <view class="fw-st" :class="{ 'fw-st--active': activeTab === 'generate' }" @tap="activeTab = 'generate'">
          <text class="fw-st-num">{{ studentList.length }}</text>
          <text class="fw-st-label">AI跟进</text>
        </view>
        <view class="fw-st" :class="{ 'fw-st--active': activeTab === 'pending' }" @tap="activeTab = 'pending'">
          <text class="fw-st-num" :style="{ color: activeTab==='pending' ? '#fff' : '#E67E22' }">{{ pendingItems.filter(i=>!i._done).length }}</text>
          <text class="fw-st-label">待审核</text>
        </view>
        <view class="fw-st" :class="{ 'fw-st--active': activeTab === 'approved' }" @tap="activeTab = 'approved'">
          <text class="fw-st-num" :style="{ color: activeTab==='approved' ? '#fff' : '#27AE60' }">{{ approvedCount }}</text>
          <text class="fw-st-label">已通过</text>
        </view>
        <view class="fw-st" :class="{ 'fw-st--active': activeTab === 'rejected' }" @tap="activeTab = 'rejected'">
          <text class="fw-st-num" :style="{ color: activeTab==='rejected' ? '#fff' : '#E74C3C' }">{{ rejectedCount }}</text>
          <text class="fw-st-label">已退回</text>
        </view>
      </template>
      <!-- 推送执行步骤 -->
      <template v-else-if="activeWheelStep === 3">
        <view class="fw-st fw-st--active">
          <text class="fw-st-num">{{ pushItems.length }}</text>
          <text class="fw-st-label">已推送</text>
        </view>
        <view class="fw-st">
          <text class="fw-st-num" style="color:#27AE60;">{{ pushItems.filter(p=>p.read_at).length }}</text>
          <text class="fw-st-label">已读取</text>
        </view>
        <view class="fw-st">
          <text class="fw-st-num" style="color:#E67E22;">{{ pushItems.filter(p=>!p.read_at).length }}</text>
          <text class="fw-st-label">未读</text>
        </view>
        <view class="fw-st" @tap="gotoStep(4)">
          <text class="fw-st-num">→</text>
          <text class="fw-st-label">效果追踪</text>
        </view>
      </template>
      <!-- 效果追踪步骤 -->
      <template v-else-if="activeWheelStep === 4">
        <view class="fw-st fw-st--active">
          <text class="fw-st-num">{{ studentList.length }}</text>
          <text class="fw-st-label">追踪学员</text>
        </view>
        <view class="fw-st">
          <text class="fw-st-num" style="color:#27AE60;">—</text>
          <text class="fw-st-label">平均依从率</text>
        </view>
        <view class="fw-st">
          <text class="fw-st-num" style="color:#3498DB;">—</text>
          <text class="fw-st-label">数据好转</text>
        </view>
        <view class="fw-st" @tap="gotoStep(0)">
          <text class="fw-st-num">↺</text>
          <text class="fw-st-label">重新采集</text>
        </view>
      </template>
    </view>

    <!-- AI跟进：固定搜索栏（不随列表滚动） -->
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

      <!-- 步骤0：数据采集 -->
      <template v-if="activeWheelStep === 0">
        <view v-for="item in dataItems" :key="item.id" class="fw-card">
          <view class="fw-card-header">
            <text class="fw-card-student">{{ item.student_name || '学员' }}</text>
            <view class="fw-data-badge" :style="{ background: item.is_abnormal ? '#FDEDEC' : '#EAFAF1', color: item.is_abnormal ? '#E74C3C' : '#27AE60' }">
              {{ item.is_abnormal ? '⚠ 异常' : '✓ 正常' }}
            </view>
          </view>
          <text class="fw-card-summary">{{ item.summary || item.description || '健康数据上报' }}</text>
          <view class="fw-card-data-row" v-if="item.data_type">
            <text class="fw-data-type-label">数据类型：</text>
            <text class="fw-data-type-val">{{ dataTypeLabel(item.data_type) }}</text>
          </view>
          <text class="fw-card-time" style="margin-top:8rpx;">{{ item.created_at ? item.created_at.slice(0,16) : '' }}</text>
          <view class="fw-card-actions" style="margin-top:12rpx;">
            <view class="fw-btn fw-btn--approve" @tap="selectStudentAndAnalyze(item)">→ AI分析此学员</view>
          </view>
        </view>
        <view v-if="dataItems.length === 0" class="fw-empty">
          <text class="fw-empty-icon">📊</text>
          <text class="fw-empty-text">暂无待查看的健康数据上报</text>
        </view>
      </template>

      <!-- 步骤1/2：AI跟进 Tab -->
      <template v-if="(activeWheelStep === 1 || activeWheelStep === 2) && activeTab === 'generate'">
        <!-- 今日重点：AI推荐高风险学员 -->
        <view v-if="priorityStudents.length > 0 && !searchText" class="fw-priority-section">
          <text class="fw-section-label">今日重点 — 建议优先跟进</text>
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
        <view v-if="agentResult" class="fw-gen-result">
          <view class="fw-gen-result-header">
            <text class="fw-gen-result-title">AI 跟进建议 — {{ selectedStudent?.name }}</text>
          </view>
          <text class="fw-gen-result-text">{{ agentResult }}</text>
          <view class="fw-gen-result-hint">已自动进入待审核队列</view>
        </view>
        <view style="height:160rpx;"></view>
      </template>

      <!-- 步骤1/2：待审核 Tab -->
      <template v-if="(activeWheelStep === 1 || activeWheelStep === 2) && activeTab === 'pending'">
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

      <!-- 步骤1/2：已通过 Tab -->
      <template v-if="(activeWheelStep === 1 || activeWheelStep === 2) && activeTab === 'approved'">
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

      <!-- 步骤1/2：已退回 Tab -->
      <template v-if="(activeWheelStep === 1 || activeWheelStep === 2) && activeTab === 'rejected'">
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

      <!-- 步骤3：推送执行 -->
      <template v-if="activeWheelStep === 3">
        <view v-for="item in pushItems" :key="item.id" class="fw-card">
          <view class="fw-card-header">
            <text class="fw-card-student">{{ item.student_name || item.receiver_name || '学员' }}</text>
            <view class="fw-push-status" :style="{ background: item.read_at ? '#EAFAF1' : '#FEF9E7', color: item.read_at ? '#27AE60' : '#E67E22' }">
              {{ item.read_at ? '已读取' : '未读' }}
            </view>
          </view>
          <text class="fw-card-summary">{{ item.content || item.summary || '推送内容' }}</text>
          <text class="fw-card-time" style="margin-top:8rpx;">
            推送时间：{{ item.pushed_at ? item.pushed_at.slice(0,16) : item.created_at ? item.created_at.slice(0,16) : '—' }}
          </text>
        </view>
        <view v-if="pushItems.length === 0" class="fw-empty">
          <text class="fw-empty-icon">📤</text>
          <text class="fw-empty-text">暂无推送记录</text>
        </view>
      </template>

      <!-- 步骤4：效果追踪（跳转提示） -->
      <template v-if="activeWheelStep === 4">
        <view class="fw-track-intro">
          <view class="fw-track-icon">📈</view>
          <text class="fw-track-title">效果追踪</text>
          <text class="fw-track-desc">查看各学员接收处方后的健康数据变化、依从率及行为改善情况</text>
          <view class="fw-track-btn" @tap="goToAnalytics">前往学员数据分析 →</view>
        </view>
        <view class="fw-card" v-for="s in studentList.slice(0,5)" :key="s.id">
          <view class="fw-card-header">
            <text class="fw-card-student">{{ s.name }}</text>
            <view class="fw-student-risk" :style="{ background: riskBg(s.risk_level) }">R{{ s.risk_level }}</view>
          </view>
          <text class="fw-card-summary">{{ s.stage_label || '进行中' }} · Day {{ s.day_index || '—' }}</text>
          <view class="fw-btn fw-btn--detail" @tap="goToStudentDetail(s.id)">查看个人数据 →</view>
        </view>
      </template>
    </scroll-view>

    <!-- 固定底部操作栏 — 仅 AI跟进 Tab 且已选学员时显示 -->
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

// 当前激活的内容Tab（generate/pending/approved/rejected）
const activeTab = ref('pending')
const refreshing = ref(false)
const pendingItems = ref<any[]>([])
const approvedItems = ref<any[]>([])
const rejectedItems = ref<any[]>([])
const dataItems = ref<any[]>([])    // 步骤0: 数据采集
const pushItems = ref<any[]>([])    // 步骤3: 推送执行
const studentList = ref<any[]>([])
const selectedStudent = ref<any>(null)
const customPrompt = ref('')
const generating = ref(false)
const agentResult = ref('')
const rejectModal = ref<any>(null)
const rejectReason = ref('')
const approvedCount = ref(0)
const rejectedCount = ref(0)

// 搜索与筛选
const searchText = ref('')
const riskFilter = ref('all')

const riskFilters = [
  { key: 'all', label: '全部' },
  { key: '3', label: 'R3 高危' },
  { key: '2', label: 'R2 中危' },
  { key: '1', label: 'R1 低危' },
]

// activeWheelStep 从 activeTab 和步骤状态计算，保持高亮与内容同步
const activeWheelStep = computed(() => {
  const map: Record<string, number> = { data: 0, generate: 1, pending: 2, approved: 2, rejected: 2, push: 3, track: 4 }
  return map[activeTab.value] ?? 2
})

const wheelSteps = [
  { icon: '📊', label: '数据采集', desc: '查看学员健康数据上报，发现异常及时干预' },
  { icon: '🤖', label: 'AI分析',  desc: '选择学员，AI基于行为数据生成个性化跟进方案' },
  { icon: '👨‍⚕️', label: '教练审核', desc: '审核AI草稿：通过即推送给学员，退回则重新生成' },
  { icon: '📤', label: '推送执行', desc: '查看已推送给学员的内容及学员读取状态' },
  { icon: '📈', label: '效果追踪', desc: '对比处方前后数据变化，评估干预效果与依从率' },
]

// 飞轮步骤点击 — 每步对应明确内容
function gotoStep(i: number) {
  const tabMap: Record<number, string> = {
    0: 'data',
    1: 'generate',
    2: 'pending',
    3: 'push',
    4: 'track',
  }
  activeTab.value = tabMap[i] ?? 'pending'
}

// 从数据采集直接跳到AI分析并预选学员
function selectStudentAndAnalyze(dataItem: any) {
  const s = studentList.value.find(s => s.id === dataItem.student_id || s.name === dataItem.student_name)
  if (s) selectedStudent.value = s
  activeTab.value = 'generate'
}

function goToAnalytics() {
  uni.navigateTo({ url: '/pages/coach/analytics/index' })
}

function goToStudentDetail(id: number) {
  uni.navigateTo({ url: '/pages/coach/students/detail?id=' + id })
}

const filteredStudents = computed(() => {
  let list = studentList.value
  if (riskFilter.value !== 'all') {
    list = list.filter(s => s.risk_level === parseInt(riskFilter.value))
  }
  if (searchText.value.trim()) {
    list = list.filter(s => s.name.includes(searchText.value.trim()))
  }
  return list
})

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
function dataTypeLabel(t: string): string {
  const map: Record<string, string> = { blood_glucose: '血糖', weight: '体重', exercise: '运动', food: '饮食', sleep: '睡眠', mood: '情绪' }
  return map[t] || t
}

async function loadData() {
  // 步骤0：数据采集 — 健康审核队列（教练侧中风险）
  try {
    const res = await http<any>('/api/v1/health-review/queue?reviewer_role=coach')
    dataItems.value = res.items || res.queue || []
  } catch { dataItems.value = [] }

  // 步骤2：审核队列
  try {
    const res = await http<any>('/api/v1/coach/review-queue')
    const all = res.items || res.queue || (Array.isArray(res) ? res : [])
    pendingItems.value = all
      .filter((i: any) => !['approved', 'rejected'].includes(i.status))
      .map((i: any) => ({ ...i, _expanded: false, _done: '' }))
    approvedItems.value = all.filter((i: any) => i.status === 'approved')
    rejectedItems.value = all.filter((i: any) => i.status === 'rejected')
    approvedCount.value = approvedItems.value.length
    rejectedCount.value = rejectedItems.value.length
  } catch {
    try {
      const r2 = await http<any>('/api/v1/coach-push/pending?page_size=50')
      pendingItems.value = (r2.items || []).map((i: any) => ({ ...i, _expanded: false, _done: '' }))
    } catch { pendingItems.value = [] }
  }

  // 步骤2：今日统计补充
  try {
    const res = await http<any>('/api/v1/coach/stats/today')
    if (res.approved) approvedCount.value = res.approved
    if (res.rejected) rejectedCount.value = res.rejected
  } catch (e) { console.warn('[flywheel] today stats:', e) }

  // 步骤3：推送执行历史（使用已通过的审核记录替代）
  pushItems.value = approvedItems.value

  // 学员列表（按风险降序）
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
      .sort((a: any, b: any) => b.risk_level - a.risk_level)
  } catch { studentList.value = [] }
}

async function approveItem(item: any) {
  try {
    await http(`/api/v1/coach/review/${item.id}/approve`, { method: 'POST' })
  } catch {
    try { await http(`/api/v1/coach-push/${item.id}/approve`, { method: 'POST' }) }
    catch (e) { console.warn('[flywheel] approveItem:', e) }
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
    } catch (e) { console.warn('[flywheel] doReject:', e) }
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
  const s = studentList.value.find(s => s.id === item.student_id || s.name === item.student_name)
  if (s) selectedStudent.value = s
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

/* 飞轮5步骤 — 可点击 */
.fw-wheel { display: flex; align-items: center; padding: 16rpx 16rpx 12rpx; gap: 0; }
.fw-wheel-step { flex: 1; text-align: center; padding: 12rpx 4rpx; border-radius: 12rpx; background: #fff; position: relative; }
.fw-wheel-step--active { background: #27AE60; }
.fw-wheel-step--active .fw-wheel-label { color: #fff; }
.fw-wheel-arrow { position: absolute; right: -8rpx; top: 50%; transform: translateY(-50%); font-size: 20rpx; color: #BDC3C7; z-index: 1; }
.fw-wheel-icon { display: block; font-size: 28rpx; }
.fw-wheel-label { display: block; font-size: 18rpx; color: #5B6B7F; margin-top: 4rpx; }

/* 步骤说明条 */
.fw-step-desc { padding: 0 24rpx 10rpx; }
.fw-step-desc-text { font-size: 22rpx; color: #8E99A4; display: block; text-align: center; }

/* 统计+Tab 单排 */
.fw-stattabs { display: flex; padding: 0 24rpx 12rpx; gap: 10rpx; }
.fw-st { flex: 1; background: #fff; border-radius: 14rpx; padding: 14rpx 6rpx 12rpx; text-align: center; }
.fw-st--active { background: #27AE60; }
.fw-st-num { display: block; font-size: 34rpx; font-weight: 700; color: #2C3E50; }
.fw-st--active .fw-st-num { color: #fff; }
.fw-st-label { display: block; font-size: 19rpx; color: #8E99A4; margin-top: 4rpx; }
.fw-st--active .fw-st-label { color: rgba(255,255,255,0.85); }

/* 搜索+筛选区 */
.fw-search-area { padding: 0 24rpx 12rpx; }
.fw-search-row { display: flex; align-items: center; gap: 12rpx; margin-bottom: 10rpx; }
.fw-search-input { flex: 1; background: #fff; border-radius: 12rpx; padding: 14rpx 20rpx; font-size: 26rpx; color: #2C3E50; }
.fw-search-count { font-size: 22rpx; color: #8E99A4; white-space: nowrap; }
.fw-risk-chips { display: flex; gap: 10rpx; }
.fw-risk-chip { padding: 10rpx 20rpx; background: #fff; border-radius: 20rpx; font-size: 24rpx; color: #5B6B7F; }
.fw-risk-chip--active { background: #27AE60; color: #fff; }

/* 主列表 */
.fw-list { height: calc(100vh - 580rpx); padding: 0 24rpx; }
.fw-list--with-bar { height: calc(100vh - 580rpx - 200rpx); }

/* 今日重点 */
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
.fw-gen-result-header { margin-bottom: 10rpx; }
.fw-gen-result-title { font-size: 26rpx; font-weight: 600; color: #27AE60; }
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
.fw-btn { text-align: center; padding: 16rpx 0; border-radius: 10rpx; font-size: 28rpx; font-weight: 600; }
.fw-btn--approve { flex: 1; background: #27AE60; color: #fff; }
.fw-btn--reject { flex: 1; background: #FFF5F5; color: #E74C3C; border: 1rpx solid #E74C3C; }
.fw-btn--regen { display: block; background: #EBF5FB; color: #3498DB; border: 1rpx solid #3498DB; margin-top: 12rpx; }
.fw-btn--detail { display: block; background: #F8F9FA; color: #5B6B7F; margin-top: 12rpx; }
.fw-card-done-label { text-align: center; margin-top: 12rpx; font-size: 26rpx; font-weight: 600; }
.fw-card-reject-reason { background: #FFF8F0; border-radius: 10rpx; padding: 12rpx; margin-top: 10rpx; }
.fw-card-reject-label { font-size: 22rpx; color: #E67E22; font-weight: 600; }
.fw-card-reject-text { font-size: 24rpx; color: #5B6B7F; }

/* 数据采集 */
.fw-data-badge { padding: 4rpx 12rpx; border-radius: 8rpx; font-size: 22rpx; font-weight: 600; }
.fw-card-data-row { display: flex; align-items: center; margin-top: 8rpx; }
.fw-data-type-label { font-size: 22rpx; color: #8E99A4; }
.fw-data-type-val { font-size: 22rpx; color: #2C3E50; font-weight: 600; }

/* 推送执行 */
.fw-push-status { padding: 4rpx 12rpx; border-radius: 8rpx; font-size: 22rpx; font-weight: 600; }

/* 效果追踪 */
.fw-track-intro { text-align: center; padding: 40rpx 32rpx; background: #fff; border-radius: 16rpx; margin-bottom: 16rpx; }
.fw-track-icon { font-size: 80rpx; display: block; margin-bottom: 16rpx; }
.fw-track-title { display: block; font-size: 34rpx; font-weight: 700; color: #2C3E50; margin-bottom: 12rpx; }
.fw-track-desc { display: block; font-size: 26rpx; color: #8E99A4; line-height: 1.6; margin-bottom: 24rpx; }
.fw-track-btn { background: #27AE60; color: #fff; padding: 20rpx 40rpx; border-radius: 14rpx; font-size: 28rpx; font-weight: 600; display: inline-block; }

/* 固定底部操作栏 */
.fw-fixed-bar { position: fixed; bottom: 0; left: 0; right: 0; background: #fff; padding: 16rpx 24rpx calc(24rpx + env(safe-area-inset-bottom)); box-shadow: 0 -4rpx 20rpx rgba(0,0,0,0.08); z-index: 100; }
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
