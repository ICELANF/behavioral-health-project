<template>
  <view class="cf-page">

    <!-- 导航栏 -->
    <view class="cf-navbar">
      <view class="cf-navbar__back" @tap="goBack"><text class="cf-navbar__arrow">&#8249;</text></view>
      <text class="cf-navbar__title">AI 飞轮</text>
      <view class="cf-navbar__refresh" @tap="refreshAll"><text>↻</text></view>
    </view>

    <!-- 飞轮可视化 -->
    <view class="cf-wheel">
      <view class="cf-wheel__center">
        <text class="cf-wheel__icon">🤖</text>
        <text class="cf-wheel__label">AI飞轮</text>
      </view>
      <view class="cf-wheel__steps">
        <view class="cf-wheel__step" v-for="(s, i) in WHEEL_STEPS" :key="i" :class="{ 'cf-wheel__step--active': s.active }" @tap="onStepTap(i)">
          <text class="cf-wheel__step-icon">{{ s.icon }}</text>
          <text class="cf-wheel__step-text">{{ s.label }}</text>
          <text class="cf-wheel__step-count" v-if="s.count > 0">{{ s.count }}</text>
        </view>
      </view>
    </view>

    <!-- 统计栏 -->
    <view class="cf-stats">
      <view class="cf-stat">
        <text class="cf-stat__val cf-stat__val--orange">{{ stats.pending }}</text>
        <text class="cf-stat__label">待审核</text>
      </view>
      <view class="cf-stat">
        <text class="cf-stat__val cf-stat__val--green">{{ stats.approved }}</text>
        <text class="cf-stat__label">已通过</text>
      </view>
      <view class="cf-stat">
        <text class="cf-stat__val cf-stat__val--red">{{ stats.rejected }}</text>
        <text class="cf-stat__label">已退回</text>
      </view>
      <view class="cf-stat">
        <text class="cf-stat__val cf-stat__val--blue">{{ stats.ai_runs }}</text>
        <text class="cf-stat__label">AI运行</text>
      </view>
    </view>

    <!-- Tab 筛选 -->
    <view class="cf-tabs">
      <view v-for="tab in TABS" :key="tab.key" class="cf-tab" :class="{ 'cf-tab--active': activeTab === tab.key }" @tap="activeTab = tab.key">
        <text>{{ tab.label }}</text>
        <view class="cf-tab__badge" v-if="getTabCount(tab.key) > 0"><text>{{ getTabCount(tab.key) }}</text></view>
      </view>
    </view>

    <!-- 审核队列 -->
    <scroll-view scroll-y class="cf-body" refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">

      <!-- 待审核 Tab -->
      <template v-if="activeTab === 'pending'">
        <!-- 批量操作 -->
        <view class="cf-batch" v-if="pendingItems.length > 1">
          <text class="cf-batch__count">{{ pendingItems.length }} 条待审核</text>
          <view class="cf-batch__btn" @tap="batchApprove"><text>全部通过</text></view>
        </view>

        <template v-if="loading">
          <view class="bhp-skeleton" v-for="i in 3" :key="i" style="height: 200rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
        </template>

        <template v-else-if="pendingItems.length">
          <view v-for="item in pendingItems" :key="item.id" class="cf-card">
            <view class="cf-card__header">
              <text class="cf-card__name">{{ item.student_name || '学员' }}</text>
              <view class="cf-card__type" :class="`cf-card__type--${item.type || 'push'}`">
                <text>{{ TYPE_LABEL[item.type] || item.type || '推送' }}</text>
              </view>
              <view class="cf-card__priority" v-if="item.priority === 'urgent'"><text>🔴 紧急</text></view>
            </view>

            <!-- AI 摘要 -->
            <text class="cf-card__summary" v-if="item.ai_summary">{{ item.ai_summary }}</text>

            <!-- 标题 + 内容 -->
            <view class="cf-card__content" v-if="item.content_title || item.content_body">
              <text class="cf-card__content-title" v-if="item.content_title">{{ item.content_title }}</text>
              <view class="cf-card__content-body" @tap="toggleExpand(item)">
                <text :class="item._expanded ? '' : 'cf-card__content-collapsed'">{{ item.content_body || item.ai_draft || '' }}</text>
                <text class="cf-card__expand-hint">{{ item._expanded ? '收起 ▲' : '展开 ▼' }}</text>
              </view>
            </view>

            <!-- AI 草稿 (fallback) -->
            <view class="cf-card__draft" v-else-if="item.ai_draft" @tap="toggleExpand(item)">
              <text class="cf-card__draft-label">AI 草稿 {{ item._expanded ? '▼' : '▶' }}</text>
              <text class="cf-card__draft-text" :class="{ 'cf-card__draft-text--collapsed': !item._expanded }">{{ item.ai_draft }}</text>
            </view>

            <!-- 处方字段 -->
            <view class="cf-card__rx" v-if="item.rx_fields && item._expanded">
              <view v-for="(val, key) in item.rx_fields" :key="key" class="cf-card__rx-row">
                <text class="cf-card__rx-key">{{ key }}</text>
                <text class="cf-card__rx-val">{{ val }}</text>
              </view>
            </view>

            <!-- 来源标记 -->
            <view class="cf-card__source" v-if="item.source_type">
              <text>来源: {{ SOURCE_LABEL[item.source_type] || item.source_type }}</text>
            </view>

            <!-- 操作按钮 -->
            <view class="cf-card__actions">
              <view class="cf-btn cf-btn--approve" @tap="handleApprove(item)"><text>✓ 通过</text></view>
              <view class="cf-btn cf-btn--edit" @tap="openEditModal(item)" v-if="item.content_title || item.ai_draft"><text>✎ 编辑</text></view>
              <view class="cf-btn cf-btn--reject" @tap="openRejectModal(item)"><text>✗ 退回</text></view>
            </view>

            <!-- 等待时间 -->
            <text class="cf-card__wait" v-if="item.wait_seconds > 0">等待 {{ formatWait(item.wait_seconds) }}</text>
          </view>
        </template>

        <view v-else class="cf-empty">
          <text class="cf-empty__icon">✓</text>
          <text class="cf-empty__title">审核已全部完成</text>
          <text class="cf-empty__sub">新的AI建议将自动出现在这里</text>
        </view>
      </template>

      <!-- 已处理 Tab -->
      <template v-if="activeTab === 'handled'">
        <template v-if="handledItems.length">
          <view v-for="item in handledItems" :key="item.id" class="cf-card cf-card--done">
            <view class="cf-card__done-badge" :class="item._action === 'approved' ? 'cf-card__done-badge--green' : 'cf-card__done-badge--red'">
              <text>{{ item._action === 'approved' ? '已通过 ✓' : '已退回 ✗' }}</text>
            </view>
            <view class="cf-card__header">
              <text class="cf-card__name">{{ item.student_name || '学员' }}</text>
              <view class="cf-card__type" :class="`cf-card__type--${item.type || 'push'}`">
                <text>{{ TYPE_LABEL[item.type] || '推送' }}</text>
              </view>
            </view>
            <text class="cf-card__summary" v-if="item.ai_summary">{{ item.ai_summary }}</text>
          </view>
        </template>
        <view v-else class="cf-empty">
          <text class="cf-empty__icon">📋</text>
          <text class="cf-empty__title">暂无已处理记录</text>
        </view>
      </template>

      <!-- AI 历史 Tab -->
      <template v-if="activeTab === 'ai_history'">
        <template v-if="aiHistory.length">
          <view v-for="(run, i) in aiHistory" :key="i" class="cf-ai-card">
            <view class="cf-ai-card__header">
              <text class="cf-ai-card__name">{{ run.student_name }}</text>
              <text class="cf-ai-card__time">{{ formatDate(run.created_at) }}</text>
            </view>
            <view class="cf-ai-card__confidence" v-if="run.confidence != null">
              <text class="cf-ai-card__conf-label">置信度</text>
              <view class="cf-ai-card__conf-bar">
                <view class="cf-ai-card__conf-fill" :style="{ width: Math.round(run.confidence * 100) + '%' }"></view>
              </view>
              <text class="cf-ai-card__conf-val">{{ Math.round(run.confidence * 100) }}%</text>
            </view>
            <view class="cf-ai-card__suggestions" v-if="run.suggestions?.length">
              <view v-for="(sug, j) in run.suggestions.slice(0, 3)" :key="j" class="cf-ai-card__sug">
                <text class="cf-ai-card__sug-idx">{{ j + 1 }}</text>
                <text class="cf-ai-card__sug-text">{{ sug.text || sug.content || sug }}</text>
              </view>
            </view>
          </view>
        </template>
        <view v-else class="cf-empty">
          <text class="cf-empty__icon">🤖</text>
          <text class="cf-empty__title">暂无AI运行记录</text>
          <text class="cf-empty__sub">点击下方按钮生成跟进计划</text>
        </view>
      </template>

    </scroll-view>

    <!-- 底部生成按钮 -->
    <view class="cf-footer">
      <view class="cf-gen-btn" @tap="showStudentPicker = true" :class="{ 'cf-gen-btn--loading': generating }">
        <text class="cf-gen-btn__text">{{ generating ? '🤖 AI 分析中...' : '🚀 生成跟进计划' }}</text>
      </view>
    </view>

    <!-- 学员选择器弹窗 -->
    <view class="cf-modal-mask" v-if="showStudentPicker" @tap="showStudentPicker = false">
      <view class="cf-modal" @tap.stop>
        <text class="cf-modal__title">选择学员生成跟进计划</text>
        <picker :range="studentNames" @change="onPickStudent">
          <view class="cf-picker-trigger">
            <text>{{ pickedStudent ? pickedStudent.name : '请选择学员' }}</text>
            <text class="cf-picker-trigger__arrow">▼</text>
          </view>
        </picker>
        <!-- 自定义指令 -->
        <view class="cf-modal__field">
          <text class="cf-modal__label">AI 指令（可选）</text>
          <textarea class="cf-modal__input" v-model="agentPrompt" placeholder="例: 重点关注血糖控制和运动习惯" :maxlength="200" style="min-height: 120rpx;" />
        </view>
        <view class="cf-modal__actions">
          <view class="cf-modal__btn cf-modal__btn--cancel" @tap="showStudentPicker = false"><text>取消</text></view>
          <view class="cf-modal__btn cf-modal__btn--confirm" @tap="runFollowup"><text>开始生成</text></view>
        </view>
      </view>
    </view>

    <!-- AI 结果弹窗 -->
    <view class="cf-modal-mask" v-if="agentResult" @tap="agentResult = null">
      <view class="cf-modal cf-modal--result" @tap.stop>
        <text class="cf-modal__title">🤖 AI 跟进建议</text>
        <view class="cf-result-confidence" v-if="agentResult.confidence != null">
          <text class="cf-result-confidence__label">置信度</text>
          <text class="cf-result-confidence__val">{{ Math.round((agentResult.confidence || 0) * 100) }}%</text>
        </view>
        <view class="cf-result-list">
          <view v-for="(sug, idx) in (agentResult.suggestions || [])" :key="idx" class="cf-result-item">
            <view class="cf-result-item__idx"><text>{{ idx + 1 }}</text></view>
            <view class="cf-result-item__body">
              <text class="cf-result-item__text">{{ sug.text || sug.content || sug }}</text>
              <view class="cf-result-item__apply" @tap.stop="applySuggestion(sug)"><text>应用此建议 →</text></view>
            </view>
          </view>
          <view v-if="!(agentResult.suggestions || []).length && agentResult.output" class="cf-result-raw">
            <text>{{ agentResult.output }}</text>
          </view>
          <view v-else-if="!(agentResult.suggestions || []).length" class="cf-empty-inline"><text>AI 暂无具体建议</text></view>
        </view>
        <view class="cf-modal__actions">
          <view class="cf-modal__btn cf-modal__btn--cancel" @tap.stop="agentResult = null"><text>关闭</text></view>
          <view class="cf-modal__btn cf-modal__btn--confirm" @tap.stop="applyAllSuggestions"><text>全部应用</text></view>
        </view>
      </view>
    </view>

    <!-- 退回原因弹窗 -->
    <view class="cf-modal-mask" v-if="rejectTarget" @tap="rejectTarget = null">
      <view class="cf-modal" @tap.stop>
        <text class="cf-modal__title">退回原因</text>
        <textarea class="cf-modal__input" v-model="rejectReason" placeholder="请输入退回原因（AI将学习改进）..." :maxlength="200" />
        <view class="cf-modal__actions">
          <view class="cf-modal__btn cf-modal__btn--cancel" @tap="rejectTarget = null"><text>取消</text></view>
          <view class="cf-modal__btn cf-modal__btn--ok" @tap="confirmReject"><text>确认退回</text></view>
        </view>
      </view>
    </view>

    <!-- 编辑弹窗 -->
    <view class="cf-modal-mask" v-if="editTarget" @tap="editTarget = null">
      <view class="cf-modal" @tap.stop>
        <text class="cf-modal__title">编辑后通过</text>
        <view class="cf-modal__field">
          <text class="cf-modal__label">标题</text>
          <input class="cf-modal__text-input" v-model="editTitle" />
        </view>
        <view class="cf-modal__field">
          <text class="cf-modal__label">内容</text>
          <textarea class="cf-modal__input" v-model="editContent" :maxlength="500" />
        </view>
        <view class="cf-modal__actions">
          <view class="cf-modal__btn cf-modal__btn--cancel" @tap="editTarget = null"><text>取消</text></view>
          <view class="cf-modal__btn cf-modal__btn--confirm" @tap="confirmEdit"><text>修改并通过</text></view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

