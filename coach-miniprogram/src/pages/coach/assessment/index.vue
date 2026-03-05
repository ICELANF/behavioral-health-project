<template>
  <view class="assess-page">
    <!-- 导航栏 -->
    <view class="assess-navbar">
      <view class="assess-nav-back" @tap="goBack">←</view>
      <text class="assess-nav-title">评估管理</text>
      <view class="assess-nav-action" @tap="openAssign()">+ 分配</view>
    </view>

    <!-- 统计 + Tab 合并单排 -->
    <view class="assess-stattabs">
      <view
        v-for="t in statTabs" :key="t.key"
        class="assess-st" :class="{ 'assess-st--active': activeTab === t.key }"
        @tap="activeTab = t.key"
      >
        <text class="assess-st-num" :style="activeTab === t.key ? {} : { color: t.color }">{{ t.count }}</text>
        <text class="assess-st-label">{{ t.label }}</text>
      </view>
    </view>

    <!-- 搜索 -->
    <view class="assess-search">
      <input class="assess-search-input" placeholder="搜索学员姓名" v-model="searchText" @confirm="loadData" />
    </view>

    <!-- 评估列表 -->
    <scroll-view scroll-y class="assess-list" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view v-for="item in filteredItems" :key="item.id" class="assess-card" @tap="item.status !== 'pending' && goReview(item)">
        <view class="assess-card-header">
          <view class="assess-card-avatar" :style="{ background: avatarColor(item.student_name || item.user_name) }">
            {{ (item.student_name || item.user_name || '?')[0] }}
          </view>
          <view class="assess-card-info">
            <text class="assess-card-name">{{ item.student_name || item.user_name || '未知学员' }}</text>
            <text class="assess-card-scale">{{ formatScales(item) }}</text>
          </view>
          <view class="assess-status-tag" :style="{ background: statusColor(item.status) }">
            {{ statusLabel(item.status) }}
          </view>
        </view>
        <view class="assess-card-body">
          <view class="assess-card-meta">
            <text class="assess-meta-item">📅 {{ formatDate(item.assigned_at || item.created_at) }}</text>
            <text class="assess-meta-item" v-if="item.completed_at">✅ {{ formatDate(item.completed_at) }}</text>
            <text class="assess-meta-item" v-if="item.score != null">📊 {{ item.score }}分</text>
          </view>
          <!-- 待审核：快捷操作 -->
          <view v-if="['submitted','review','completed','completed_pending_review'].includes(item.status)" class="assess-card-actions">
            <view class="assess-action-btn assess-action-ai"
              :class="{ 'assess-action-ai--loading': aiLoadingId === item.id }"
              @tap.stop="openAiReport(item)">
              {{ aiLoadingId === item.id ? '解读中…' : '🤖 AI解读' }}
            </view>
            <view class="assess-action-btn assess-action-review" @tap.stop="goReview(item)">查看评估</view>
          </view>
          <!-- 待完成：提醒学员 -->
          <view v-if="item.status === 'pending'" class="assess-card-actions">
            <view class="assess-action-btn assess-action-remind" @tap.stop="remindStudent(item)">提醒完成</view>
          </view>
        </view>
      </view>

      <view v-if="!loading && filteredItems.length === 0" class="assess-empty">
        <text class="assess-empty-icon">📋</text>
        <text class="assess-empty-text">暂无{{ statTabs.find(t => t.key === activeTab)?.label || '' }}评估</text>
        <view class="assess-empty-action" @tap="openAssign()">分配新评估</view>
      </view>

      <view v-if="loading" class="assess-loading">
        <text>加载中...</text>
      </view>
    </scroll-view>

    <!-- AI 解读报告底部弹窗 -->
    <view v-if="showAiSheet" class="assess-modal-mask" @tap="showAiSheet = false">
      <view class="assess-modal assess-ai-sheet" @tap.stop>
        <view class="assess-ai-header">
          <text class="assess-ai-title">🤖 AI 评估解读报告</text>
          <view class="assess-ai-close" @tap="showAiSheet = false">✕</view>
        </view>
        <view v-if="aiReport" class="assess-ai-body">
          <view class="assess-ai-section">
            <text class="assess-ai-label">📋 总结</text>
            <text class="assess-ai-text">{{ aiReport.summary }}</text>
          </view>
          <view class="assess-ai-section">
            <text class="assess-ai-label">📊 阶段解读</text>
            <text class="assess-ai-text">{{ aiReport.stage_interpretation }}</text>
          </view>
          <view class="assess-ai-section" v-if="aiReport.strengths?.length">
            <text class="assess-ai-label">✅ 优势</text>
            <view v-for="(s, i) in aiReport.strengths" :key="i" class="assess-ai-tag assess-ai-tag--green">{{ s }}</view>
          </view>
          <view class="assess-ai-section" v-if="aiReport.risks?.length">
            <text class="assess-ai-label">⚠️ 风险</text>
            <view v-for="(r, i) in aiReport.risks" :key="i" class="assess-ai-tag assess-ai-tag--orange">{{ r }}</view>
          </view>
          <view class="assess-ai-section" v-if="aiReport.coach_actions?.length">
            <text class="assess-ai-label">💡 建议行动</text>
            <view v-for="(a, i) in aiReport.coach_actions" :key="i" class="assess-ai-action-item">{{ i+1 }}. {{ a }}</view>
          </view>
          <view class="assess-ai-section" v-if="aiReport.prescription_hint">
            <text class="assess-ai-label">📝 处方方向</text>
            <text class="assess-ai-text assess-ai-hint">{{ aiReport.prescription_hint }}</text>
          </view>
          <view class="assess-ai-footer">
            <text class="assess-ai-source">来源: {{ aiReport.source === 'llm' ? 'AI大模型' : '规则引擎' }}</text>
            <text class="assess-ai-conf">置信度: {{ Math.round((aiReport.confidence || 0) * 100) }}%</text>
          </view>
        </view>
        <view v-else class="assess-ai-loading">
          <text>正在生成解读报告，请稍候…</text>
        </view>
        <view class="assess-modal-actions" style="margin-top:24rpx">
          <view class="assess-modal-btn assess-modal-confirm" @tap="showAiSheet = false">确认</view>
        </view>
      </view>
    </view>

    <!-- 分配评估弹窗 -->
    <view v-if="showAssign" class="assess-modal-mask" @tap="closeAssign">
      <view class="assess-modal" @tap.stop>
        <text class="assess-modal-title">分配新评估</text>

        <!-- ① 学员选择面板（未选时显示） -->
        <view v-if="!selectedStudentObj" class="assess-modal-section">
          <view class="assess-modal-hrow">
            <text class="assess-modal-label">选择学员</text>
            <view class="assess-search-toggle" @tap="modalSearchMode = !modalSearchMode">
              {{ modalSearchMode ? '📋 推荐' : '🔍 搜索' }}
            </view>
          </view>

          <!-- 搜索框 -->
          <view v-if="modalSearchMode" class="assess-modal-searchbox">
            <input class="assess-modal-sinput" v-model="modalSearchQuery" placeholder="输入姓名搜索..." focus />
          </view>

          <!-- 学员卡片列表 -->
          <view class="assess-student-cards">
            <view
              v-for="s in currentBatchStudents" :key="s.id"
              class="assess-sc-card"
              @tap="selectStudentObj(s)"
            >
              <view class="assess-sc-avatar" :style="{ background: avatarColor(s.name) }">{{ (s.name||'?')[0] }}</view>
              <view class="assess-sc-info">
                <text class="assess-sc-name">{{ s.name }}</text>
                <text class="assess-sc-sub">{{ formatStudentSub(s) }}</text>
              </view>
              <view class="assess-sc-risk" :style="{ background: riskBg(s.risk_level) }">R{{ parseRisk(s.risk_level) }}</view>
            </view>
            <view v-if="currentBatchStudents.length === 0" class="assess-sc-empty">
              {{ modalSearchMode ? '未找到匹配学员' : '暂无学员数据' }}
            </view>
          </view>

          <!-- 批次导航（仅推荐模式） -->
          <view v-if="!modalSearchMode && prioritizedStudents.length > BATCH_SIZE" class="assess-batch-nav">
            <view class="assess-batch-btn" :class="{ 'assess-batch-btn--off': batchIndex === 0 }" @tap="prevBatch">‹ 上一批</view>
            <text class="assess-batch-info">{{ Math.floor(batchIndex / BATCH_SIZE) + 1 }} / {{ Math.ceil(prioritizedStudents.length / BATCH_SIZE) }}</text>
            <view class="assess-batch-btn" :class="{ 'assess-batch-btn--off': !hasNextBatch }" @tap="nextBatch">下一批 ›</view>
          </view>
        </view>

        <!-- ② 已选学员展示（已选时显示） -->
        <view v-else class="assess-modal-section">
          <view class="assess-modal-hrow">
            <text class="assess-modal-label">已选学员</text>
            <view class="assess-reselect" @tap="selectedStudentObj = null">↩ 重新选择</view>
          </view>
          <view class="assess-selected-card">
            <view class="assess-sc-avatar" :style="{ background: avatarColor(selectedStudentObj.name) }">{{ (selectedStudentObj.name||'?')[0] }}</view>
            <view class="assess-sc-info">
              <text class="assess-sc-name">{{ selectedStudentObj.name }}</text>
              <text class="assess-sc-sub">{{ formatStudentSub(selectedStudentObj) }}</text>
            </view>
            <view class="assess-sc-risk" :style="{ background: riskBg(selectedStudentObj.risk_level) }">R{{ parseRisk(selectedStudentObj.risk_level) }}</view>
          </view>
        </view>

        <!-- ③ 量表/时间/备注（仅已选学员后展示） -->
        <template v-if="selectedStudentObj">
          <view class="assess-modal-section">
            <view class="assess-modal-hrow">
              <text class="assess-modal-label">量表组合</text>
              <view class="assess-ai-suggest-btn" :class="{ 'assess-ai-suggest-btn--loading': assignAiLoading }" @tap="loadAiSuggestion">
                {{ assignAiLoading ? '分析中…' : '🤖 AI建议' }}
              </view>
            </view>
            <!-- 包预设快选 -->
            <view class="assess-pack-row">
              <view v-for="(pack, pKey) in SCALE_PACKS" :key="pKey"
                class="assess-pack-chip"
                :class="{ 'assess-pack-chip--active': isPackSelected(String(pKey)) }"
                @tap="applyPack(String(pKey))">
                {{ pack.label }}
              </view>
            </view>
            <view class="assess-scale-options">
              <view
                v-for="s in SCALES_REGISTRY" :key="s.key"
                class="assess-scale-opt"
                :class="{ 'assess-scale-opt--active': selectedScales.includes(s.key),
                           'assess-scale-opt--ai': assignAiInfo.suggested_scales?.includes(s.key) }"
                @tap="toggleScale(s.key)"
              >
                {{ s.shortLabel }}<text v-if="assignAiInfo.suggested_scales?.includes(s.key)" style="font-size:18rpx"> 🤖</text>
              </view>
            </view>
            <!-- AI 建议展示 -->
            <view v-if="assignAiInfo.rationale" class="assess-ai-box">
              <text class="assess-ai-box-tag">✨ AI推荐{{ assignAiInfo.pack_name ? '「'+assignAiInfo.pack_name+'」' : '' }}（{{ assignAiInfo.source==='llm'?'大模型':'规则引擎' }}，{{ Math.round((assignAiInfo.confidence||0.6)*100) }}%）</text>
              <text class="assess-ai-box-text">{{ assignAiInfo.rationale }}</text>
              <view v-for="s in SCALES_REGISTRY" :key="'r-'+s.key">
                <text v-if="assignAiInfo.per_scale_rationale?.[s.key]" class="assess-scale-reason">{{ s.shortLabel }}：{{ assignAiInfo.per_scale_rationale[s.key] }}</text>
              </view>
            </view>
            <text class="assess-scale-hint">已选 {{ selectedScales.length }} 个量表，预计 {{ estimatedTime }} 分钟</text>
          </view>

          <!-- 问卷区 -->
          <view class="assess-modal-section" v-if="surveyTools.length">
            <view class="assess-survey-header">
              <text class="assess-modal-label">问卷（可选）</text>
              <text class="assess-survey-hint">{{ selectedSurveys.length ? selectedSurveys.length + '份已选' : '可与量表同时分配' }}</text>
            </view>
            <view class="assess-survey-list">
              <view v-for="sv in surveyTools" :key="sv.key"
                class="assess-survey-item"
                :class="{ 'assess-survey-item--active': selectedSurveys.includes(sv.surveyId!),
                           'assess-survey-item--ai': assignAiInfo.suggested_surveys?.some((s:any) => s.id === sv.surveyId) }"
                @tap="selectedSurveys.includes(sv.surveyId!) ? selectedSurveys.splice(selectedSurveys.indexOf(sv.surveyId!),1) : selectedSurveys.push(sv.surveyId!)">
                <view class="assess-survey-check">{{ selectedSurveys.includes(sv.surveyId!) ? '✓' : '' }}</view>
                <view class="assess-survey-info">
                  <text class="assess-survey-title">📝 {{ sv.label }}</text>
                  <text class="assess-survey-reason" v-if="assignAiInfo.suggested_surveys?.find((s:any) => s.id === sv.surveyId)">
                    🤖 {{ assignAiInfo.suggested_surveys.find((s:any) => s.id === sv.surveyId)?.rationale }}
                  </text>
                  <text v-else class="assess-survey-desc">{{ sv.desc }}</text>
                </view>
                <text class="assess-survey-time">{{ sv.time }}min</text>
              </view>
            </view>
          </view>

          <view class="assess-modal-section">
            <text class="assess-modal-label">截止时间</text>
            <picker mode="date" @change="deadline = $event.detail.value">
              <view class="assess-picker">{{ deadline || '选择截止日期（可选）' }}</view>
            </picker>
          </view>

          <view class="assess-modal-section">
            <text class="assess-modal-label">备注</text>
            <textarea class="assess-textarea" placeholder="给学员的备注说明（可选）" v-model="assignNote" maxlength="200" />
          </view>
        </template>

        <view class="assess-modal-actions">
          <view class="assess-modal-btn assess-modal-cancel" @tap="closeAssign">取消</view>
          <view
            class="assess-modal-btn assess-modal-confirm"
            :class="{ 'assess-modal-confirm--off': !selectedStudentObj }"
            @tap="doAssign"
          >确认分配</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'
