<template>
  <view class="detail-page">
    <view class="detail-navbar">
      <view class="detail-nav-back" @tap="goBack">←</view>
      <text class="detail-nav-title">{{ student.name || '学员档案' }}</text>
      <view class="detail-nav-action" @tap="refresh">↻</view>
    </view>

    <scroll-view scroll-y class="detail-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <!-- 基本信息 -->
      <view class="detail-profile">
        <view class="detail-avatar" :style="{ background: riskColor(student.risk_level) }">
          {{ (student.name || '?')[0] }}
        </view>
        <view class="detail-profile-info">
          <text class="detail-profile-name">{{ student.name }}</text>
          <text class="detail-profile-stage">{{ student.stage || '未评估' }} · Day {{ student.day_index || '—' }}</text>
        </view>
        <view class="detail-risk-badge" :style="{ background: riskColor(student.risk_level) }">
          风险 R{{ student.risk_level || 0 }}
        </view>
      </view>

      <!-- 快速操作 — 全部直接针对此学员，无需二次筛选 -->
      <view class="detail-actions">
        <view class="detail-act-btn" @tap="sendMessage">
          <text class="detail-act-icon">💬</text>
          <text class="detail-act-label">发消息</text>
        </view>
        <view class="detail-act-btn" @tap="openAssignModal">
          <text class="detail-act-icon">📋</text>
          <text class="detail-act-label">分配评估</text>
        </view>
        <view class="detail-act-btn" @tap="openRxModal">
          <text class="detail-act-icon">📝</text>
          <text class="detail-act-label">开处方</text>
        </view>
        <view class="detail-act-btn" @tap="activeTab = 'health'">
          <text class="detail-act-icon">📊</text>
          <text class="detail-act-label">数据</text>
        </view>
      </view>

      <!-- Tab切换 -->
      <view class="detail-tabs">
        <view v-for="t in detailTabs" :key="t.key" class="detail-tab"
          :class="{ 'detail-tab--active': activeTab === t.key }" @tap="activeTab = t.key">
          {{ t.label }}
        </view>
      </view>

      <!-- Loading 指示器 -->
      <view v-if="dataLoading" class="detail-loading">
        <text class="detail-loading-text">加载中...</text>
      </view>

      <!-- 概览 Tab -->
      <template v-if="!dataLoading && activeTab === 'overview'">
        <view class="detail-card">
          <text class="detail-card-title">健康指标</text>
          <view class="detail-metric-grid">
            <view v-for="m in healthMetrics" :key="m.label" class="detail-metric">
              <text class="detail-metric-val" :style="{ color: m.color }">{{ m.value }}</text>
              <text class="detail-metric-label">{{ m.label }}</text>
            </view>
          </view>
        </view>
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

      <!-- 行为记录 Tab — 仅此学员的行为数据 -->
      <template v-if="!dataLoading && activeTab === 'behavior'">
        <view class="detail-card" v-for="(log, idx) in behaviorLogs" :key="idx">
          <view class="detail-log-header">
            <text class="detail-log-type" :style="{ color: logColor(log.type) }">{{ log.type_label }}</text>
            <text class="detail-log-time">{{ log.time }}</text>
          </view>
          <text class="detail-log-content">{{ log.content }}</text>
        </view>
        <view v-if="behaviorLogs.length === 0" class="detail-empty">暂无行为记录</view>
      </template>

      <!-- 督导记录 Tab — 仅此学员的督导互动 -->
      <template v-if="!dataLoading && activeTab === 'supervision'">
        <view class="detail-card" v-for="(note, idx) in supervisionNotes" :key="idx">
          <view class="detail-note-header">
            <text class="detail-note-date">{{ note.date }}</text>
            <text class="detail-note-author">{{ note.author || '教练' }}</text>
          </view>
          <text class="detail-note-content">{{ note.content }}</text>
        </view>
        <view v-if="supervisionNotes.length === 0" class="detail-empty">暂无督导记录</view>
        <view class="detail-add-note">
          <textarea class="detail-note-input" placeholder="添加督导笔记..." v-model="newNote" />
          <view class="detail-note-submit" @tap="submitNote">提交</view>
        </view>
      </template>

      <!-- 健康数据 Tab — 此学员个人各类生理数据汇总 -->
      <template v-if="!dataLoading && activeTab === 'health'">
        <view class="detail-card">
          <text class="detail-card-title">个人健康数据</text>
          <view class="health-stat-grid">
            <view class="health-stat">
              <text class="health-stat-val" :style="{ color: glucoseColor(healthData.fasting_glucose) }">
                {{ healthData.fasting_glucose != null ? healthData.fasting_glucose : '—' }}
              </text>
              <text class="health-stat-unit">mmol/L</text>
              <text class="health-stat-label">空腹血糖</text>
            </view>
            <view class="health-stat">
              <text class="health-stat-val" style="color:#3498DB">
                {{ healthData.weight != null ? healthData.weight : '—' }}
              </text>
              <text class="health-stat-unit">kg</text>
              <text class="health-stat-label">体重</text>
            </view>
            <view class="health-stat">
              <text class="health-stat-val" style="color:#27AE60">
                {{ healthData.exercise_minutes != null ? healthData.exercise_minutes : '—' }}
              </text>
              <text class="health-stat-unit">分钟</text>
              <text class="health-stat-label">今日运动</text>
            </view>
            <view class="health-stat">
              <text class="health-stat-val" style="color:#9B59B6">
                {{ healthData.sleep_hours != null ? healthData.sleep_hours : '—' }}
              </text>
              <text class="health-stat-unit">小时</text>
              <text class="health-stat-label">睡眠时长</text>
            </view>
          </view>
        </view>

        <!-- 血糖趋势 -->
        <view class="detail-card" v-if="glucoseTrend.length > 0">
          <text class="detail-card-title">血糖趋势（近7天）</text>
          <view class="trend-bars">
            <view v-for="(p, i) in glucoseTrend" :key="i" class="trend-bar-col">
              <text class="trend-bar-top">{{ p.val }}</text>
              <view class="trend-bar" :style="{ height: p.height + 'rpx', background: glucoseColor(p.val) }"></view>
              <text class="trend-bar-label">{{ p.label }}</text>
            </view>
          </view>
        </view>

        <!-- 体重趋势 -->
        <view class="detail-card" v-if="weightTrend.length > 0">
          <text class="detail-card-title">体重趋势（近7天）</text>
          <view class="trend-bars">
            <view v-for="(p, i) in weightTrend" :key="i" class="trend-bar-col">
              <text class="trend-bar-top">{{ p.val }}</text>
              <view class="trend-bar" :style="{ height: p.height + 'rpx', background: '#3498DB' }"></view>
              <text class="trend-bar-label">{{ p.label }}</text>
            </view>
          </view>
        </view>

        <!-- 微行动完成（复用概览数据）-->
        <view class="detail-card">
          <text class="detail-card-title">近7天微行动完成</text>
          <view class="detail-action-bars">
            <view v-for="(d, i) in weekActions" :key="i" class="detail-action-bar-col">
              <view class="detail-action-bar" :style="{ height: d.height + 'rpx', background: d.completed ? '#27AE60' : '#E8E8E8' }"></view>
              <text class="detail-action-bar-label">{{ d.label }}</text>
            </view>
          </view>
        </view>

        <view v-if="!healthData.fasting_glucose && !healthData.weight && !healthData.exercise_minutes" class="detail-empty">
          学员暂未上报健康数据
        </view>
      </template>

      <view style="height:60rpx;"></view>
    </scroll-view>
  </view>

  <!-- 发消息 Modal -->
  <view v-if="showMsgModal" class="modal-mask" @tap="closeMsgModal">
    <view class="modal-sheet" @tap.stop>
      <view class="modal-title">发消息 — {{ student.name }}</view>

      <!-- AI 建议区 -->
      <view class="modal-field">
        <view class="ai-bar">
          <text class="modal-label" style="margin-bottom:0">消息内容</text>
          <view class="ai-btn" :class="{ 'ai-btn--loading': msgAiLoading }" @tap="loadAiMessage">
            {{ msgAiLoading ? '生成中…' : '🤖 AI建议' }}
          </view>
        </view>
        <textarea class="modal-textarea" v-model="msgContent" placeholder="输入消息，或点击右上角 AI建议 自动生成…" />
        <!-- AI 内容展示区（持久显示直到关闭） -->
        <view v-if="msgAiInfo.rationale" class="ai-suggestion-box">
          <view class="ai-sug-header">
            <text class="ai-sug-tag">✨ AI建议（{{ msgAiInfo.source === 'llm' ? '大模型' : '规则引擎' }}，可信度 {{ Math.round((msgAiInfo.confidence || 0.5) * 100) }}%）</text>
          </view>
          <text class="ai-sug-rationale">建议依据：{{ msgAiInfo.rationale }}</text>
          <text class="ai-sug-hint">↑ 内容已填入输入框，请按需修改后发送</text>
        </view>
      </view>

      <view class="modal-actions">
        <view class="modal-btn modal-btn--cancel" @tap="closeMsgModal">取消</view>
        <view class="modal-btn modal-btn--confirm" :class="{ 'modal-btn--submitting': submitting }" @tap="submitMsg">
          {{ submitting ? '发送中…' : '发送' }}
        </view>
      </view>
    </view>
  </view>

  <!-- 分配评估 Modal -->
  <view v-if="showAssignModal" class="modal-mask" @tap="closeAssignModal">
    <view class="modal-sheet assign-sheet" @tap.stop>
      <view class="modal-title">分配评估 — {{ student.name }}</view>

      <!-- 量表选择 + AI建议 -->
      <view class="modal-field">
        <view class="ai-bar">
          <text class="modal-label" style="margin-bottom:0">量表选择（约{{ assignScaleTime }}分钟）</text>
          <view class="ai-btn" :class="{ 'ai-btn--loading': assignAiLoading }" @tap="loadAiAssessment">
            {{ assignAiLoading ? '分析中…' : '🤖 AI建议' }}
          </view>
        </view>
        <!-- 快速包选 -->
        <view class="assign-packs">
          <view v-for="(pack, pKey) in SCALE_PACKS" :key="pKey"
            class="assign-pack-btn"
            :class="{ 'assign-pack-btn--active': isPackActive(String(pKey)) }"
            @tap="selectPack(String(pKey))">
            {{ pack.label }}
          </view>
        </view>
        <!-- 量表明细勾选 -->
        <view class="assign-scales">
          <view v-for="s in SCALES_REGISTRY" :key="s.key"
            class="assign-scale-item"
            :class="{ 'assign-scale-item--active': assignForm.scales.includes(s.key),
                       'assign-scale-item--ai': assignAiInfo.suggested_scales?.includes(s.key) }"
            @tap="toggleAssignScale(s.key)">
            <view class="assign-scale-check">{{ assignForm.scales.includes(s.key) ? '✓' : '' }}</view>
            <view class="assign-scale-info">
              <text class="assign-scale-name">{{ s.shortLabel }} · {{ s.label }}</text>
              <text v-if="assignAiInfo.per_scale_rationale?.[s.key]" class="assign-scale-ai-reason">🤖 {{ assignAiInfo.per_scale_rationale[s.key] }}</text>
              <text v-else class="assign-scale-desc">{{ s.desc }}</text>
            </view>
            <text class="assign-scale-time">{{ s.time }}min</text>
          </view>
        </view>
        <!-- AI 总体建议 -->
        <view v-if="assignAiInfo.rationale" class="ai-suggestion-box" style="margin-top:12rpx">
          <view class="ai-sug-header">
            <text class="ai-sug-tag">✨ AI推荐{{ assignAiInfo.pack_name ? '「' + assignAiInfo.pack_name + '」' : '' }}（{{ assignAiInfo.source === 'llm' ? '大模型' : '规则引擎' }}，可信度 {{ Math.round((assignAiInfo.confidence || 0.6) * 100) }}%）</text>
          </view>
          <text class="ai-sug-rationale">推荐原因：{{ assignAiInfo.rationale }}</text>
          <text class="ai-sug-hint">↑ 已自动勾选推荐量表，可手动增减</text>
        </view>
      </view>

      <!-- 问卷区 -->
      <view class="modal-field" v-if="surveyTools.length">
        <view class="assign-section-title">
          <text class="modal-label" style="margin-bottom:0">问卷（可选）</text>
          <text class="assign-section-hint">{{ selectedSurveys.length ? selectedSurveys.length + '份已选' : '可与量表同时分配' }}</text>
        </view>
        <view class="assign-scales">
          <view v-for="sv in surveyTools" :key="sv.key"
            class="assign-scale-item"
            :class="{ 'assign-scale-item--active': selectedSurveys.includes(sv.surveyId!),
                       'assign-scale-item--ai': assignAiInfo.suggested_surveys?.some((s:any) => s.id === sv.surveyId) }"
            @tap="selectedSurveys.includes(sv.surveyId!) ? selectedSurveys.splice(selectedSurveys.indexOf(sv.surveyId!),1) : selectedSurveys.push(sv.surveyId!)">
            <view class="assign-scale-check">{{ selectedSurveys.includes(sv.surveyId!) ? '✓' : '' }}</view>
            <view class="assign-scale-info">
              <text class="assign-scale-name">📝 {{ sv.label }}</text>
              <text class="assign-scale-ai-reason" v-if="assignAiInfo.suggested_surveys?.find((s:any) => s.id === sv.surveyId)">
                🤖 {{ assignAiInfo.suggested_surveys.find((s:any) => s.id === sv.surveyId)?.rationale }}
              </text>
              <text v-else class="assign-scale-desc">{{ sv.desc }}</text>
            </view>
            <text class="assign-scale-time">{{ sv.time }}min</text>
          </view>
        </view>
      </view>

      <view class="modal-field">
        <text class="modal-label">备注（可选）</text>
        <textarea class="modal-textarea" v-model="assignForm.note" placeholder="请输入备注…" />
      </view>

      <view class="modal-actions">
        <view class="modal-btn modal-btn--cancel" @tap="closeAssignModal">取消</view>
        <view class="modal-btn modal-btn--confirm" :class="{ 'modal-btn--submitting': submitting }" @tap="submitAssign">
          {{ submitting ? '提交中…' : '确认分配' }}
        </view>
      </view>
    </view>
  </view>

  <!-- 开处方 Modal -->
  <view v-if="showRxModal" class="modal-mask" @tap="closeRxModal">
    <view class="modal-sheet" @tap.stop>
      <view class="modal-title">开具处方 — {{ student.name }}</view>

      <view class="modal-field">
        <text class="modal-label">处方类型</text>
        <view class="modal-options">
          <view v-for="t in rxTypes" :key="t.key" class="modal-option"
            :class="{ 'modal-option--active': rxForm.type === t.key }" @tap="rxForm.type = t.key">
            {{ t.label }}
          </view>
        </view>
      </view>

      <!-- AI 起草入口 -->
      <view class="modal-field">
        <view class="ai-bar">
          <text class="modal-label" style="margin-bottom:0">处方内容</text>
          <view class="ai-btn" :class="{ 'ai-btn--loading': rxAiLoading }" @tap="loadAiDraft">
            {{ rxAiLoading ? '生成中…' : '🤖 AI起草' }}
          </view>
        </view>
        <textarea class="modal-textarea" v-model="rxForm.content" placeholder="输入处方内容，或点击右上角 AI起草 自动生成…" />
        <!-- AI 建议展示区（持久显示） -->
        <view v-if="rxForm.aiSource" class="ai-suggestion-box">
          <view class="ai-sug-header">
            <text class="ai-sug-tag">✨ AI草稿已生成（{{ rxForm.aiSource === 'llm' ? '大模型' : '规则引擎' }}，可信度 {{ Math.round((rxForm.confidence || 0.5) * 100) }}%）</text>
          </view>
          <text v-if="rxForm.rationale" class="ai-sug-rationale">起草依据：{{ rxForm.rationale }}</text>
          <text v-if="rxForm.duration" class="ai-sug-rationale">建议周期：{{ rxForm.duration }}，随访：{{ rxForm.followUp }}</text>
          <text class="ai-sug-hint">↑ 内容已填入，请检查修改后再开具</text>
        </view>
      </view>

      <!-- 高风险副签 -->
      <view class="modal-field" v-if="(student.risk_level || 0) >= 3">
        <view class="rx-expert-bar" @tap="rxForm.requestExpertReview = !rxForm.requestExpertReview">
          <view class="rx-expert-checkbox" :class="{ 'rx-expert-checkbox--on': rxForm.requestExpertReview }">
            {{ rxForm.requestExpertReview ? '✓' : '' }}
          </view>
          <text class="rx-expert-label">提交专家副签（风险 R{{ student.risk_level }}，建议开启）</text>
        </view>
      </view>

      <view class="modal-actions">
        <view class="modal-btn modal-btn--cancel" @tap="closeRxModal">取消</view>
        <view class="modal-btn modal-btn--confirm" :class="{ 'modal-btn--submitting': submitting }" @tap="submitRx">
          {{ submitting ? '提交中…' : '确认开具' }}
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { httpReq as http } from '@/api/request'
import { SCALES_REGISTRY, SCALE_PACKS, estimateTime, loadSurveyTools } from '@/utils/assessmentTools'
import type { ToolDef } from '@/utils/assessmentTools'
import { avatarColor, parseRisk, riskColor, riskBg } from '@/utils/studentUtils'