// ============================================================
// 内联 HTTP
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
          reject({ statusCode: res.statusCode, data: e })
        }
      },
      fail(err) { reject(err) },
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
function _post<T = any>(path: string, data?: any): Promise<T> { return _request<T>('POST', path, data) }

// 多端点 fallback
async function tryGet<T = any>(paths: string[], params?: Record<string, any>): Promise<T | null> {
  for (const p of paths) {
    try { return await _get<T>(p, params) } catch {}
  }
  return null
}

// ============================================================
// 常量
// ============================================================
const TABS = [
  { key: 'pending',    label: '待审核' },
  { key: 'handled',    label: '已处理' },
  { key: 'ai_history', label: 'AI记录' },
]

const TYPE_LABEL: Record<string, string> = {
  rx_push: '处方推送', prescription: '行为处方', assessment: '评估审核',
  ai_reply: 'AI回复', push: '内容推送', followup: '跟进计划', alert: '风险预警',
}

const SOURCE_LABEL: Record<string, string> = {
  ai_recommendation: 'AI推荐', assessment_trigger: '评估触发',
  manual: '手动创建', system: '系统生成', behavior_rx: '行为处方',
}

// ============================================================
// 状态
// ============================================================
const activeTab      = ref('pending')
const loading        = ref(false)
const refreshing     = ref(false)
const queue          = ref<any[]>([])
const handledItems   = ref<any[]>([])
const aiHistory      = ref<any[]>([])
const stats          = ref({ pending: 0, approved: 0, rejected: 0, ai_runs: 0 })
const rejectTarget   = ref<any>(null)
const rejectReason   = ref('')
const editTarget     = ref<any>(null)
const editTitle      = ref('')
const editContent    = ref('')
const showStudentPicker = ref(false)
const studentList    = ref<any[]>([])
const pickedStudent  = ref<any>(null)
const agentPrompt    = ref('')
const generating     = ref(false)
const agentResult    = ref<any>(null)
let refreshTimer: any = null