import { SCALES_REGISTRY, SCALE_PACKS, estimateTime, SCALE_NAME_MAP, loadSurveyTools } from '@/utils/assessmentTools'
import type { ToolDef } from '@/utils/assessmentTools'
import { avatarColor, parseRisk, riskBg } from '@/utils/studentUtils'

const activeTab = ref('all')
const searchText = ref('')
const refreshing = ref(false)
const loading = ref(false)
const assignments = ref<any[]>([])
const studentsData = ref<any[]>([])
const showAssign = ref(false)

// AI 解读状态
const showAiSheet = ref(false)
const aiReport = ref<any>(null)
const aiLoadingId = ref<number | null>(null)

async function openAiReport(item: any) {
  if (aiLoadingId.value) return
  showAiSheet.value = true
  aiReport.value = null
  aiLoadingId.value = item.id
  try {
    // 先尝试获取已有报告
    const cached = await http<any>(`/api/v1/assessment-assignments/${item.id}/ai-report`)
    if (cached.has_report && cached.report) {
      aiReport.value = cached.report
    } else {
      // 触发 AI 解读
      const res = await http<any>(`/api/v1/assessment-assignments/${item.id}/ai-interpret`, { method: 'POST' })
      aiReport.value = res.report
    }
  } catch (e: any) {
    uni.showToast({ title: e?.data?.detail || 'AI解读失败', icon: 'none' })
    showAiSheet.value = false
  } finally {
    aiLoadingId.value = null
  }
}
const selectedStudentObj = ref<any>(null)
const selectedScales = ref<string[]>(['big5', 'ttm7'])
const BATCH_SIZE = 5
const batchIndex = ref(0)
const modalSearchMode = ref(false)
const modalSearchQuery = ref('')
const deadline = ref('')
const assignNote = ref('')