const studentId = ref(0)
const activeTab = ref('overview')
const refreshing = ref(false)
const dataLoading = ref(false)
const student = ref<any>({})
const behaviorLogs = ref<any[]>([])
const supervisionNotes = ref<any[]>([])
const newNote = ref('')

// Modal state
const showMsgModal = ref(false)
const msgContent = ref('')
const msgAiLoading = ref(false)
const msgAiInfo = ref<any>({})

const showAssignModal = ref(false)
const assignAiLoading = ref(false)
const assignAiInfo = ref<any>({})

const showRxModal = ref(false)
const submitting = ref(false)
const assignForm = ref<{ scales: string[], note: string }>({ scales: ['big5', 'ttm7'], note: '' })
const surveyTools = ref<ToolDef[]>([])
const selectedSurveys = ref<number[]>([])
const rxForm = ref({
  type: 'behavior', content: '', aiSource: '', rationale: '',
  confidence: 0.5, duration: '', followUp: '', requestExpertReview: false,
})
const rxAiLoading = ref(false)

// ── 弹窗开关（重置 AI 状态） ──
function closeMsgModal() { showMsgModal.value = false; msgAiInfo.value = {}; msgContent.value = '' }
function closeAssignModal() {
  showAssignModal.value = false
  assignAiInfo.value = {}
  assignForm.value = { scales: ['big5', 'ttm7'], note: '' }
  selectedSurveys.value = []
}
function closeRxModal() {
  showRxModal.value = false
  rxForm.value = { type: 'behavior', content: '', aiSource: '', rationale: '', confidence: 0.5, duration: '', followUp: '', requestExpertReview: false }
}
async function openAssignModal() {
  assignAiInfo.value = {}
  assignForm.value = { scales: ['big5', 'ttm7'], note: '' }
  selectedSurveys.value = []
  showAssignModal.value = true
  surveyTools.value = await loadSurveyTools()
}
function openRxModal() {
  rxForm.value = { type: 'behavior', content: '', aiSource: '', rationale: '', confidence: 0.5, duration: '', followUp: '', requestExpertReview: false }
  showRxModal.value = true
}