const studentNames = computed(() => studentList.value.map(s => s.name))

const pendingItems = computed(() => queue.value.filter(i => !i._handled))

// 飞轮步骤
const WHEEL_STEPS = computed(() => [
  { icon: '📊', label: '数据采集', active: true, count: 0 },
  { icon: '🤖', label: 'AI分析', active: generating.value, count: stats.value.ai_runs },
  { icon: '📋', label: '教练审核', active: stats.value.pending > 0, count: stats.value.pending },
  { icon: '📤', label: '推送执行', active: false, count: stats.value.approved },
  { icon: '📈', label: '效果追踪', active: false, count: 0 },
])

function getTabCount(key: string): number {
  if (key === 'pending') return pendingItems.value.length
  if (key === 'handled') return handledItems.value.length
  if (key === 'ai_history') return aiHistory.value.length
  return 0
}

// ============================================================
// 生命周期
// ============================================================
onMounted(() => {
  loadAll()
  // 30秒自动刷新待审核
  refreshTimer = setInterval(() => { if (activeTab.value === 'pending') loadQueue() }, 30000)
})

onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })

async function loadAll() {
  await Promise.all([loadQueue(), loadStats(), loadStudentList()])
}

async function refreshAll() {
  uni.showToast({ title: '刷新中...', icon: 'none', duration: 800 })
  await loadAll()
}