const estimatedTime = computed(() => estimateTime(selectedScales.value))

// AI 量表建议
const assignAiInfo = ref<any>({})
const assignAiLoading = ref(false)

// 问卷
const surveyTools = ref<ToolDef[]>([])
const selectedSurveys = ref<number[]>([])

async function loadAiSuggestion() {
  if (!selectedStudentObj.value || assignAiLoading.value) return
  assignAiLoading.value = true
  try {
    const sid = selectedStudentObj.value.id || selectedStudentObj.value.user_id
    const res = await http<any>(`/api/v1/coach/students/${sid}/ai-assessment-suggestion`, { method: 'POST' })
    assignAiInfo.value = {
      suggested_scales: res.suggested_scales || [],
      per_scale_rationale: res.per_scale_rationale || {},
      pack_name: res.pack_name || '',
      rationale: res.rationale || '',
      confidence: res.confidence ?? 0.6,
      source: res.source || 'rules',
    }
    if (res.suggested_scales?.length) selectedScales.value = [...res.suggested_scales]
    if (res.suggested_surveys?.length) selectedSurveys.value = res.suggested_surveys.map((s: any) => s.id)
  } catch (e: any) {
    uni.showToast({ title: e?.data?.detail || 'AI建议失败', icon: 'none', duration: 2000 })
  } finally {
    assignAiLoading.value = false
  }
}