// ── 分配评估 — 量表选择辅助 ──
const assignScaleTime = computed(() => estimateTime(assignForm.value.scales))
function toggleAssignScale(key: string) {
  const idx = assignForm.value.scales.indexOf(key)
  if (idx >= 0) assignForm.value.scales.splice(idx, 1)
  else assignForm.value.scales.push(key)
}
function isPackActive(packKey: string): boolean {
  const pack = (SCALE_PACKS as Record<string, { scales: string[] }>)[packKey]
  if (!pack) return false
  return pack.scales.every(k => assignForm.value.scales.includes(k)) &&
    assignForm.value.scales.length === pack.scales.length
}
function selectPack(packKey: string) {
  const pack = (SCALE_PACKS as Record<string, { scales: string[] }>)[packKey]
  if (!pack) return
  if (isPackActive(packKey)) assignForm.value.scales = []
  else assignForm.value.scales = [...pack.scales]
}

// ── AI：发消息建议 ──
async function loadAiMessage() {
  if (msgAiLoading.value) return
  msgAiLoading.value = true
  try {
    const res = await http<any>('/api/v1/coach/students/' + studentId.value + '/ai-message-draft', { method: 'POST' })
    msgContent.value = res.draft_content || ''
    msgAiInfo.value = { rationale: res.rationale || '', confidence: res.confidence ?? 0.5, source: res.source || 'rules' }
  } catch (e: any) {
    uni.showToast({ title: e?.data?.detail || 'AI建议失败', icon: 'none', duration: 2000 })
  } finally {
    msgAiLoading.value = false
  }
}