async function onRefresh() {
  refreshing.value = true
  await loadAll()
  refreshing.value = false
}

// ============================================================
// 数据加载 — 多端点 fallback
// ============================================================
async function loadQueue() {
  loading.value = true
  try {
    // 尝试多个可能的端点
    const res = await tryGet<any>([
      '/v1/coach/review-queue',
      '/v1/coach-push/pending',
    ], { page_size: 50 })

    if (res) {
      const items = res.items || res.results || []
      queue.value = items.map((item: any) => ({
        ...item,
        student_name: item.student_name || item.target_name || '学员',
        _handled: false, _action: '', _expanded: false,
      }))
    } else {
      queue.value = []
    }
  } catch { queue.value = [] }
  finally { loading.value = false }
}

async function loadStats() {
  try {
    const res = await tryGet<any>(['/v1/coach/stats/today', '/v1/coach/dashboard'])
    if (res) {
      const ts = res.today_stats || res
      stats.value = {
        pending: ts.pending ?? ts.pending_followups ?? pendingItems.value.length,
        approved: ts.approved ?? 0,
        rejected: ts.rejected ?? 0,
        ai_runs: ts.ai_runs ?? ts.ai_followups ?? 0,
      }
    }
  } catch {}
}

async function loadStudentList() {
  try {
    const res = await tryGet<any>(['/v1/coach/students', '/v1/coach/dashboard'])
    const list = res?.students || res?.items || []
    studentList.value = list.map((s: any) => ({ ...s, name: s.name || s.full_name || s.username }))
  } catch { studentList.value = [] }
}

// ============================================================
// 审核操作
// ============================================================
async function handleApprove(item: any) {
  try {
    // 尝试多个审核端点
    try { await _post(`/v1/coach/review/${item.id}/approve`, {}) }
    catch { await _post(`/v1/coach-push/${item.id}/approve`, {}) }

    item._handled = true; item._action = 'approved'
    handledItems.value.unshift({ ...item })
    stats.value.approved++; stats.value.pending = Math.max(0, stats.value.pending - 1)
    uni.showToast({ title: '已通过', icon: 'success' })
  } catch { uni.showToast({ title: '操作失败', icon: 'none' }) }
}