function isPackSelected(packKey: string): boolean {
  const pack = (SCALE_PACKS as Record<string, { scales: string[] }>)[packKey]
  if (!pack) return false
  return pack.scales.every(k => selectedScales.value.includes(k)) &&
    selectedScales.value.length === pack.scales.length
}
function applyPack(packKey: string) {
  const pack = (SCALE_PACKS as Record<string, { scales: string[] }>)[packKey]
  if (!pack) return
  if (isPackSelected(packKey)) selectedScales.value = []
  else selectedScales.value = [...pack.scales]
}

// 统计 + Tab 合并：单排四格，既是数字展示又是筛选器
const statTabs = computed(() => [
  { key: 'all',       label: '全部', color: '#9B59B6', count: assignments.value.filter(a => a.status !== 'cancelled').length },
  { key: 'pending',   label: '待完成', color: '#E67E22', count: assignments.value.filter(a => a.status === 'pending').length },
  { key: 'review',    label: '待审核', color: '#9B59B6', count: assignments.value.filter(a => a.status === 'completed').length },
  { key: 'completed', label: '已完成', color: '#27AE60', count: assignments.value.filter(a => ['reviewed', 'pushed'].includes(a.status)).length },
])

function formatStudentSub(s: any): string {
  const days = s.days_since_last_contact ?? s.days_no_contact ?? null
  const stage = s.stage_label || s.stage || ''
  if (days === null) return stage || '从未联系'
  if (days > 30) return `${stage} · ${days}天未联系`
  return `${stage} · ${days}天前联系`
}
function selectStudentObj(s: any) {
  selectedStudentObj.value = s
  modalSearchMode.value = false
  modalSearchQuery.value = ''
}
function nextBatch() {
  if (hasNextBatch.value) batchIndex.value += BATCH_SIZE
}
function prevBatch() {
  if (batchIndex.value >= BATCH_SIZE) batchIndex.value -= BATCH_SIZE
}
function closeAssign() {
  showAssign.value = false
  selectedStudentObj.value = null
  batchIndex.value = 0
  modalSearchMode.value = false
  modalSearchQuery.value = ''
  assignAiInfo.value = {}
  selectedSurveys.value = []
}