// ── AI：评估量表建议 ──
async function loadAiAssessment() {
  if (assignAiLoading.value) return
  assignAiLoading.value = true
  try {
    const res = await http<any>('/api/v1/coach/students/' + studentId.value + '/ai-assessment-suggestion', { method: 'POST' })
    assignAiInfo.value = {
      suggested_scales: res.suggested_scales || [],
      per_scale_rationale: res.per_scale_rationale || {},
      pack_name: res.pack_name || '',
      pack_key: res.pack_key || '',
      rationale: res.rationale || '',
      confidence: res.confidence ?? 0.6,
      source: res.source || 'rules',
    }
    if (res.suggested_scales?.length) assignForm.value.scales = [...res.suggested_scales]
    // P2: AI 推荐问卷自动预选
    if (res.suggested_surveys?.length) {
      selectedSurveys.value = res.suggested_surveys.map((s: any) => s.id)
    }
  } catch (e: any) {
    uni.showToast({ title: e?.data?.detail || 'AI建议失败', icon: 'none', duration: 2000 })
  } finally {
    assignAiLoading.value = false
  }
}

// ── AI：处方起草 ──
async function loadAiDraft() {
  if (rxAiLoading.value) return
  rxAiLoading.value = true
  try {
    const res = await http<any>('/api/v1/coach/students/' + studentId.value + '/ai-prescription-draft', { method: 'POST' })
    rxForm.value.content = res.draft_content || ''
    rxForm.value.type = res.type || rxForm.value.type
    rxForm.value.aiSource = res.source || 'rules'
    rxForm.value.rationale = res.rationale || ''
    rxForm.value.confidence = res.confidence ?? 0.5
    rxForm.value.duration = res.duration || ''
    rxForm.value.followUp = res.follow_up || ''
    if (res.micro_actions?.length) {
      rxForm.value.content += '\n\n微行动：\n' + (res.micro_actions as string[]).map((a: string) => '• ' + a).join('\n')
    }
  } catch (e: any) {
    uni.showToast({ title: e?.data?.detail || 'AI起草失败', icon: 'none', duration: 2000 })
  } finally {
    rxAiLoading.value = false
  }
}