function openRejectModal(item: any) { rejectTarget.value = item; rejectReason.value = '' }

async function confirmReject() {
  if (!rejectReason.value.trim()) { uni.showToast({ title: '请输入退回原因', icon: 'none' }); return }
  const item = rejectTarget.value
  try {
    try { await _post(`/v1/coach/review/${item.id}/reject`, { reason: rejectReason.value }) }
    catch { await _post(`/v1/coach-push/${item.id}/reject`, { reason: rejectReason.value }) }

    item._handled = true; item._action = 'rejected'
    handledItems.value.unshift({ ...item })
    stats.value.rejected++; stats.value.pending = Math.max(0, stats.value.pending - 1)
    rejectTarget.value = null
    uni.showToast({ title: '已退回', icon: 'none' })
  } catch { uni.showToast({ title: '操作失败', icon: 'none' }) }
}

function openEditModal(item: any) {
  editTarget.value = item
  editTitle.value = item.content_title || ''
  editContent.value = item.content_body || item.ai_draft || ''
}

async function confirmEdit() {
  const item = editTarget.value
  try {
    try { await _post(`/v1/coach/review/${item.id}/approve`, { edited_title: editTitle.value, edited_content: editContent.value }) }
    catch { await _post(`/v1/coach-push/${item.id}/approve`, { edited_title: editTitle.value, edited_content: editContent.value }) }

    item._handled = true; item._action = 'approved'
    handledItems.value.unshift({ ...item })
    editTarget.value = null
    uni.showToast({ title: '已修改并通过', icon: 'success' })
  } catch { uni.showToast({ title: '操作失败', icon: 'none' }) }
}

async function batchApprove() {
  const items = pendingItems.value
  if (!items.length) return
  uni.showModal({
    title: '批量通过', content: `确认通过全部 ${items.length} 条？`, confirmColor: '#10b981',
    success: async (res) => {
      if (!res.confirm) return
      let ok = 0
      for (const item of items) {
        try {
          try { await _post(`/v1/coach/review/${item.id}/approve`, {}) }
          catch { await _post(`/v1/coach-push/${item.id}/approve`, {}) }
          item._handled = true; item._action = 'approved'
          handledItems.value.unshift({ ...item }); ok++
        } catch {}
      }
      stats.value.approved += ok; stats.value.pending = Math.max(0, stats.value.pending - ok)
      uni.showToast({ title: `已通过 ${ok} 条`, icon: 'success' })
    },
  })
}

// ============================================================
// AI 操作
// ============================================================
function onPickStudent(e: any) { pickedStudent.value = studentList.value[Number(e.detail.value)] || null }

async function runFollowup() {
  if (!pickedStudent.value) { uni.showToast({ title: '请选择学员', icon: 'none' }); return }
  showStudentPicker.value = false; generating.value = true
  try {
    const prompt = agentPrompt.value.trim() || '为学员生成个性化跟进计划'
    const res = await _post<any>('/v1/agent/run', {
      agent_type: 'COACHING', user_id: String(pickedStudent.value.id), input: prompt,
    })
    const result = res.data || res
    agentResult.value = result
    // 记录到AI历史
    aiHistory.value.unshift({
      student_name: pickedStudent.value.name,
      created_at: new Date().toISOString(),
      confidence: result.confidence,
      suggestions: result.suggestions || [],
    })
    stats.value.ai_runs++
  } catch { uni.showToast({ title: '生成失败', icon: 'none' }) }
  finally { generating.value = false; agentPrompt.value = '' }
}

function applySuggestion(sug: any) {
  const text = sug.text || sug.content || String(sug)
  uni.showActionSheet({
    itemList: ['创建推送草稿', '复制文本'],
    success(res) {
      if (res.tapIndex === 0) {
        agentResult.value = null
        setTimeout(() => {
          uni.navigateTo({ url: `/pages/coach/push-queue?draft=${encodeURIComponent(text)}` })
        }, 200)
      } else {
        uni.setClipboardData({ data: text })
        uni.showToast({ title: '已复制', icon: 'success' })
      }
    }
  })
}

function applyAllSuggestions() {
  const all = (agentResult.value?.suggestions || []).map((s: any) => s.text || s.content || String(s)).join('\n\n')
  agentResult.value = null
  if (all) {
    setTimeout(() => {
      uni.setClipboardData({ data: all })
      uni.showToast({ title: '全部建议已复制', icon: 'success' })
    }, 200)
  }
}

