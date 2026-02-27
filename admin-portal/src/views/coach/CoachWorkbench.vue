<template>
  <!--
    Coach 效率工作台
    飞轮目标: 效率 — 处方一键化 + AI审核快捷键(A/R/N)，单学员处理时间从5分钟降到30秒
    核心设计:
      旧版: 表格列表→点进→看详情→手动编写处方→保存返回 (5步, 5分钟/人)
      新版: 学员流(类似Tinder) → AI预填处方 → 快捷键A/R/N → 下一个 (1步, 30秒/人)
    位置: admin-portal/src/views/coach/CoachWorkbench.vue
  -->
  <div class="coach-workbench" @keydown="handleKeydown">
    <!-- ═══ 顶部Tab栏 ═══ -->
    <div class="top-tab-bar">
      <div class="top-tabs">
        <button class="top-tab" :class="{ active: activeTopTab === 'review' }" @click="activeTopTab = 'review'">审核工作台</button>
        <button class="top-tab" :class="{ active: activeTopTab === 'history' }" @click="switchTab('history')">历史记录</button>
        <button class="top-tab" :class="{ active: activeTopTab === 'analytics' }" @click="switchTab('analytics')">效率分析</button>
        <button class="top-tab" :class="{ active: activeTopTab === 'profile' }" @click="activeTopTab = 'profile'">个人档案</button>
        <button class="top-tab" :class="{ active: activeTopTab === 'contributions' }" @click="activeTopTab = 'contributions'">我的分享</button>
        <button class="top-tab" :class="{ active: activeTopTab === 'benefits' }" @click="activeTopTab = 'benefits'">我的权益</button>
      </div>
      <UserAvatarPopover :size="36" />
    </div>

    <!-- ═══ Tab: 审核工作台 ═══ -->
    <div v-show="activeTopTab === 'review'" class="review-content">
      <!-- 统计栏 -->
      <div class="stats-bar">
        <div class="stat">
          <span class="stat-num urgent">{{ pendingCount }}</span>
          <span class="stat-label">待处理</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ todayReviewed }}</span>
          <span class="stat-label">今日已审</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ avgSeconds }}s</span>
          <span class="stat-label">平均耗时</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ myStudentCount }}</span>
          <span class="stat-label">我的学员</span>
        </div>
      </div>

      <div class="workbench-body">
        <!-- 左侧: 待审队列 -->
        <div class="queue-panel">
          <div class="queue-header">
            <h3>审核队列</h3>
            <div class="queue-filters">
              <button v-for="f in filters" :key="f.key"
                class="filter-btn" :class="{ active: activeFilter === f.key }"
                @click="activeFilter = f.key">
                {{ f.label }}
                <span class="filter-count" v-if="f.count > 0">{{ f.count }}</span>
              </button>
            </div>
          </div>
          <div class="queue-list">
            <div v-for="item in filteredQueue" :key="item.id"
              class="queue-item" :class="{ selected: currentItem?.id === item.id, urgent: item.priority === 'urgent' }"
              @click="selectItem(item)">
              <div class="item-avatar">{{ item.name[0] }}</div>
              <div class="item-info">
                <span class="item-name">{{ item.name }}</span>
                <span class="item-type">
                  <span class="source-badge-sm" :style="{ background: getSourceStyle(item.source_type || item.type).bg, color: getSourceStyle(item.source_type || item.type).color }">
                    {{ getSourceStyle(item.source_type || item.type).icon }} {{ sourceLabel(item.source_type || item.type) }}
                  </span>
                </span>
              </div>
              <div class="item-badges">
                <span class="badge-stage" :style="{ background: stageColor(item.stage) }">
                  {{ item.stage }}
                </span>
                <span class="badge-time">{{ item.waitTime }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧: 审核工作区 -->
        <div class="review-panel" v-if="currentItem">
          <!-- 学员卡片 -->
          <div class="student-card">
            <div class="student-header">
              <div class="student-avatar-lg">{{ currentItem.name[0] }}</div>
              <div class="student-meta">
                <h2 class="student-name">{{ currentItem.name }}</h2>
                <div class="student-tags">
                  <span class="tag stage">{{ currentItem.stage }}</span>
                  <span class="tag level">{{ currentItem.level }}</span>
                  <span class="tag bpt">{{ currentItem.bptType }}</span>
                  <span class="tag streak" v-if="currentItem.streakDays > 0">
                    🔥{{ currentItem.streakDays }}天
                  </span>
                </div>
              </div>
              <div class="risk-indicator" :class="currentItem.riskLevel">
                {{ riskLabel(currentItem.riskLevel) }}
              </div>
            </div>

            <!-- AI摘要 -->
            <div class="ai-summary">
              <span class="ai-badge">🤖 AI摘要</span>
              <p>{{ currentItem.aiSummary }}</p>
            </div>
          </div>

          <!-- AI预填处方 -->
          <div class="prescription-area">
            <div class="rx-header">
              <h3>{{ currentItem.typeLabel }}</h3>
              <span class="source-badge" :style="{ background: getSourceStyle(currentItem.source_type || currentItem.type).bg, color: getSourceStyle(currentItem.source_type || currentItem.type).color }">
                {{ getSourceStyle(currentItem.source_type || currentItem.type).icon }} {{ sourceLabel(currentItem.source_type || currentItem.type) }}
              </span>
              <span class="rx-source">AI预填 · 可修改</span>
            </div>

            <div class="rx-fields" v-if="currentItem.type === 'prescription'">
              <div class="rx-field" v-for="field in rxFields" :key="field.key">
                <label>{{ field.label }}</label>
                <textarea v-model="field.value" :rows="field.rows || 1"
                  class="rx-input" :placeholder="field.placeholder" />
              </div>
            </div>

            <div class="ai-reply-preview" v-if="currentItem.type === 'ai_reply'">
              <div class="preview-label">AI拟回复:</div>
              <div class="preview-content">{{ currentItem.aiDraft }}</div>
              <textarea v-model="editedReply" class="edit-area" placeholder="修改回复内容..." />
            </div>

            <div class="push-preview" v-if="currentItem.type === 'push'">
              <div class="preview-label">待推送内容:</div>
              <div class="push-card-preview">
                <span class="push-type">{{ currentItem.pushType }}</span>
                <p>{{ currentItem.pushContent }}</p>
              </div>
            </div>
          </div>

          <!-- 快捷操作栏 -->
          <div class="action-bar">
            <div class="shortcut-hint">
              快捷键: <kbd>A</kbd> 通过 · <kbd>R</kbd> 驳回 · <kbd>N</kbd> 跳过 · <kbd>E</kbd> 编辑
            </div>
            <div class="action-buttons">
              <button class="action-btn reject" @click="handleReject" title="驳回 (R)">
                <span class="btn-icon">✕</span>
                <span class="btn-label">驳回</span>
                <kbd>R</kbd>
              </button>
              <button class="action-btn skip" @click="handleSkip" title="跳过 (N)">
                <span class="btn-icon">→</span>
                <span class="btn-label">跳过</span>
                <kbd>N</kbd>
              </button>
              <button class="action-btn approve" @click="handleApprove" title="通过 (A)">
                <span class="btn-icon">✓</span>
                <span class="btn-label">通过并发送</span>
                <kbd>A</kbd>
              </button>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div class="empty-state" v-else>
          <div class="empty-icon">🎉</div>
          <h3>全部处理完成</h3>
          <p>暂无待审核内容，休息一下吧</p>
        </div>
      </div>
    </div>

    <!-- ═══ Tab: 审批历史 ═══ -->
    <div v-show="activeTopTab === 'history'" class="history-content">
      <!-- 筛选栏 -->
      <div class="history-filters">
        <select v-model="historyStatus" @change="loadHistory" class="filter-select">
          <option value="">全部状态</option>
          <option value="sent">已通过</option>
          <option value="rejected">已驳回</option>
          <option value="expired">已过期</option>
        </select>
        <input type="date" v-model="historyDateFrom" @change="loadHistory" class="filter-input" placeholder="开始日期" />
        <input type="date" v-model="historyDateTo" @change="loadHistory" class="filter-input" placeholder="结束日期" />
      </div>

      <div class="history-table-wrap">
        <table class="history-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>学员</th>
              <th>类型</th>
              <th>状态</th>
              <th>驳回原因</th>
              <th>耗时</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in historyItems" :key="item.id">
              <td>{{ formatDateTime(item.reviewed_at || item.created_at) }}</td>
              <td>{{ item.student_name }}</td>
              <td>
                <span class="source-badge" :style="{ background: getSourceStyle(item.source_type).bg, color: getSourceStyle(item.source_type).color }">
                  {{ getSourceStyle(item.source_type).icon }} {{ sourceLabel(item.source_type) }}
                </span>
              </td>
              <td>
                <span class="status-tag" :class="item.status">{{ statusLabel(item.status) }}</span>
              </td>
              <td class="note-cell">{{ item.coach_note || '-' }}</td>
              <td>{{ item.review_seconds != null ? item.review_seconds + 's' : '-' }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="!historyItems.length" class="no-data">暂无历史记录</div>
      </div>

      <div class="pagination" v-if="historyTotal > historyPageSize">
        <button :disabled="historyPage <= 1" @click="historyPage--; loadHistory()">上一页</button>
        <span>{{ historyPage }} / {{ Math.ceil(historyTotal / historyPageSize) }}</span>
        <button :disabled="historyPage * historyPageSize >= historyTotal" @click="historyPage++; loadHistory()">下一页</button>
      </div>
    </div>

    <!-- ═══ Tab: 效率分析 ═══ -->
    <div v-show="activeTopTab === 'analytics'" class="analytics-content">
      <div class="analytics-period">
        <button v-for="p in [7, 14, 30]" :key="p"
          class="period-btn" :class="{ active: analyticsPeriod === p }"
          @click="analyticsPeriod = p; loadAnalytics()">
          {{ p }}天
        </button>
      </div>

      <div class="analytics-cards" v-if="analytics">
        <div class="a-card">
          <div class="a-num">{{ analytics.total_reviewed }}</div>
          <div class="a-label">总审批数</div>
        </div>
        <div class="a-card">
          <div class="a-num" style="color:#10b981">{{ (analytics.approval_rate * 100).toFixed(1) }}%</div>
          <div class="a-label">审批通过率</div>
        </div>
        <div class="a-card">
          <div class="a-num" style="color:#3b82f6">{{ analytics.avg_review_seconds }}s</div>
          <div class="a-label">平均审批耗时</div>
        </div>
        <div class="a-card">
          <div class="a-num" style="color:#dc2626">{{ analytics.rejected }}</div>
          <div class="a-label">驳回数</div>
        </div>
      </div>

      <!-- 按类型分布 -->
      <div class="analytics-section" v-if="analytics">
        <h4>按来源类型分布</h4>
        <div class="type-bars">
          <div class="type-bar" v-for="(count, type) in analytics.by_type" :key="type as string">
            <span class="type-label">
              <span class="source-badge-sm" :style="{ background: getSourceStyle(type as string).bg, color: getSourceStyle(type as string).color }">
                {{ getSourceStyle(type as string).icon }} {{ sourceLabel(type as string) }}
              </span>
            </span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: typeBarWidth(count), background: sourceBarColor(type as string) }"></div>
            </div>
            <span class="type-count">{{ count }}</span>
          </div>
        </div>
      </div>

      <!-- 每日趋势 -->
      <div class="analytics-section" v-if="analytics && analytics.by_day.length">
        <h4>每日审批趋势</h4>
        <div class="day-chart">
          <div class="day-bar-group" v-for="d in analytics.by_day" :key="d.date">
            <div class="day-bar" :style="{ height: dayBarHeight(d.count) }">
              <span class="day-bar-val">{{ d.count }}</span>
            </div>
            <span class="day-label">{{ d.date.slice(5) }}</span>
          </div>
        </div>
      </div>

      <!-- 通过/驳回/过期 分布 -->
      <div class="analytics-section" v-if="analytics">
        <h4>审批结果分布</h4>
        <div class="pie-legend">
          <span class="legend-item">
            <span class="dot" style="background:#10b981"></span>
            通过 {{ analytics.approved }}
          </span>
          <span class="legend-item">
            <span class="dot" style="background:#dc2626"></span>
            驳回 {{ analytics.rejected }}
          </span>
          <span class="legend-item">
            <span class="dot" style="background:#9ca3af"></span>
            过期 {{ analytics.expired }}
          </span>
        </div>
      </div>
    </div>

    <!-- ═══ Tab: 个人档案 ═══ -->
    <div v-show="activeTopTab === 'profile'" class="personal-tab-wrap">
      <PersonalHealthProfile :embedded="true" />
    </div>

    <!-- ═══ Tab: 我的分享 ═══ -->
    <div v-show="activeTopTab === 'contributions'" class="personal-tab-wrap">
      <MyContributions />
    </div>

    <!-- ═══ Tab: 我的权益 ═══ -->
    <div v-show="activeTopTab === 'benefits'" class="personal-tab-wrap">
      <MyBenefits />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { coachFlywheelApi, pushQueueApi, type ReviewQueueItem, type HistoryItem, type ReviewAnalytics } from '@/api/coach-api'
import { UserAvatarPopover, PersonalHealthProfile, MyContributions, MyBenefits } from '@/components/health'

// ── Top-level tab ──
const activeTopTab = ref('review')

// ── 数据 ──
const pendingCount = ref(0)
const todayReviewed = ref(0)
const avgSeconds = ref(0)
const myStudentCount = ref(0)
const activeFilter = ref('all')
const editedReply = ref('')
const loading = ref(true)

type QueueItem = ReviewQueueItem

const queue = ref<QueueItem[]>([])
const currentItem = ref<QueueItem | null>(null)

async function loadData() {
  loading.value = true
  const [statsResult, queueResult] = await Promise.allSettled([
    coachFlywheelApi.getStatsToday(),
    coachFlywheelApi.getReviewQueue({ status: 'pending', limit: 50 }),
  ])

  if (statsResult.status === 'fulfilled') {
    const s = statsResult.value
    todayReviewed.value = s.todayReviewed
    pendingCount.value = s.pendingCount
    avgSeconds.value = s.avgSeconds
    myStudentCount.value = s.streakDays
  } else {
    console.warn('Failed to load coach stats:', statsResult.reason)
  }

  if (queueResult.status === 'fulfilled') {
    queue.value = queueResult.value.items
    pendingCount.value = queueResult.value.totalPending
  } else {
    console.warn('Failed to load review queue:', queueResult.reason)
  }

  currentItem.value = queue.value[0] || null
  loading.value = false
}

onMounted(loadData)

const filters = computed(() => [
  { key: 'all', label: '全部', count: queue.value.length },
  { key: 'prescription', label: '处方', count: queue.value.filter(q => q.type === 'prescription').length },
  { key: 'ai_reply', label: 'AI回复', count: queue.value.filter(q => q.type === 'ai_reply').length },
  { key: 'push', label: '推送', count: queue.value.filter(q => q.type === 'push').length },
])

const filteredQueue = computed(() => {
  if (activeFilter.value === 'all') return queue.value
  return queue.value.filter(q => q.type === activeFilter.value)
})

// ── 处方六要素 ──
const rxFields = ref([
  { key: 'target', label: '目标行为', value: '', rows: 1, placeholder: '具体做什么' },
  { key: 'frequency', label: '频次剂量', value: '', rows: 1, placeholder: '多久一次' },
  { key: 'time_place', label: '时间地点', value: '', rows: 1, placeholder: '何时何地' },
  { key: 'trigger', label: '启动线索', value: '', rows: 1, placeholder: '提醒机制' },
  { key: 'obstacle', label: '障碍预案', value: '', rows: 1, placeholder: '遇到困难怎么办' },
  { key: 'support', label: '支持资源', value: '', rows: 1, placeholder: '谁来帮助(选填)' },
])

// ── 方法 ──
function selectItem(item: QueueItem) {
  currentItem.value = item
}

function stageColor(stage: string): string {
  const map: Record<string, string> = {
    S0: '#ef4444', S1: '#f97316', S2: '#eab308',
    S3: '#84cc16', S4: '#22c55e', S5: '#10b981', S6: '#059669',
  }
  return map[stage] || '#6b7280'
}

function riskLabel(level: string): string {
  const map: Record<string, string> = {
    low: '🟢 低', medium: '🟡 中', high: '🔴 高', crisis: '🚨 危机',
  }
  return map[level] || ''
}

async function handleApprove() {
  if (!currentItem.value) return
  try {
    await coachFlywheelApi.approveReview(currentItem.value.id)
  } catch (e) {
    console.warn('Approve API failed, continuing locally', e)
  }
  removeCurrentAndNext()
}

async function handleReject() {
  if (!currentItem.value) return
  try {
    await coachFlywheelApi.rejectReview(currentItem.value.id, { reason: '教练驳回' })
  } catch (e) {
    console.warn('Reject API failed, continuing locally', e)
  }
  removeCurrentAndNext()
}

function handleSkip() {
  const idx = queue.value.findIndex(q => q.id === currentItem.value?.id)
  if (idx >= 0 && idx < queue.value.length - 1) {
    currentItem.value = queue.value[idx + 1] ?? null
  }
}

function removeCurrentAndNext() {
  const idx = queue.value.findIndex(q => q.id === currentItem.value?.id)
  if (idx >= 0) queue.value.splice(idx, 1)
  pendingCount.value--
  todayReviewed.value++
  currentItem.value = queue.value[idx] ?? queue.value[0] ?? null
}

function handleKeydown(e: KeyboardEvent) {
  // Only respond to shortcuts when on review tab
  if (activeTopTab.value !== 'review') return
  if (!currentItem.value) return
  if (document.activeElement?.tagName === 'TEXTAREA') return
  switch (e.key.toLowerCase()) {
    case 'a': e.preventDefault(); handleApprove(); break
    case 'r': e.preventDefault(); handleReject(); break
    case 'n': e.preventDefault(); handleSkip(); break
  }
}

// ── 历史记录 ──
const historyItems = ref<HistoryItem[]>([])
const historyTotal = ref(0)
const historyPage = ref(1)
const historyPageSize = 20
const historyStatus = ref('')
const historyDateFrom = ref('')
const historyDateTo = ref('')
let historyLoaded = false

async function loadHistory() {
  try {
    const res = await pushQueueApi.getHistory({
      status: historyStatus.value || undefined,
      page: historyPage.value,
      page_size: historyPageSize,
      date_from: historyDateFrom.value || undefined,
      date_to: historyDateTo.value || undefined,
    })
    historyItems.value = res.items
    historyTotal.value = res.total
    historyLoaded = true
  } catch (e) {
    console.warn('Failed to load history:', e)
  }
}

// ── 效率分析 ──
const analytics = ref<ReviewAnalytics | null>(null)
const analyticsPeriod = ref(7)
let analyticsLoaded = false

async function loadAnalytics() {
  try {
    analytics.value = await pushQueueApi.getAnalytics(analyticsPeriod.value)
    analyticsLoaded = true
  } catch (e) {
    console.warn('Failed to load analytics:', e)
  }
}

function switchTab(tab: string) {
  activeTopTab.value = tab
  if (tab === 'history' && !historyLoaded) loadHistory()
  if (tab === 'analytics' && !analyticsLoaded) loadAnalytics()
}

// ── 辅助函数 ──
const sourceLabels: Record<string, string> = {
  challenge: '挑战打卡', device_alert: '设备预警', micro_action: '微行动',
  ai_recommendation: 'AI建议', system: '系统', coach_message: '教练消息',
  coach_reminder: '教练提醒', assessment_push: '评估结果',
  micro_action_assign: '微行动指派', vision_rx: '视力处方', xzb_expert: '行智诊疗',
  prescription: '行为处方', ai_reply: 'AI回复', push: '推送',
}
function sourceLabel(type: string): string {
  return sourceLabels[type] || type
}

// 来源类型样式映射 (背景色 / 文字色 / 图标 / 柱状图色)
const sourceStyles: Record<string, { bg: string; color: string; icon: string; bar: string }> = {
  xzb_expert:        { bg: '#e8f5e9', color: '#2e7d32', icon: '💊', bar: '#2e7d32' },
  vision_rx:         { bg: '#e3f2fd', color: '#1565c0', icon: '👁', bar: '#1565c0' },
  prescription:      { bg: '#ede7f6', color: '#6a1b9a', icon: '📋', bar: '#7c4dff' },
  device_alert:      { bg: '#fff3e0', color: '#e65100', icon: '⚡', bar: '#ff9800' },
  challenge:         { bg: '#fff8e1', color: '#f57f17', icon: '🏆', bar: '#ffc107' },
  ai_recommendation: { bg: '#e8eaf6', color: '#283593', icon: '🤖', bar: '#5c6bc0' },
  assessment_push:   { bg: '#fce4ec', color: '#c62828', icon: '📊', bar: '#ef5350' },
  micro_action:      { bg: '#f3e5f5', color: '#7b1fa2', icon: '⚡', bar: '#ab47bc' },
  micro_action_assign: { bg: '#f3e5f5', color: '#7b1fa2', icon: '📌', bar: '#ab47bc' },
  coach_message:     { bg: '#e0f2f1', color: '#00695c', icon: '💬', bar: '#26a69a' },
  coach_reminder:    { bg: '#e0f2f1', color: '#00695c', icon: '🔔', bar: '#26a69a' },
  ai_reply:          { bg: '#e8eaf6', color: '#283593', icon: '🤖', bar: '#5c6bc0' },
  push:              { bg: '#eceff1', color: '#455a64', icon: '📤', bar: '#78909c' },
  system:            { bg: '#eceff1', color: '#455a64', icon: '⚙', bar: '#90a4ae' },
}
const defaultSourceStyle = { bg: '#f5f5f5', color: '#616161', icon: '📎', bar: '#9e9e9e' }
function getSourceStyle(type: string) {
  return sourceStyles[type] || defaultSourceStyle
}
function sourceBarColor(type: string): string {
  return (sourceStyles[type] || defaultSourceStyle).bar
}

const statusLabels: Record<string, string> = {
  approved: '已通过', sent: '已发送', rejected: '已驳回', expired: '已过期', pending: '待处理',
}
function statusLabel(s: string): string {
  return statusLabels[s] || s
}

function formatDateTime(str: string | null): string {
  if (!str) return '-'
  return str.replace('T', ' ').slice(0, 16)
}

function typeBarWidth(count: number): string {
  if (!analytics.value) return '0%'
  const max = Math.max(...Object.values(analytics.value.by_type), 1)
  return `${Math.round((count / max) * 100)}%`
}

function dayBarHeight(count: number): string {
  if (!analytics.value || !analytics.value.by_day.length) return '0px'
  const max = Math.max(...analytics.value.by_day.map(d => d.count), 1)
  return `${Math.max(4, Math.round((count / max) * 120))}px`
}
</script>

<style scoped>
.coach-workbench { height: 100vh; display: flex; flex-direction: column; background: #f8fafc; }

/* ── 顶部Tab栏 ── */
.top-tab-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 52px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}
.top-tabs {
  display: flex;
  gap: 4px;
}
.top-tab {
  padding: 8px 18px;
  font-size: 14px;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}
.top-tab:hover {
  color: #374151;
  background: #f3f4f6;
}
.top-tab.active {
  background: #3b82f6;
  color: #fff;
}

/* ── Review Content ── */
.review-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── 统计栏 ── */
.stats-bar {
  display: flex; gap: 24px; padding: 16px 24px;
  background: #fff; border-bottom: 1px solid #e5e7eb;
  align-items: center;
}
.stat { text-align: center; }
.stat-num { display: block; font-size: 24px; font-weight: 800; color: #111827; }
.stat-num.urgent { color: #dc2626; }
.stat-label { font-size: 12px; color: #6b7280; }

/* ── 主体 ── */
.workbench-body { flex: 1; display: flex; overflow: hidden; }

/* ── 左侧队列 ── */
.queue-panel { width: 320px; background: #fff; border-right: 1px solid #e5e7eb; display: flex; flex-direction: column; }
.queue-header { padding: 16px; border-bottom: 1px solid #f3f4f6; }
.queue-header h3 { font-size: 15px; font-weight: 700; margin: 0 0 10px; }
.queue-filters { display: flex; gap: 6px; }
.filter-btn {
  padding: 4px 10px; border-radius: 6px; border: 1px solid #e5e7eb;
  background: #fff; font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 4px;
}
.filter-btn.active { background: #eff6ff; border-color: #3b82f6; color: #2563eb; }
.filter-count {
  background: #dc2626; color: #fff; font-size: 10px; padding: 0 5px;
  border-radius: 8px; font-weight: 700;
}

.queue-list { flex: 1; overflow-y: auto; }
.queue-item {
  display: flex; align-items: center; gap: 10px; padding: 12px 16px;
  cursor: pointer; border-bottom: 1px solid #f3f4f6; transition: background 0.15s;
}
.queue-item:hover { background: #f9fafb; }
.queue-item.selected { background: #eff6ff; border-left: 3px solid #3b82f6; }
.queue-item.urgent { border-left: 3px solid #dc2626; }
.item-avatar {
  width: 36px; height: 36px; border-radius: 50%; background: #e0e7ff;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700; color: #4338ca; flex-shrink: 0;
}
.item-info { flex: 1; min-width: 0; }
.item-name { display: block; font-size: 14px; font-weight: 600; color: #111827; }
.item-type { font-size: 11px; color: #6b7280; }
.item-badges { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.badge-stage { font-size: 10px; color: #fff; padding: 1px 6px; border-radius: 4px; font-weight: 700; }
.badge-time { font-size: 10px; color: #9ca3af; }

/* ── 右侧审核区 ── */
.review-panel { flex: 1; display: flex; flex-direction: column; overflow-y: auto; }

.student-card { padding: 20px 24px; background: #fff; border-bottom: 1px solid #f3f4f6; }
.student-header { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; }
.student-avatar-lg {
  width: 48px; height: 48px; border-radius: 50%; background: #e0e7ff;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 700; color: #4338ca; flex-shrink: 0;
}
.student-meta { flex: 1; }
.student-name { font-size: 18px; font-weight: 800; margin: 0 0 4px; }
.student-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.tag {
  font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600;
}
.tag.stage { background: #dcfce7; color: #16a34a; }
.tag.level { background: #dbeafe; color: #2563eb; }
.tag.bpt { background: #fef3c7; color: #d97706; }
.tag.streak { background: #fef2f2; color: #dc2626; }

.risk-indicator { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.risk-indicator.low { background: #dcfce7; color: #16a34a; }
.risk-indicator.medium { background: #fef9c3; color: #ca8a04; }
.risk-indicator.high { background: #fef2f2; color: #dc2626; }
.risk-indicator.crisis { background: #dc2626; color: #fff; }

.ai-summary {
  background: #f0fdf4; border-radius: 10px; padding: 12px 14px;
}
.ai-badge {
  font-size: 11px; font-weight: 700; color: #059669;
  background: #d1fae5; padding: 2px 6px; border-radius: 4px; margin-bottom: 6px; display: inline-block;
}
.ai-summary p { font-size: 13px; color: #374151; margin: 8px 0 0; line-height: 1.6; }

/* ── 处方区 ── */
.prescription-area { padding: 20px 24px; flex: 1; }
.rx-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.rx-header h3 { font-size: 16px; font-weight: 700; margin: 0; }
.rx-source { font-size: 11px; color: #3b82f6; background: #eff6ff; padding: 2px 8px; border-radius: 4px; }
.source-badge { display: inline-flex; align-items: center; gap: 3px; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; white-space: nowrap; }
.source-badge-sm { display: inline-flex; align-items: center; gap: 2px; font-size: 10px; font-weight: 600; padding: 1px 6px; border-radius: 3px; white-space: nowrap; }

.rx-fields { display: flex; flex-direction: column; gap: 10px; }
.rx-field label { display: block; font-size: 12px; font-weight: 600; color: #374151; margin-bottom: 4px; }
.rx-input {
  width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 8px;
  font-size: 13px; resize: none; font-family: inherit;
  transition: border-color 0.2s;
}
.rx-input:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }

.ai-reply-preview, .push-preview { margin-bottom: 16px; }
.preview-label { font-size: 12px; font-weight: 600; color: #6b7280; margin-bottom: 8px; }
.preview-content {
  background: #f9fafb; border-radius: 10px; padding: 14px;
  font-size: 14px; color: #374151; line-height: 1.6; border: 1px solid #e5e7eb;
}
.edit-area {
  width: 100%; margin-top: 8px; padding: 10px; border: 1px solid #d1d5db;
  border-radius: 8px; font-size: 13px; resize: vertical; min-height: 60px; font-family: inherit;
}

/* ── 快捷操作栏 ── */
.action-bar {
  padding: 12px 24px 16px; background: #fff;
  border-top: 1px solid #e5e7eb; box-shadow: 0 -2px 8px rgba(0,0,0,0.04);
}
.shortcut-hint { font-size: 11px; color: #9ca3af; text-align: center; margin-bottom: 10px; }
.shortcut-hint kbd {
  background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 3px;
  padding: 1px 5px; font-size: 11px; font-family: monospace;
}
.action-buttons { display: flex; gap: 10px; }
.action-btn {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 12px; border: none; border-radius: 10px; font-size: 14px; font-weight: 700;
  cursor: pointer; transition: all 0.15s;
}
.action-btn:active { transform: scale(0.97); }
.action-btn kbd {
  background: rgba(255,255,255,0.2); border-radius: 3px; padding: 1px 5px;
  font-size: 10px; font-family: monospace;
}
.action-btn.approve { background: #10b981; color: #fff; flex: 2; }
.action-btn.reject { background: #fef2f2; color: #dc2626; }
.action-btn.skip { background: #f3f4f6; color: #6b7280; }
.btn-icon { font-size: 18px; }

/* ── 空状态 ── */
.empty-state { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.empty-icon { font-size: 64px; margin-bottom: 16px; }
.empty-state h3 { font-size: 18px; font-weight: 700; color: #111827; margin: 0 0 8px; }
.empty-state p { font-size: 14px; color: #6b7280; }

/* ── 历史记录 ── */
.history-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; padding: 16px 24px; }
.history-filters { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.filter-select, .filter-input {
  padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px;
  background: #fff; color: #374151;
}
.history-table-wrap { flex: 1; overflow: auto; }
.history-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.history-table th { background: #f9fafb; padding: 10px 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #e5e7eb; white-space: nowrap; }
.history-table td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; color: #4b5563; }
.history-table tr:hover { background: #f9fafb; }
.note-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #dc2626; }
.status-tag { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.status-tag.sent, .status-tag.approved { background: #dcfce7; color: #16a34a; }
.status-tag.rejected { background: #fef2f2; color: #dc2626; }
.status-tag.expired { background: #f3f4f6; color: #6b7280; }
.no-data { text-align: center; padding: 40px; color: #9ca3af; font-size: 14px; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; padding: 12px 0; }
.pagination button { padding: 6px 16px; border: 1px solid #d1d5db; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; }
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.pagination span { font-size: 13px; color: #6b7280; }

/* ── 效率分析 ── */
.analytics-content { flex: 1; overflow-y: auto; padding: 16px 24px; }
.analytics-period { display: flex; gap: 8px; margin-bottom: 20px; }
.period-btn { padding: 6px 18px; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; cursor: pointer; font-size: 13px; font-weight: 600; }
.period-btn.active { background: #3b82f6; color: #fff; border-color: #3b82f6; }
.analytics-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
.a-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; text-align: center; }
.a-num { font-size: 28px; font-weight: 800; color: #111827; }
.a-label { font-size: 12px; color: #6b7280; margin-top: 4px; }
.analytics-section { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; margin-bottom: 16px; }
.analytics-section h4 { font-size: 14px; font-weight: 700; margin: 0 0 12px; color: #374151; }
.type-bars { display: flex; flex-direction: column; gap: 8px; }
.type-bar { display: flex; align-items: center; gap: 10px; }
.type-label { width: 110px; font-size: 12px; color: #6b7280; text-align: right; flex-shrink: 0; }
.bar-track { flex: 1; height: 20px; background: #f3f4f6; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; background: #3b82f6; border-radius: 4px; transition: width 0.3s; min-width: 2px; }
.type-count { width: 32px; font-size: 12px; font-weight: 700; color: #374151; }
.day-chart { display: flex; align-items: flex-end; gap: 4px; height: 140px; padding-top: 10px; }
.day-bar-group { flex: 1; display: flex; flex-direction: column; align-items: center; }
.day-bar { width: 100%; max-width: 36px; background: #3b82f6; border-radius: 4px 4px 0 0; display: flex; align-items: flex-start; justify-content: center; min-height: 4px; }
.day-bar-val { font-size: 10px; color: #fff; font-weight: 700; margin-top: 2px; }
.day-label { font-size: 10px; color: #9ca3af; margin-top: 4px; }
.pie-legend { display: flex; gap: 20px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #374151; }
.dot { width: 10px; height: 10px; border-radius: 50%; }

/* ── Personal tab wrapper ── */
.personal-tab-wrap {
  flex: 1;
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
  overflow-y: auto;
  height: calc(100vh - 52px);
  width: 100%;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .workbench-body { flex-direction: column !important; }
  .queue-panel { width: 100% !important; max-height: 200px; overflow-y: auto; }
  .stats-bar { flex-wrap: wrap; }
  .top-tabs { overflow-x: auto; }
}
@media (min-width: 769px) and (max-width: 1024px) {
  .queue-panel { width: 240px !important; }
}
@media (max-width: 640px) {
  .queue-panel { max-height: 50vh !important; }
  .action-buttons { flex-wrap: wrap; }
  .action-btn { min-height: 48px; font-size: 15px; }
  .action-btn.approve { flex: 1 1 100%; }
  .stats-bar { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
  .top-tabs { scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch; }
  .top-tabs :deep(.ant-tabs-tab) { scroll-snap-align: start; min-height: 44px; }
  .personal-tab-wrap { padding: 12px; height: calc(100vh - 52px - env(safe-area-inset-bottom, 0px)); }
  .edit-area { font-size: 16px; }
  .shortcut-hint { display: none; }
}
</style>