// Health data for 健康数据 tab
const healthData = ref<any>({})
const glucoseTrend = ref<any[]>([])
const weightTrend = ref<any[]>([])

const detailTabs = [
  { key: 'overview', label: '概览' },
  { key: 'behavior', label: '行为记录' },
  { key: 'supervision', label: '督导记录' },
  { key: 'health', label: '健康数据' },
]

const rxTypes = [
  { key: 'behavior', label: '行为处方' },
  { key: 'exercise', label: '运动处方' },
  { key: 'nutrition', label: '饮食处方' },
  { key: 'emotion', label: '情绪处方' },
]

const rxTypeLabels: Record<string, string> = {
  behavior: '行为处方',
  exercise: '运动处方',
  nutrition: '饮食处方',
  emotion: '情绪处方',
}

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
    const completed = d.completed ?? false
    return { label, completed, height: completed ? 100 : 20 }
  })
})


function logColor(type: string): string {
  const m: Record<string, string> = { checkin: '#27AE60', mood: '#9B59B6', meal: '#E67E22', exercise: '#3498DB', medication: '#E74C3C' }
  return m[type] || '#5B6B7F'
}

function glucoseColor(val: number | null | undefined): string {
  if (val == null) return '#5B6B7F'
  if (val > 7.0) return '#E74C3C'
  if (val > 6.1) return '#E67E22'
  return '#27AE60'
}