async function openAssign() {
  showAssign.value = true
  surveyTools.value = await loadSurveyTools()
}

const prioritizedStudents = computed(() => {
  return [...studentsData.value].sort((a: any, b: any) => {
    const ra = parseRisk(a.risk_level), rb = parseRisk(b.risk_level)
    if (rb !== ra) return rb - ra
    const da = a.days_since_last_contact ?? a.days_no_contact ?? 999
    const db = b.days_since_last_contact ?? b.days_no_contact ?? 999
    return db - da
  })
})
const currentBatchStudents = computed(() => {
  if (modalSearchMode.value) {
    const q = modalSearchQuery.value.toLowerCase()
    if (!q) return prioritizedStudents.value.slice(0, BATCH_SIZE)
    return studentsData.value.filter((s: any) =>
      (s.name || s.full_name || '').toLowerCase().includes(q)
    ).slice(0, BATCH_SIZE)
  }
  return prioritizedStudents.value.slice(batchIndex.value, batchIndex.value + BATCH_SIZE)
})
const hasNextBatch = computed(() => batchIndex.value + BATCH_SIZE < prioritizedStudents.value.length)

const filteredItems = computed(() => {
  // 全部Tab不显示已取消，保持列表干净
  let list = assignments.value.filter(a => a.status !== 'cancelled')
  if (activeTab.value !== 'all') {
    if (activeTab.value === 'pending') list = list.filter(a => a.status === 'pending')
    else if (activeTab.value === 'review') list = list.filter(a => a.status === 'completed')
    else if (activeTab.value === 'completed') list = list.filter(a => ['reviewed', 'pushed'].includes(a.status))
  }
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(a => (a.student_name || a.user_name || '').toLowerCase().includes(q))
  }
  return list.sort((a: any, b: any) => {
    const da = a.updated_at || a.created_at || ''
    const db = b.updated_at || b.created_at || ''
    return db.localeCompare(da)
  })
})


function statusColor(s: string): string {
  const map: Record<string, string> = {
    pending: '#E67E22',
    completed: '#9B59B6',
    reviewed: '#27AE60', pushed: '#27AE60',
    cancelled: '#BDC3C7'
  }
  return map[s] || '#8E99A4'
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    pending: '待完成', completed: '待审核',
    reviewed: '已审核', pushed: '已推送', cancelled: '已取消'
  }
  return map[s] || s
}

function formatDate(d: string): string {
  if (!d) return '-'
  return d.slice(0, 10)
}

function formatScales(item: any): string {
  if (item.scale_names) return item.scale_names
  if (item.scales && Array.isArray(item.scales)) {
    return item.scales.map((s: string) => SCALE_NAME_MAP[s] || s).join(' + ')
  }
  return item.assessment_type || '综合评估'
}

function toggleScale(val: string) {
  const idx = selectedScales.value.indexOf(val)
  if (idx >= 0) selectedScales.value.splice(idx, 1)
  else selectedScales.value.push(val)
}

async function loadData() {
  loading.value = true

  // 主数据源: /coach-list 返回教练所有状态的评估任务
  try {
    const res = await http<any>('/api/v1/assessment-assignments/coach-list')
    assignments.value = res.assignments || (Array.isArray(res) ? res : [])
  } catch (e) {
    console.warn('[assessment/index] coach-list:', e)
    // fallback: review-list 只含 completed/reviewed
    try {
      const res2 = await http<any>('/api/v1/assessment-assignments/review-list')
      assignments.value = res2.assignments || res2.items || (Array.isArray(res2) ? res2 : [])
    } catch (e2) { console.warn('[assessment/index] review-list:', e2); assignments.value = [] }
  }

  // 加载学员列表（用于分配弹窗）
  try {
    const res = await http<any>('/api/v1/coach/students')
    studentsData.value = res.students || res.items || (Array.isArray(res) ? res : [])
  } catch (e) {
    console.warn('[assessment/index] students:', e)
    try {
      const dash = await http<any>('/api/v1/coach/dashboard')
      studentsData.value = dash.students || []
    } catch (e2) { console.warn('[assessment/index] dashboard students:', e2); studentsData.value = [] }
  }

  loading.value = false
}