// ============================================================
// 工具
// ============================================================
function onStepTap(i: number) {
  if (i === 0) { uni.showToast({ title: '数据持续采集中', icon: 'none' }) }
  else if (i === 1) { showStudentPicker.value = true; uni.showToast({ title: '选择学员开始AI分析', icon: 'none', duration: 1000 }) }
  else if (i === 2) { activeTab.value = 'pending'; uni.showToast({ title: '已切换到待审核', icon: 'none', duration: 800 }) }
  else if (i === 3) { activeTab.value = 'handled'; uni.showToast({ title: '已切换到已处理', icon: 'none', duration: 800 }) }
  else if (i === 4) { activeTab.value = 'ai_history'; uni.showToast({ title: '已切换到AI记录', icon: 'none', duration: 800 }) }
}

function toggleExpand(item: any) { item._expanded = !item._expanded }

function formatWait(s: number): string {
  if (s < 60) return `${s}秒`
  if (s < 3600) return `${Math.floor(s / 60)}分钟`
  return `${Math.floor(s / 3600)}小时`
}

function formatDate(dt: string): string {
  if (!dt) return ''
  return dt.slice(0, 16).replace('T', ' ')
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.cf-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

/* 导航 */
.cf-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; padding-top: calc(88rpx + env(safe-area-inset-top));
  background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.cf-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; }