async function loadData() {
  if (!studentId.value) return
  dataLoading.value = true

  // 主数据：dashboard 学员列表（含 health_data / micro_action_7d）
  try {
    const dash = await http<any>('/api/v1/coach/dashboard')
    const found = (dash.students || []).find((s: any) => (s.id || s.user_id) === studentId.value)
    if (found) {
      const ma = found.micro_action_7d || {}
      student.value = {
        ...found,
        name: found.name || found.full_name || found.username || '学员',
        risk_level: typeof found.risk_level === 'string'
          ? parseInt(found.risk_level.replace(/\D/g, '')) || 0
          : (found.risk_level || 0),
        micro_action_count: ma.completed ?? 0,
        micro_action_total: ma.total ?? 0,
        week_active_days: ma.completed != null ? Math.min(ma.completed, 7) : undefined,
        fasting_glucose: found.health_data?.fasting_glucose,
        weight: found.health_data?.weight,
        exercise_minutes: found.health_data?.exercise_minutes,
      }
    }
  } catch (e) { console.warn('[coach/students/detail] dashboard:', e) }

  // 补充：profile 端点（height / weight / goals）
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
  } catch (e) { console.warn('[coach/students/detail] profile:', e) }

  // 健康数据 tab 初始化（仅使用 dashboard health_data 字段，无额外端点请求）
  const hd = student.value.health_data || {}
  healthData.value = {
    fasting_glucose: hd.fasting_glucose ?? student.value.fasting_glucose ?? null,
    weight: hd.weight ?? student.value.weight ?? null,
    exercise_minutes: hd.exercise_minutes ?? student.value.exercise_minutes ?? null,
    sleep_hours: hd.sleep_hours ?? null,
  }

  // 行为记录（仅此学员）
  try {
    const bRes = await http<any>('/api/v1/coach/behavior/' + studentId.value + '/recent?limit=20')
    behaviorLogs.value = (bRes.items || []).map((r: any) => ({
      type: r.behavior_type,
      type_label: r.type_label || r.behavior_type,
      content: r.description || r.note || '完成微行动',
      time: r.recorded_at ? r.recorded_at.slice(0, 10) : '',
    }))
  } catch { behaviorLogs.value = [] }

  // 督导记录（仅此学员）
  try {
    const nRes = await http<any>('/api/v1/coach/students/' + studentId.value + '/notes')
    supervisionNotes.value = nRes.items || []
  } catch { supervisionNotes.value = [] }

  dataLoading.value = false
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
    const nRes = await http<any>('/api/v1/coach/students/' + studentId.value + '/notes')
    supervisionNotes.value = nRes.items || []
  } catch {
    uni.showToast({ title: '提交失败', icon: 'none' })
  }
}

async function submitAssign() {
  if (submitting.value) return
  if (!assignForm.value.scales.length && !selectedSurveys.value.length) {
    uni.showToast({ title: '请选择至少一个量表或问卷', icon: 'none' }); return
  }
  submitting.value = true
  let scaleOk = true, surveyOk = true
  try {
    // 分配量表
    if (assignForm.value.scales.length) {
      await http('/api/v1/assessment-assignments/assign', {
        method: 'POST',
        data: {
          student_id: studentId.value,
          scales: assignForm.value.scales,
          note: assignForm.value.note || '',
        },
      })
    }
  } catch { scaleOk = false }

  // 分配问卷（逐条，静默失败不阻断）
  for (const surveyId of selectedSurveys.value) {
    try {
      await http(`/api/v1/surveys/${surveyId}/assign`, {
        method: 'POST',
        data: { student_ids: [studentId.value], message: assignForm.value.note || '' },
      })
    } catch { surveyOk = false }
  }

  submitting.value = false
  closeAssignModal()
  if (!scaleOk && !surveyOk) {
    uni.showToast({ title: '分配失败，请稍后重试', icon: 'none' })
  } else {
    const parts = []
    if (assignForm.value.scales.length && scaleOk) parts.push(`${assignForm.value.scales.length}个量表`)
    if (selectedSurveys.value.length) parts.push(`${selectedSurveys.value.length}份问卷`)
    uni.showToast({ title: parts.join(' + ') + ' 已分配', icon: 'success' })
  }
}