async function doAssign() {
  if (!selectedStudentObj.value) {
    uni.showToast({ title: '请选择学员', icon: 'none' })
    return
  }
  if (selectedScales.value.length === 0 && selectedSurveys.value.length === 0) {
    uni.showToast({ title: '请选择量表或问卷', icon: 'none' })
    return
  }

  const student = selectedStudentObj.value
  const parts: string[] = []
  let ok = true

  if (selectedScales.value.length) {
    try {
      await http('/api/v1/assessment-assignments/assign', {
        method: 'POST',
        data: {
          user_id: student.id || student.user_id,
          student_id: student.id || student.user_id,
          scales: selectedScales.value,
          assessment_type: selectedScales.value.join(','),
          deadline: deadline.value || undefined,
          note: assignNote.value || undefined,
        }
      })
      parts.push(`${selectedScales.value.length}个量表`)
    } catch (e: any) {
      const detail = e?.data?.detail || e?.detail || e?.message || '量表分配失败'
      uni.showToast({ title: detail.slice(0, 20), icon: 'none' }); ok = false
    }
  }

  for (const surveyId of selectedSurveys.value) {
    try {
      await http(`/api/v1/surveys/${surveyId}/assign`, {
        method: 'POST',
        data: { student_ids: [student.id || student.user_id], message: assignNote.value || '' },
      })
    } catch { /* 静默，不阻断 */ }
  }
  if (selectedSurveys.value.length) parts.push(`${selectedSurveys.value.length}份问卷`)

  if (ok) {
    uni.showToast({ title: parts.join(' + ') + ' 已分配', icon: 'success' })
    closeAssign()
    assignNote.value = ''
    deadline.value = ''
    loadData()
  }
}

async function remindStudent(item: any) {
  try {
    await http(`/api/v1/assessment-assignments/${item.id}/remind`, { method: 'POST' })
    uni.showToast({ title: '提醒已发送', icon: 'success' })
  } catch (e: any) {
    console.warn('[assessment/index] remind:', e)
    uni.showToast({ title: e?.data?.detail || '提醒发送失败', icon: 'none' })
  }
}

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }

function goReview(item: any) {
  uni.navigateTo({ url: '/pages/coach/assessment/review?id=' + item.id })
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.assess-page { min-height: 100vh; background: #F5F6FA; }
.assess-navbar { display: flex; align-items: center; padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top)); background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); color: #fff; }
.assess-nav-back { font-size: 40rpx; padding: 16rpx; }
.assess-nav-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.assess-nav-action { font-size: 26rpx; padding: 8rpx 16rpx; background: rgba(255,255,255,0.2); border-radius: 8rpx; }