.cf-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.cf-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.cf-navbar__refresh { font-size: 36rpx; color: var(--bhp-primary-500, #10b981); width: 64rpx; text-align: center; }

/* 飞轮可视化 */
.cf-wheel { background: var(--surface); padding: 20rpx 32rpx; border-bottom: 1px solid var(--border-light); }
.cf-wheel__center { display: flex; align-items: center; gap: 8rpx; margin-bottom: 16rpx; }
.cf-wheel__icon { font-size: 32rpx; }
.cf-wheel__label { font-size: 26rpx; font-weight: 700; color: var(--text-primary); }
.cf-wheel__steps { display: flex; gap: 8rpx; }
.cf-wheel__step {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4rpx;
  padding: 12rpx 4rpx; border-radius: var(--radius-md); background: var(--surface-secondary);
  position: relative;
}
.cf-wheel__step--active { background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); }
.cf-wheel__step:active { opacity: 0.6; transform: scale(0.95); }
.cf-wheel__step-icon { font-size: 24rpx; }
.cf-wheel__step-text { font-size: 18rpx; color: var(--text-tertiary); }
.cf-wheel__step--active .cf-wheel__step-text { color: #059669; font-weight: 600; }
.cf-wheel__step-count {
  position: absolute; top: -8rpx; right: -4rpx; min-width: 28rpx; height: 28rpx;
  border-radius: 14rpx; background: #ef4444; color: #fff; font-size: 18rpx; font-weight: 700;
  display: flex; align-items: center; justify-content: center; padding: 0 6rpx;
}

/* 统计 */
.cf-stats { display: flex; background: var(--surface); padding: 20rpx 32rpx; border-bottom: 1px solid var(--border-light); gap: 8rpx; }
.cf-stat { flex: 1; text-align: center; }
.cf-stat__val { display: block; font-size: 36rpx; font-weight: 800; }
.cf-stat__val--orange { color: #f59e0b; } .cf-stat__val--green { color: #10b981; } .cf-stat__val--red { color: #ef4444; } .cf-stat__val--blue { color: #3b82f6; }
.cf-stat__label { display: block; font-size: 20rpx; color: var(--text-secondary); margin-top: 2rpx; }

/* Tab */
.cf-tabs { display: flex; background: var(--surface); padding: 0 24rpx; border-bottom: 1px solid var(--border-light); }
.cf-tab {
  flex: 1; text-align: center; padding: 18rpx 0; font-size: 24rpx; font-weight: 500;
  color: var(--text-secondary); border-bottom: 3px solid transparent; position: relative;
}
.cf-tab--active { color: var(--bhp-primary-500, #10b981); border-bottom-color: var(--bhp-primary-500, #10b981); font-weight: 700; }
.cf-tab__badge {
  position: absolute; top: 8rpx; right: calc(50% - 48rpx);
  min-width: 28rpx; height: 28rpx; border-radius: 14rpx; background: #ef4444; color: #fff;
  font-size: 18rpx; font-weight: 700; display: flex; align-items: center; justify-content: center; padding: 0 6rpx;
}

/* 主体 */
.cf-body { flex: 1; padding: 20rpx 32rpx 160rpx; }

/* 批量 */
.cf-batch { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16rpx; }
.cf-batch__count { font-size: 24rpx; color: var(--text-secondary); }
.cf-batch__btn { font-size: 22rpx; font-weight: 600; color: #fff; background: #10b981; padding: 8rpx 24rpx; border-radius: var(--radius-full); }

/* 卡片 */
.cf-card { position: relative; background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; margin-bottom: 20rpx; border: 1px solid var(--border-light); overflow: hidden; }
.cf-card--done { opacity: 0.55; }
.cf-card__done-badge { position: absolute; top: 16rpx; right: 16rpx; font-size: 22rpx; font-weight: 700; padding: 4rpx 14rpx; border-radius: var(--radius-full); }
.cf-card__done-badge--green { background: #f0fdf4; color: #16a34a; }
.cf-card__done-badge--red { background: #fef2f2; color: #dc2626; }
.cf-card__header { display: flex; align-items: center; gap: 12rpx; margin-bottom: 12rpx; flex-wrap: wrap; }
.cf-card__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.cf-card__type { font-size: 20rpx; font-weight: 600; padding: 4rpx 14rpx; border-radius: var(--radius-full); }
.cf-card__type--rx_push, .cf-card__type--prescription { background: #eff6ff; color: #2563eb; }
.cf-card__type--assessment { background: #faf5ff; color: #7c3aed; }
.cf-card__type--ai_reply, .cf-card__type--followup { background: #f0fdf4; color: #16a34a; }
.cf-card__type--push { background: #fffbeb; color: #d97706; }
.cf-card__type--alert { background: #fef2f2; color: #dc2626; }
.cf-card__priority { font-size: 18rpx; font-weight: 700; padding: 2rpx 12rpx; border-radius: var(--radius-full); background: #fef2f2; color: #dc2626; }
.cf-card__summary { display: block; font-size: 24rpx; color: var(--text-tertiary); line-height: 1.5; margin-bottom: 12rpx; }

/* 内容 */
.cf-card__content { background: var(--surface-secondary); border-radius: var(--radius-md); padding: 16rpx 20rpx; margin-bottom: 12rpx; }
.cf-card__content-title { display: block; font-size: 26rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 8rpx; }
.cf-card__content-collapsed { overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.cf-card__content-body { font-size: 24rpx; color: var(--text-secondary); line-height: 1.6; }
.cf-card__expand-hint { display: block; font-size: 20rpx; color: var(--bhp-primary-500, #10b981); margin-top: 8rpx; font-weight: 600; }

/* 草稿 */
.cf-card__draft { background: var(--surface-secondary); border-radius: var(--radius-md); padding: 16rpx 20rpx; margin-bottom: 12rpx; }
.cf-card__draft-label { display: block; font-size: 22rpx; font-weight: 600; color: var(--text-secondary); margin-bottom: 8rpx; }
.cf-card__draft-text { display: block; font-size: 26rpx; color: var(--text-primary); line-height: 1.6; white-space: pre-wrap; }
.cf-card__draft-text--collapsed { overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; white-space: normal; }

/* 处方字段 */
.cf-card__rx { margin-bottom: 12rpx; }
.cf-card__rx-row { display: flex; gap: 12rpx; padding: 6rpx 0; border-bottom: 1px solid var(--border-light); }
.cf-card__rx-row:last-child { border-bottom: none; }
.cf-card__rx-key { font-size: 22rpx; color: var(--text-secondary); width: 160rpx; flex-shrink: 0; }
.cf-card__rx-val { font-size: 22rpx; color: var(--text-primary); flex: 1; }

.cf-card__source { font-size: 20rpx; color: var(--text-tertiary); margin-bottom: 8rpx; }

/* 操作按钮 */
.cf-card__actions { display: flex; gap: 12rpx; margin-top: 16rpx; }
.cf-btn { flex: 1; height: 68rpx; border-radius: var(--radius-lg); display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 700; }
.cf-btn:active { opacity: 0.8; }
.cf-btn--approve { background: #10b981; color: #fff; }
.cf-btn--edit { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.cf-btn--reject { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.cf-card__wait { display: block; font-size: 20rpx; color: var(--text-tertiary); margin-top: 8rpx; text-align: right; }

/* AI 历史卡片 */
.cf-ai-card { background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; margin-bottom: 16rpx; border: 1px solid var(--border-light); }
.cf-ai-card__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.cf-ai-card__name { font-size: 26rpx; font-weight: 700; color: var(--text-primary); }
.cf-ai-card__time { font-size: 22rpx; color: var(--text-tertiary); }
.cf-ai-card__confidence { display: flex; align-items: center; gap: 12rpx; margin-bottom: 12rpx; }
.cf-ai-card__conf-label { font-size: 22rpx; color: var(--text-secondary); flex-shrink: 0; }
.cf-ai-card__conf-bar { flex: 1; height: 12rpx; background: var(--bhp-gray-100, #f3f4f6); border-radius: var(--radius-full); overflow: hidden; }
.cf-ai-card__conf-fill { height: 100%; background: #10b981; border-radius: var(--radius-full); }
.cf-ai-card__conf-val { font-size: 22rpx; font-weight: 700; color: #10b981; }
.cf-ai-card__suggestions { display: flex; flex-direction: column; gap: 8rpx; }
.cf-ai-card__sug { display: flex; gap: 10rpx; }
.cf-ai-card__sug-idx { font-size: 20rpx; font-weight: 700; color: var(--bhp-primary-500, #10b981); }
.cf-ai-card__sug-text { font-size: 24rpx; color: var(--text-secondary); line-height: 1.5; }

/* 空 */
.cf-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 16rpx; }
.cf-empty__icon { font-size: 64rpx; }
.cf-empty__title { font-size: 28rpx; color: var(--text-secondary); font-weight: 600; }
.cf-empty__sub { font-size: 24rpx; color: var(--text-tertiary); }
.cf-empty-inline { text-align: center; padding: 32rpx; font-size: 24rpx; color: var(--text-tertiary); }

/* 底部 */
.cf-footer { position: fixed; bottom: 0; left: 0; right: 0; padding: 20rpx 32rpx; padding-bottom: calc(20rpx + env(safe-area-inset-bottom)); background: var(--surface); border-top: 1px solid var(--border-light); }
.cf-gen-btn { height: 88rpx; border-radius: var(--radius-lg); background: linear-gradient(135deg, #059669 0%, #10b981 100%); display: flex; align-items: center; justify-content: center; box-shadow: 0 4rpx 16rpx rgba(16,185,129,0.3); }
.cf-gen-btn--loading { opacity: 0.7; pointer-events: none; }
.cf-gen-btn__text { font-size: 30rpx; font-weight: 700; color: #fff; }

/* 弹窗 */
.cf-modal-mask { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 999; }
.cf-modal { width: 88%; background: var(--surface); border-radius: var(--radius-xl); padding: 32rpx; }
.cf-modal--result { max-height: 80vh; overflow-y: auto; }
.cf-modal__title { display: block; font-size: 30rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 24rpx; }
.cf-modal__field { margin-bottom: 20rpx; }
.cf-modal__label { display: block; font-size: 24rpx; font-weight: 600; color: var(--text-secondary); margin-bottom: 8rpx; }
.cf-modal__input { width: 100%; min-height: 160rpx; padding: 16rpx 20rpx; background: var(--surface-secondary); border-radius: var(--radius-lg); border: 1px solid var(--border-light); font-size: 26rpx; color: var(--text-primary); box-sizing: border-box; }
.cf-modal__text-input { width: 100%; height: 72rpx; padding: 0 20rpx; background: var(--surface-secondary); border-radius: var(--radius-lg); border: 1px solid var(--border-light); font-size: 26rpx; color: var(--text-primary); box-sizing: border-box; }
.cf-modal__actions { display: flex; gap: 16rpx; margin-top: 20rpx; }
.cf-modal__btn { flex: 1; height: 80rpx; border-radius: var(--radius-lg); display: flex; align-items: center; justify-content: center; font-size: 28rpx; font-weight: 600; }
.cf-modal__btn:active { opacity: 0.85; }
.cf-modal__btn--cancel { background: var(--surface-secondary); color: var(--text-secondary); }
.cf-modal__btn--ok { background: #ef4444; color: #fff; }
.cf-modal__btn--confirm { background: #10b981; color: #fff; }

.cf-picker-trigger { display: flex; justify-content: space-between; align-items: center; padding: 20rpx 24rpx; background: var(--surface-secondary); border-radius: var(--radius-lg); border: 1px solid var(--border-light); font-size: 28rpx; color: var(--text-primary); margin-bottom: 16rpx; }
.cf-picker-trigger__arrow { font-size: 22rpx; color: var(--text-tertiary); }

/* AI 结果 */
.cf-result-confidence { display: flex; align-items: center; justify-content: space-between; padding: 16rpx 20rpx; background: #f0fdf4; border-radius: var(--radius-md); margin-bottom: 20rpx; }
.cf-result-confidence__label { font-size: 24rpx; color: var(--text-secondary); }
.cf-result-confidence__val { font-size: 32rpx; font-weight: 800; color: #10b981; }
.cf-result-list { display: flex; flex-direction: column; gap: 12rpx; margin-bottom: 20rpx; }
.cf-result-item { display: flex; gap: 12rpx; padding: 16rpx 20rpx; background: var(--surface-secondary); border-radius: var(--radius-md); }
.cf-result-item__idx { width: 40rpx; height: 40rpx; border-radius: 50%; flex-shrink: 0; background: var(--bhp-primary-500, #10b981); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22rpx; font-weight: 700; }
.cf-result-item__body { flex: 1; }
.cf-result-item__text { display: block; font-size: 26rpx; color: var(--text-primary); line-height: 1.5; }
.cf-result-item__apply { margin-top: 8rpx; font-size: 22rpx; font-weight: 600; color: var(--bhp-primary-500, #10b981); }
.cf-result-raw { padding: 16rpx 20rpx; background: var(--surface-secondary); border-radius: var(--radius-md); font-size: 24rpx; color: var(--text-secondary); line-height: 1.6; white-space: pre-wrap; }
</style>