async function submitRx() {
  if (submitting.value) return
  const content = rxForm.value.content.trim()
  if (!content) { uni.showToast({ title: '请填写处方内容', icon: 'none' }); return }
  submitting.value = true
  try {
    const label = rxTypeLabels[rxForm.value.type] || '处方'
    await http('/api/v1/coach/students/' + studentId.value + '/notes', {
      method: 'POST',
      data: { content: `[${label}] ${content}` },
    })
    // P3: 如勾选专家副签，提交副签申请
    const wantExpertReview = rxForm.value.requestExpertReview
    if (wantExpertReview) {
      try {
        await http('/api/v1/coach/students/' + studentId.value + '/prescriptions/request-expert-review', { method: 'POST' })
      } catch (e) { console.warn('[detail] expert review request:', e) }
    }
    closeRxModal()
    uni.showToast({ title: wantExpertReview ? '处方已开具，已提交专家副签' : '处方已开具', icon: 'success' })
    // 刷新督导记录（处方存入督导记录）
    const nRes = await http<any>('/api/v1/coach/students/' + studentId.value + '/notes')
    supervisionNotes.value = nRes.items || []
  } catch {
    uni.showToast({ title: '开具失败，请稍后重试', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function sendMessage() {
  msgContent.value = ''
  msgAiInfo.value = {}
  showMsgModal.value = true
}

async function submitMsg() {
  if (submitting.value) return
  const content = msgContent.value.trim()
  if (!content) { uni.showToast({ title: '请输入消息内容', icon: 'none' }); return }
  submitting.value = true
  try {
    await http('/api/v1/coach/students/' + studentId.value + '/notes', {
      method: 'POST',
      data: { content: '[消息] ' + content },
    })
    closeMsgModal()
    uni.showToast({ title: '消息已发送', icon: 'success' })
    const nRes = await http<any>('/api/v1/coach/students/' + studentId.value + '/notes')
    supervisionNotes.value = nRes.items || []
  } catch {
    uni.showToast({ title: '发送失败，请稍后重试', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
function refresh() { loadData() }
function goBack() { uni.navigateBack() }

onLoad((opts: any) => {
  studentId.value = parseInt(opts?.id) || 0
  if (opts?.tab) activeTab.value = opts.tab
  loadData()
})
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

.detail-tabs { display: flex; gap: 8rpx; padding: 0 24rpx 16rpx; }
.detail-tab { flex: 1; text-align: center; padding: 14rpx 0; background: #fff; border-radius: 12rpx; font-size: 24rpx; color: #5B6B7F; }
.detail-tab--active { background: #2D8E69; color: #fff; }

.detail-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin: 0 24rpx 16rpx; }
.detail-card-title { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }

.detail-metric-grid { display: flex; }
.detail-metric { flex: 1; text-align: center; }
.detail-metric-val { display: block; font-size: 36rpx; font-weight: 700; }
.detail-metric-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.detail-action-bars { display: flex; align-items: flex-end; gap: 12rpx; height: 160rpx; }
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

/* 健康数据 Tab */
.health-stat-grid { display: flex; gap: 16rpx; flex-wrap: wrap; }
.health-stat { flex: 1; min-width: calc(50% - 8rpx); background: #F8F9FA; border-radius: 12rpx; padding: 20rpx 16rpx; text-align: center; }
.health-stat-val { display: block; font-size: 44rpx; font-weight: 700; }
.health-stat-unit { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 2rpx; }
.health-stat-label { display: block; font-size: 22rpx; color: #5B6B7F; margin-top: 6rpx; }

/* 趋势图 */
.trend-bars { display: flex; align-items: flex-end; gap: 8rpx; height: 180rpx; }
.trend-bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; }
.trend-bar-top { font-size: 18rpx; color: #8E99A4; margin-bottom: 4rpx; }
.trend-bar { width: 100%; border-radius: 6rpx 6rpx 0 0; min-height: 8rpx; }
.trend-bar-label { font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }

/* Modals */
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; display: flex; align-items: flex-end; }
.modal-sheet { width: 100%; background: #fff; border-radius: 32rpx 32rpx 0 0; padding: 40rpx 32rpx calc(48rpx + env(safe-area-inset-bottom)); }
.modal-title { font-size: 34rpx; font-weight: 700; color: #2C3E50; text-align: center; margin-bottom: 32rpx; }

.modal-field { margin-bottom: 28rpx; }
.modal-label { display: block; font-size: 26rpx; color: #5B6B7F; font-weight: 500; margin-bottom: 12rpx; }
.modal-options { display: flex; gap: 12rpx; flex-wrap: wrap; }
.modal-option { padding: 12rpx 20rpx; border-radius: 10rpx; background: #F0F0F0; font-size: 26rpx; color: #5B6B7F; }
.modal-option--active { background: #2D8E69; color: #fff; }
.modal-textarea { width: 100%; min-height: 160rpx; background: #F5F6FA; border-radius: 12rpx; padding: 16rpx; font-size: 28rpx; color: #2C3E50; box-sizing: border-box; }

.modal-actions { display: flex; gap: 16rpx; margin-top: 32rpx; }
.modal-btn { flex: 1; text-align: center; padding: 26rpx 0; border-radius: 16rpx; font-size: 30rpx; font-weight: 600; }
.modal-btn--cancel { background: #F0F0F0; color: #5B6B7F; }
.modal-btn--confirm { background: #2D8E69; color: #fff; }
.modal-btn--submitting { background: #8DC9B3; }

.detail-loading { display: flex; align-items: center; justify-content: center; padding: 120rpx 0; }
.detail-loading-text { font-size: 28rpx; color: #8E99A4; }
.detail-empty { text-align: center; padding: 60rpx; font-size: 26rpx; color: #8E99A4; }

/* ── AI 通用按钮 ── */
.ai-bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12rpx; }
.ai-btn { padding: 8rpx 20rpx; background: linear-gradient(135deg, #1a7a50, #27AE60); color: #fff; border-radius: 10rpx; font-size: 24rpx; font-weight: 600; }
.ai-btn--loading { background: #8DC9B3; pointer-events: none; opacity: 0.7; }

/* ── AI 建议展示框（持久显示，不会自动消失） ── */
.ai-suggestion-box {
  margin-top: 12rpx; padding: 20rpx 24rpx;
  background: linear-gradient(135deg, #f0faf5, #eaf6ff);
  border-radius: 16rpx; border-left: 6rpx solid #27AE60;
}
.ai-sug-header { margin-bottom: 10rpx; }
.ai-sug-tag { font-size: 22rpx; font-weight: 700; color: #1a7a50; }
.ai-sug-rationale { display: block; font-size: 24rpx; color: #2C3E50; line-height: 1.6; margin-bottom: 6rpx; }
.ai-sug-hint { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 8rpx; }

/* ── 评估选项 AI 高亮 ── */
.modal-option--ai { border: 2rpx solid #27AE60 !important; }
.option-ai-mark { font-size: 20rpx; }

/* ── 专家副签（开处方 Modal） ── */
.rx-expert-bar { display: flex; align-items: center; gap: 12rpx; padding: 16rpx; background: #FFF8E6; border-radius: 12rpx; border: 2rpx solid #F39C12; }
.rx-expert-checkbox { width: 40rpx; height: 40rpx; border-radius: 8rpx; border: 2rpx solid #F39C12; display: flex; align-items: center; justify-content: center; font-size: 28rpx; color: #F39C12; flex-shrink: 0; }
.rx-expert-checkbox--on { background: #F39C12; color: #fff; border-color: #F39C12; }
.rx-expert-label { font-size: 26rpx; color: #E67E22; flex: 1; line-height: 1.4; }

/* ── 分配评估 Modal — 量表选择 ── */
.assign-sheet { max-height: 92vh; overflow-y: auto; }
.assign-packs { display: flex; gap: 10rpx; flex-wrap: wrap; margin: 12rpx 0 8rpx; }
.assign-pack-btn { padding: 10rpx 28rpx; border-radius: 32rpx; font-size: 24rpx; background: #F0F0F0; color: #5B6B7F; }
.assign-pack-btn--active { background: #2D8E69; color: #fff; }
.assign-section-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.assign-section-hint { font-size: 22rpx; color: #8E99A4; }
.assign-scales { display: flex; flex-direction: column; gap: 8rpx; }
.assign-scale-item { display: flex; align-items: center; gap: 16rpx; padding: 16rpx 12rpx; background: #F8F9FA; border-radius: 12rpx; border: 2rpx solid transparent; }
.assign-scale-item--active { background: #F0FFF8; border-color: #2D8E69; }
.assign-scale-item--ai { border-color: #F39C12; }
.assign-scale-item--active.assign-scale-item--ai { background: #FFF8F0; border-color: #E67E22; }
.assign-scale-check { width: 36rpx; height: 36rpx; border-radius: 8rpx; border: 2rpx solid #CCC; display: flex; align-items: center; justify-content: center; font-size: 22rpx; color: #2D8E69; font-weight: 700; background: #fff; flex-shrink: 0; }
.assign-scale-item--active .assign-scale-check { background: #2D8E69; color: #fff; border-color: #2D8E69; }
.assign-scale-info { flex: 1; min-width: 0; }
.assign-scale-name { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; }
.assign-scale-desc { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 2rpx; }
.assign-scale-ai-reason { display: block; font-size: 22rpx; color: #E67E22; margin-top: 2rpx; }
.assign-scale-time { font-size: 22rpx; color: #8E99A4; flex-shrink: 0; }
</style>