/* ── 统计+Tab 合并单排 ── */
.assess-stattabs { display: flex; padding: 16rpx 24rpx 12rpx; gap: 12rpx; }
.assess-st { flex: 1; background: #fff; border-radius: 14rpx; padding: 18rpx 8rpx 14rpx; text-align: center; }
.assess-st--active { background: #9B59B6; }
.assess-st-num { display: block; font-size: 36rpx; font-weight: 700; color: #2C3E50; }
.assess-st--active .assess-st-num { color: #fff; }
.assess-st-label { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.assess-st--active .assess-st-label { color: rgba(255,255,255,0.85); }

.assess-search { padding: 12rpx 24rpx; }
.assess-search-input { background: #fff; border-radius: 12rpx; padding: 16rpx 24rpx; font-size: 28rpx; }

.assess-list { height: calc(100vh - 480rpx); padding: 0 24rpx 24rpx; }

.assess-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); }
.assess-card-header { display: flex; align-items: center; gap: 16rpx; }
.assess-card-avatar { width: 72rpx; height: 72rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 30rpx; font-weight: 600; }
.assess-card-info { flex: 1; }
.assess-card-name { display: block; font-size: 30rpx; font-weight: 600; color: #2C3E50; }
.assess-card-scale { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.assess-status-tag { padding: 6rpx 16rpx; border-radius: 8rpx; color: #fff; font-size: 22rpx; white-space: nowrap; }

.assess-card-body { margin-top: 16rpx; }
.assess-card-meta { display: flex; flex-wrap: wrap; gap: 16rpx; }
.assess-meta-item { font-size: 24rpx; color: #8E99A4; }
.assess-card-actions { display: flex; gap: 12rpx; margin-top: 16rpx; justify-content: flex-end; }
.assess-action-btn { padding: 10rpx 24rpx; border-radius: 8rpx; font-size: 24rpx; }
.assess-action-review { background: #9B59B6; color: #fff; }
.assess-action-remind { background: #F0F0F0; color: #E67E22; }
.assess-action-ai { background: linear-gradient(135deg, #1a7a50, #27AE60); color: #fff; }
.assess-action-ai--loading { opacity: 0.6; pointer-events: none; }

/* ── AI 解读底部弹窗 ── */
.assess-ai-sheet { max-height: 88vh; display: flex; flex-direction: column; }
.assess-ai-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20rpx; }
.assess-ai-title { font-size: 32rpx; font-weight: 700; color: #2C3E50; }
.assess-ai-close { font-size: 36rpx; color: #8E99A4; padding: 8rpx; }
.assess-ai-body { flex: 1; overflow-y: auto; }
.assess-ai-section { margin-bottom: 20rpx; }
.assess-ai-label { display: block; font-size: 24rpx; color: #5B6B7F; font-weight: 600; margin-bottom: 8rpx; }
.assess-ai-text { display: block; font-size: 28rpx; color: #2C3E50; line-height: 1.6; }
.assess-ai-hint { background: #f0faf5; padding: 12rpx 16rpx; border-radius: 10rpx; color: #1a7a50; font-weight: 500; }
.assess-ai-tag { display: inline-block; padding: 6rpx 16rpx; border-radius: 8rpx; font-size: 24rpx; margin: 4rpx 6rpx 4rpx 0; }
.assess-ai-tag--green { background: #e8f8f0; color: #27AE60; }
.assess-ai-tag--orange { background: #fff3e6; color: #E67E22; }
.assess-ai-action-item { font-size: 26rpx; color: #2C3E50; padding: 6rpx 0; line-height: 1.5; }
.assess-ai-footer { display: flex; gap: 20rpx; margin-top: 16rpx; padding-top: 12rpx; border-top: 1rpx solid #F0F0F0; }
.assess-ai-source, .assess-ai-conf { font-size: 22rpx; color: #8E99A4; }
.assess-ai-loading { text-align: center; padding: 60rpx 0; font-size: 28rpx; color: #8E99A4; }

.assess-empty { text-align: center; padding: 120rpx 0; }
.assess-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.assess-empty-text { display: block; font-size: 28rpx; color: #8E99A4; margin-bottom: 24rpx; }
.assess-empty-action { display: inline-block; padding: 16rpx 40rpx; background: #9B59B6; color: #fff; border-radius: 12rpx; font-size: 28rpx; }

.assess-loading { text-align: center; padding: 40rpx; color: #8E99A4; font-size: 26rpx; }

.assess-modal-mask { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 999; }
.assess-modal { width: 88%; max-height: 85vh; background: #fff; border-radius: 24rpx; padding: 32rpx; overflow-y: auto; }
.assess-modal-title { display: block; font-size: 32rpx; font-weight: 600; color: #2C3E50; margin-bottom: 24rpx; text-align: center; }
.assess-modal-section { margin-bottom: 24rpx; }
.assess-modal-label { display: block; font-size: 26rpx; color: #5B6B7F; margin-bottom: 12rpx; font-weight: 500; }
.assess-picker { padding: 16rpx 20rpx; background: #F5F6FA; border-radius: 12rpx; font-size: 28rpx; color: #2C3E50; }
.assess-scale-options { display: flex; flex-wrap: wrap; gap: 12rpx; }
.assess-scale-opt { padding: 10rpx 20rpx; border-radius: 8rpx; background: #F0F0F0; font-size: 24rpx; color: #5B6B7F; }
.assess-scale-opt--active { background: #9B59B6; color: #fff; }
.assess-scale-hint { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 12rpx; }
.assess-survey-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.assess-survey-hint { font-size: 22rpx; color: #8E99A4; }
.assess-survey-list { display: flex; flex-direction: column; gap: 8rpx; }
.assess-survey-item { display: flex; align-items: center; gap: 12rpx; padding: 14rpx 12rpx; background: #F8F9FA; border-radius: 12rpx; border: 2rpx solid transparent; }
.assess-survey-item--active { background: #F0FFF8; border-color: #2D8E69; }
.assess-survey-item--ai { border-color: #E67E22; }
.assess-survey-check { width: 36rpx; height: 36rpx; border-radius: 8rpx; border: 2rpx solid #CCC; display: flex; align-items: center; justify-content: center; font-size: 22rpx; color: #2D8E69; font-weight: 700; flex-shrink: 0; }
.assess-survey-item--active .assess-survey-check { background: #2D8E69; border-color: #2D8E69; color: #fff; }
.assess-survey-info { flex: 1; }
.assess-survey-title { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; }
.assess-survey-desc { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.assess-survey-reason { display: block; font-size: 22rpx; color: #E67E22; margin-top: 4rpx; }
.assess-survey-time { font-size: 22rpx; color: #8E99A4; white-space: nowrap; flex-shrink: 0; }
.assess-textarea { width: 100%; height: 120rpx; padding: 16rpx; background: #F5F6FA; border-radius: 12rpx; font-size: 26rpx; }
.assess-modal-actions { display: flex; gap: 16rpx; margin-top: 24rpx; }
.assess-modal-btn { flex: 1; text-align: center; padding: 20rpx 0; border-radius: 12rpx; font-size: 28rpx; }
.assess-modal-cancel { background: #F0F0F0; color: #5B6B7F; }
.assess-modal-confirm { background: #9B59B6; color: #fff; }
.assess-modal-confirm--off { background: #C0C0C0; pointer-events: none; }

/* ── 学员选择器 ── */
.assess-modal-hrow { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12rpx; }
.assess-search-toggle { font-size: 24rpx; color: #9B59B6; padding: 6rpx 16rpx; background: #F5F0FF; border-radius: 8rpx; }
.assess-modal-searchbox { margin-bottom: 12rpx; }
.assess-modal-sinput { width: 100%; padding: 14rpx 20rpx; background: #F5F6FA; border-radius: 12rpx; font-size: 28rpx; box-sizing: border-box; }

.assess-student-cards { display: flex; flex-direction: column; gap: 10rpx; }
.assess-sc-card { display: flex; align-items: center; gap: 16rpx; padding: 16rpx; background: #F8F9FA; border-radius: 14rpx; border: 2rpx solid transparent; }
.assess-sc-card:active { border-color: #9B59B6; background: #F5F0FF; }
.assess-sc-avatar { width: 64rpx; height: 64rpx; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 26rpx; font-weight: 600; flex-shrink: 0; }
.assess-sc-info { flex: 1; }
.assess-sc-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.assess-sc-sub { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.assess-sc-risk { padding: 4rpx 12rpx; border-radius: 6rpx; color: #fff; font-size: 22rpx; font-weight: 600; flex-shrink: 0; }
.assess-sc-empty { text-align: center; padding: 40rpx 0; font-size: 26rpx; color: #8E99A4; }

/* ── 批次导航 ── */
.assess-batch-nav { display: flex; align-items: center; justify-content: space-between; padding: 12rpx 0; margin-top: 8rpx; }
.assess-batch-btn { font-size: 24rpx; color: #9B59B6; padding: 8rpx 20rpx; background: #F5F0FF; border-radius: 8rpx; }
.assess-batch-btn--off { color: #C0C0C0; background: #F5F5F5; pointer-events: none; }
.assess-batch-info { font-size: 24rpx; color: #8E99A4; }

/* ── 已选学员卡片 ── */
.assess-selected-card { display: flex; align-items: center; gap: 16rpx; padding: 16rpx; background: #F5F0FF; border-radius: 14rpx; border: 2rpx solid #9B59B6; }
.assess-reselect { font-size: 24rpx; color: #9B59B6; }

/* ── AI 量表建议 ── */
.assess-ai-suggest-btn { padding: 8rpx 20rpx; background: linear-gradient(135deg, #1a7a50, #27AE60); color: #fff; border-radius: 10rpx; font-size: 24rpx; font-weight: 600; }
.assess-ai-suggest-btn--loading { background: #8DC9B3; pointer-events: none; }
.assess-pack-row { display: flex; gap: 10rpx; flex-wrap: wrap; margin-bottom: 12rpx; }
.assess-pack-chip { padding: 8rpx 22rpx; border-radius: 28rpx; font-size: 24rpx; background: #F0F0F0; color: #5B6B7F; }
.assess-pack-chip--active { background: #9B59B6; color: #fff; }
.assess-scale-opt--ai { border: 2rpx solid #F39C12 !important; background: #FFF9EC; }
.assess-ai-box { margin-top: 12rpx; padding: 16rpx 20rpx; background: linear-gradient(135deg, #f0faf5, #eaf6ff); border-radius: 12rpx; border-left: 4rpx solid #27AE60; }
.assess-ai-box-tag { display: block; font-size: 22rpx; font-weight: 700; color: #1a7a50; margin-bottom: 6rpx; }
.assess-ai-box-text { display: block; font-size: 24rpx; color: #2C3E50; line-height: 1.5; margin-bottom: 4rpx; }
.assess-scale-reason { display: block; font-size: 22rpx; color: #E67E22; margin-top: 4rpx; }
</style>