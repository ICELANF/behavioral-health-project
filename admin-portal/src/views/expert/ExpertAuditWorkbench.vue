<template>
  <!--
    Expert 统一审核工作台
    飞轮目标: 质量保障 — 所有AI输出/处方/内容/Agent行为在一个界面统一审核
    核心设计:
      ❌ 旧版: Streamlit独立端口(:8501)，与平台割裂，数据不通，只能看不能批
      ✅ 新版: 嵌入Admin Portal，三栏布局(筛选→内容→裁决)，支持批量审核+标注
    位置: admin-portal/src/views/expert/ExpertAuditWorkbench.vue
  -->
  <div class="expert-audit">
    <!-- ═══ 顶部: 质量指标 ═══ -->
    <div class="metrics-bar">
      <div class="metric">
        <span class="metric-label">今日审核</span>
        <span class="metric-value">{{ todayAudited }}</span>
      </div>
      <div class="metric">
        <span class="metric-label">合格率</span>
        <span class="metric-value" :class="passRateClass">{{ passRate }}%</span>
      </div>
      <div class="metric">
        <span class="metric-label">待审队列</span>
        <span class="metric-value urgent">{{ pendingQueue }}</span>
      </div>
      <div class="metric">
        <span class="metric-label">红线拦截</span>
        <span class="metric-value red">{{ redlineBlocked }}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Agent异常</span>
        <span class="metric-value" :class="agentAnomalyCount > 0 ? 'red' : ''">{{ agentAnomalyCount }}</span>
      </div>
    </div>

    <div class="audit-body">
      <!-- ═══ 左栏: 筛选+队列 ═══ -->
      <div class="filter-panel">
        <!-- 审核类型分组 -->
        <div class="filter-section">
          <h4>审核类型</h4>
          <div class="filter-group">
            <label v-for="t in auditTypes" :key="t.key" class="filter-chip"
              :class="{ active: selectedTypes.includes(t.key) }">
              <input type="checkbox" v-model="selectedTypes" :value="t.key" hidden />
              <span class="chip-icon">{{ t.icon }}</span>
              <span class="chip-label">{{ t.label }}</span>
              <span class="chip-count">{{ t.count }}</span>
            </label>
          </div>
        </div>

        <!-- 风险等级 -->
        <div class="filter-section">
          <h4>风险等级</h4>
          <div class="filter-group horizontal">
            <button v-for="r in riskLevels" :key="r.key"
              class="risk-btn" :class="{ active: selectedRisk === r.key, [r.key]: true }"
              @click="selectedRisk = selectedRisk === r.key ? 'all' : r.key">
              {{ r.label }} ({{ r.count }})
            </button>
          </div>
        </div>

        <!-- Agent筛选 -->
        <div class="filter-section">
          <h4>涉及Agent</h4>
          <select v-model="selectedAgent" class="agent-select">
            <option value="all">全部Agent</option>
            <option v-for="a in agentList" :key="a" :value="a">{{ a }}</option>
          </select>
        </div>

        <!-- 队列列表 -->
        <div class="queue-scroll">
          <div v-for="item in filteredItems" :key="item.id"
            class="audit-item" :class="{ selected: currentAudit?.id === item.id }"
            @click="selectAudit(item)">
            <div class="item-risk-dot" :class="item.risk" />
            <div class="item-content">
              <div class="item-title">{{ item.title }}</div>
              <div class="item-sub">
                {{ item.agent }} · {{ item.userName }} · {{ item.time }}
              </div>
            </div>
            <div class="item-type-badge">{{ item.typeIcon }}</div>
          </div>
        </div>
      </div>

      <!-- ═══ 中栏: 内容详情 ═══ -->
      <div class="content-panel" v-if="currentAudit">
        <div class="content-header">
          <div class="content-title-row">
            <h2>{{ currentAudit.title }}</h2>
            <span class="content-risk-badge" :class="currentAudit.risk">
              {{ riskMap[currentAudit.risk] }}
            </span>
          </div>
          <div class="content-meta">
            <span>Agent: <strong>{{ currentAudit.agent }}</strong></span>
            <span>用户: <strong>{{ currentAudit.userName }}</strong> ({{ currentAudit.userStage }})</span>
            <span>时间: {{ currentAudit.time }}</span>
          </div>
        </div>

        <!-- 根据类型渲染不同内容 -->
        <!-- AI对话审核 -->
        <div class="content-section" v-if="currentAudit.type === 'ai_dialogue'">
          <h3>对话上下文</h3>
          <div class="dialogue-flow">
            <div v-for="msg in currentAudit.dialogue" :key="msg.id"
              class="msg-bubble" :class="msg.role">
              <div class="msg-role">{{ msg.role === 'user' ? '用户' : 'AI' }}</div>
              <div class="msg-text">{{ msg.text }}</div>
              <div class="msg-modality" v-if="msg.modality !== 'text'">
                {{ modalityIcon(msg.modality) }} {{ msg.modality }}
              </div>
            </div>
          </div>

          <!-- 安全红线检查结果 -->
          <div class="safety-check" v-if="currentAudit.safetyFlags.length > 0">
            <h3>⚠️ 安全红线触发</h3>
            <div v-for="flag in currentAudit.safetyFlags" :key="flag.rule" class="safety-flag">
              <span class="flag-rule">{{ flag.rule }}</span>
              <span class="flag-desc">{{ flag.description }}</span>
              <span class="flag-action" :class="flag.action">{{ flag.action }}</span>
            </div>
          </div>
        </div>

        <!-- 处方审核 -->
        <div class="content-section" v-if="currentAudit.type === 'prescription'">
          <h3>行为处方内容</h3>
          <div class="rx-review-grid">
            <div v-for="f in currentAudit.rxFields" :key="f.key" class="rx-review-field">
              <label>{{ f.label }}</label>
              <div class="rx-review-value" :class="{ flagged: f.flagged }">
                {{ f.value }}
                <span class="flag-icon" v-if="f.flagged" :title="f.flagReason">⚠️</span>
              </div>
            </div>
          </div>
          <div class="evidence-section" v-if="currentAudit.evidenceLevel">
            <h3>证据等级</h3>
            <div class="evidence-badge" :class="'t' + currentAudit.evidenceLevel">
              T{{ currentAudit.evidenceLevel }}
              <span>{{ evidenceLabel(currentAudit.evidenceLevel) }}</span>
            </div>
          </div>
        </div>

        <!-- Agent行为审核 -->
        <div class="content-section" v-if="currentAudit.type === 'agent_behavior'">
          <h3>Agent决策链</h3>
          <div class="decision-chain">
            <div v-for="step in currentAudit.decisionSteps" :key="step.step" class="chain-step">
              <div class="step-num">{{ step.step }}</div>
              <div class="step-content">
                <div class="step-action">{{ step.action }}</div>
                <div class="step-detail">{{ step.detail }}</div>
              </div>
              <div class="step-verdict" :class="step.ok ? 'ok' : 'issue'">
                {{ step.ok ? '✓' : '✕' }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ 右栏: 裁决面板 ═══ -->
      <div class="verdict-panel" v-if="currentAudit">
        <h3>审核裁决</h3>

        <!-- 快速评分 -->
        <div class="verdict-section">
          <label>质量评分</label>
          <div class="score-buttons">
            <button v-for="s in [1,2,3,4,5]" :key="s"
              class="score-btn" :class="{ active: verdictScore === s }"
              @click="verdictScore = s">
              {{ s }}
            </button>
          </div>
          <div class="score-labels">
            <span>不合格</span><span>优秀</span>
          </div>
        </div>

        <!-- 问题标注 (多选) -->
        <div class="verdict-section">
          <label>问题标注</label>
          <div class="issue-tags">
            <label v-for="tag in issueTags" :key="tag.key" class="issue-chip"
              :class="{ active: selectedIssues.includes(tag.key) }">
              <input type="checkbox" v-model="selectedIssues" :value="tag.key" hidden />
              {{ tag.label }}
            </label>
          </div>
        </div>

        <!-- 备注 -->
        <div class="verdict-section">
          <label>审核备注</label>
          <textarea v-model="verdictNote" class="verdict-textarea" 
            placeholder="补充说明（可选）..." rows="3" />
        </div>

        <!-- 裁决按钮 -->
        <div class="verdict-actions">
          <button class="v-btn pass" @click="submitVerdict('pass')">
            ✓ 合格通过
          </button>
          <button class="v-btn revise" @click="submitVerdict('revise')">
            ↻ 退回修改
          </button>
          <button class="v-btn block" @click="submitVerdict('block')">
            ✕ 拦截禁用
          </button>
        </div>

        <!-- 历史裁决 -->
        <div class="verdict-history" v-if="currentAudit.history.length > 0">
          <h4>历史审核</h4>
          <div v-for="h in currentAudit.history" :key="h.time" class="history-item">
            <span class="history-verdict" :class="h.verdict">{{ h.verdict }}</span>
            <span class="history-by">{{ h.by }}</span>
            <span class="history-time">{{ h.time }}</span>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div class="empty-center" v-if="!currentAudit">
        <div class="empty-icon">🔍</div>
        <h3>选择左侧项目开始审核</h3>
        <p>或使用筛选器缩小范围</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { expertFlywheelApi, type ExpertAuditItem } from '@/api/expert-api'

// ── 指标 ──
const todayAudited = ref(0)
const passRate = ref(0)
const pendingQueue = ref(0)
const redlineBlocked = ref(0)
const agentAnomalyCount = ref(0)
const loading = ref(true)
const passRateClass = computed(() => passRate.value >= 90 ? 'green' : passRate.value >= 80 ? 'yellow' : 'red')

// ── 筛选 ──
const selectedTypes = ref(['ai_dialogue', 'prescription', 'agent_behavior'])
const selectedRisk = ref('all')
const selectedAgent = ref('all')

const auditTypes = ref([
  { key: 'ai_dialogue', icon: '💬', label: 'AI对话', count: 0 },
  { key: 'prescription', icon: '📋', label: '行为处方', count: 0 },
  { key: 'agent_behavior', icon: '🤖', label: 'Agent行为', count: 0 },
  { key: 'content', icon: '📄', label: '内容推荐', count: 0 },
  { key: 'safety', icon: '🛡️', label: '安全事件', count: 0 },
])

const riskLevels = ref([
  { key: 'critical', label: '🚨 严重', count: 0 },
  { key: 'high', label: '🔴 高', count: 0 },
  { key: 'medium', label: '🟡 中', count: 0 },
  { key: 'low', label: '🟢 低', count: 0 },
])

const agentList = ref([
  'crisis_responder', 'nutrition_guide', 'exercise_guide', 'emotion_support',
  'behavior_coach', 'tcm_wellness', 'pain_relief_guide', 'rx_composer',
])

const riskMap: Record<string, string> = {
  critical: '🚨 严重', high: '🔴 高危', medium: '🟡 中等', low: '🟢 低风险',
}

// ── 裁决 ──
const verdictScore = ref(0)
const selectedIssues = ref<string[]>([])
const verdictNote = ref('')

const issueTags = [
  { key: 'medical_boundary', label: '越医疗边界' },
  { key: 'stage_mismatch', label: '阶段不匹配' },
  { key: 'tone_inappropriate', label: '语气不当' },
  { key: 'evidence_weak', label: '证据不足' },
  { key: 'privacy_risk', label: '隐私风险' },
  { key: 'rx_too_aggressive', label: '处方过激' },
  { key: 'missing_disclaimer', label: '缺免责声明' },
  { key: 'hallucination', label: 'AI幻觉' },
]

// ── 审核项 ──
type AuditItem = ExpertAuditItem

const auditItems = ref<AuditItem[]>([])
const currentAudit = ref<AuditItem | null>(null)

const filteredItems = computed(() => {
  return auditItems.value.filter(item => {
    if (!selectedTypes.value.includes(item.type)) return false
    if (selectedRisk.value !== 'all' && item.risk !== selectedRisk.value) return false
    if (selectedAgent.value !== 'all' && item.agent !== selectedAgent.value) return false
    return true
  })
})

async function loadData() {
  loading.value = true
  const [metricsResult, queueResult, anomaliesResult] = await Promise.allSettled([
    expertFlywheelApi.getQualityMetrics(),
    expertFlywheelApi.getAuditQueue(),
    expertFlywheelApi.getAgentAnomalies(),
  ])

  if (metricsResult.status === 'fulfilled') {
    const m = metricsResult.value
    todayAudited.value = m.todayAudited
    passRate.value = m.passRate
    pendingQueue.value = m.pendingQueue
    redlineBlocked.value = m.redlineBlocked
    agentAnomalyCount.value = m.agentAnomalyCount
    // Update type counts from byType
    for (const t of auditTypes.value) {
      t.count = m.byType[t.key] ?? 0
    }
  } else {
    console.warn('Failed to load expert metrics:', metricsResult.reason)
  }

  if (queueResult.status === 'fulfilled') {
    auditItems.value = queueResult.value.items
    // Update risk counts from byRisk
    for (const r of riskLevels.value) {
      r.count = queueResult.value.byRisk[r.key] ?? 0
    }
  } else {
    console.warn('Failed to load audit queue:', queueResult.reason)
  }

  if (anomaliesResult.status === 'fulfilled') {
    const anomalies = anomaliesResult.value
    // Extract unique agent names for filter
    const names = new Set(anomalies.map(a => a.agentName))
    if (names.size > 0) {
      agentList.value = [...new Set([...agentList.value, ...names])]
    }
  }

  loading.value = false
}

async function loadQueue() {
  try {
    const params: any = {}
    if (selectedTypes.value.length < auditTypes.value.length) {
      params.type_filter = selectedTypes.value.join(',')
    }
    if (selectedRisk.value !== 'all') params.risk_filter = selectedRisk.value
    if (selectedAgent.value !== 'all') params.agent_filter = selectedAgent.value
    const result = await expertFlywheelApi.getAuditQueue(params)
    auditItems.value = result.items
  } catch (e) {
    console.warn('Failed to reload audit queue', e)
  }
}

// Reload queue on filter changes
watch([selectedTypes, selectedRisk, selectedAgent], loadQueue, { deep: true })

onMounted(loadData)

function selectAudit(item: AuditItem) { currentAudit.value = item }
function modalityIcon(m: string) {
  const map: Record<string, string> = { voice: '🎤', image: '📷', video: '🎬', device: '⌚' }
  return map[m] || '📝'
}
function evidenceLabel(level: number) {
  const map: Record<number, string> = { 1: '临床指南', 2: 'RCT研究', 3: '专家共识', 4: '个人经验' }
  return map[level] || ''
}

async function submitVerdict(verdict: string) {
  if (!currentAudit.value) return
  try {
    const result = await expertFlywheelApi.submitVerdict(currentAudit.value.id, {
      verdict,
      score: verdictScore.value,
      issues: selectedIssues.value,
      note: verdictNote.value,
    })
    // Remove from local list
    const idx = auditItems.value.findIndex(a => a.id === currentAudit.value?.id)
    if (idx >= 0) auditItems.value.splice(idx, 1)
    pendingQueue.value--
    todayAudited.value++
    // Jump to next item (use next_id from API if available)
    if (result.nextId) {
      const next = auditItems.value.find(a => a.id === result.nextId)
      currentAudit.value = next || auditItems.value[0] || null
    } else {
      currentAudit.value = auditItems.value[0] || null
    }
  } catch (e) {
    console.warn('Verdict API failed, handling locally', e)
    const idx = auditItems.value.findIndex(a => a.id === currentAudit.value?.id)
    if (idx >= 0) auditItems.value.splice(idx, 1)
    pendingQueue.value--
    todayAudited.value++
    currentAudit.value = auditItems.value[0] || null
  }
  verdictScore.value = 0
  selectedIssues.value = []
  verdictNote.value = ''
}
</script>

<style scoped>
.expert-audit { height: 100vh; display: flex; flex-direction: column; background: #f8fafc; }

/* ── 指标栏 ── */
.metrics-bar {
  display: flex; gap: 32px; padding: 14px 24px;
  background: #fff; border-bottom: 1px solid #e5e7eb;
}
.metric { text-align: center; }
.metric-label { display: block; font-size: 11px; color: #6b7280; margin-bottom: 2px; }
.metric-value { font-size: 22px; font-weight: 800; color: #111827; }
.metric-value.urgent { color: #f59e0b; }
.metric-value.red { color: #dc2626; }
.metric-value.green { color: #10b981; }
.metric-value.yellow { color: #f59e0b; }

/* ── 主体三栏 ── */
.audit-body { flex: 1; display: flex; overflow: hidden; }

/* ── 左栏 ── */
.filter-panel {
  width: 280px; background: #fff; border-right: 1px solid #e5e7eb;
  display: flex; flex-direction: column; overflow-y: auto;
}
.filter-section { padding: 12px 14px; border-bottom: 1px solid #f3f4f6; }
.filter-section h4 { font-size: 12px; font-weight: 700; color: #374151; margin: 0 0 8px; text-transform: uppercase; }
.filter-group { display: flex; flex-direction: column; gap: 4px; }
.filter-group.horizontal { flex-direction: row; flex-wrap: wrap; gap: 4px; }

.filter-chip {
  display: flex; align-items: center; gap: 6px; padding: 6px 10px;
  border-radius: 8px; cursor: pointer; font-size: 12px;
  background: #f9fafb; border: 1px solid #e5e7eb; transition: all 0.15s;
}
.filter-chip.active { background: #eff6ff; border-color: #3b82f6; color: #2563eb; }
.chip-count { margin-left: auto; font-weight: 700; font-size: 11px; color: #6b7280; }

.risk-btn {
  padding: 4px 8px; border-radius: 6px; border: 1px solid #e5e7eb;
  background: #fff; font-size: 11px; cursor: pointer;
}
.risk-btn.active.critical { background: #fef2f2; border-color: #dc2626; color: #dc2626; }
.risk-btn.active.high { background: #fff7ed; border-color: #f97316; color: #f97316; }
.risk-btn.active.medium { background: #fefce8; border-color: #eab308; color: #ca8a04; }
.risk-btn.active.low { background: #f0fdf4; border-color: #22c55e; color: #16a34a; }

.agent-select {
  width: 100%; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px;
  font-size: 12px; background: #fff;
}

.queue-scroll { flex: 1; overflow-y: auto; }
.audit-item {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  cursor: pointer; border-bottom: 1px solid #f3f4f6; transition: background 0.15s;
}
.audit-item:hover { background: #f9fafb; }
.audit-item.selected { background: #eff6ff; border-left: 3px solid #3b82f6; }
.item-risk-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.item-risk-dot.critical { background: #dc2626; }
.item-risk-dot.high { background: #f97316; }
.item-risk-dot.medium { background: #eab308; }
.item-risk-dot.low { background: #22c55e; }
.item-content { flex: 1; min-width: 0; }
.item-title { font-size: 13px; font-weight: 600; color: #111827; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-sub { font-size: 10px; color: #6b7280; margin-top: 2px; }
.item-type-badge { font-size: 16px; }

/* ── 中栏 ── */
.content-panel { flex: 1; overflow-y: auto; background: #fff; border-right: 1px solid #e5e7eb; }
.content-header { padding: 16px 20px; border-bottom: 1px solid #f3f4f6; }
.content-title-row { display: flex; align-items: center; justify-content: space-between; }
.content-title-row h2 { font-size: 16px; font-weight: 700; margin: 0; }
.content-risk-badge { font-size: 12px; padding: 3px 8px; border-radius: 6px; font-weight: 600; }
.content-risk-badge.critical { background: #fef2f2; color: #dc2626; }
.content-risk-badge.high { background: #fff7ed; color: #ea580c; }
.content-risk-badge.medium { background: #fefce8; color: #ca8a04; }
.content-meta { display: flex; gap: 16px; font-size: 12px; color: #6b7280; margin-top: 8px; }

.content-section { padding: 16px 20px; }
.content-section h3 { font-size: 14px; font-weight: 700; margin: 0 0 12px; }

/* 对话流 */
.dialogue-flow { display: flex; flex-direction: column; gap: 10px; }
.msg-bubble { max-width: 85%; padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.6; }
.msg-bubble.user { background: #eff6ff; align-self: flex-start; border-bottom-left-radius: 4px; }
.msg-bubble.ai { background: #f0fdf4; align-self: flex-end; border-bottom-right-radius: 4px; }
.msg-role { font-size: 10px; font-weight: 700; color: #6b7280; margin-bottom: 4px; }
.msg-modality { font-size: 10px; color: #9ca3af; margin-top: 4px; }

/* 安全检查 */
.safety-check { background: #fef2f2; border-radius: 10px; padding: 12px; margin-top: 12px; }
.safety-flag {
  display: flex; align-items: center; gap: 8px; padding: 6px 0;
  font-size: 12px; border-bottom: 1px solid #fecaca;
}
.flag-rule { font-weight: 700; color: #dc2626; white-space: nowrap; }
.flag-desc { flex: 1; color: #7f1d1d; }
.flag-action { padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; background: #fef9c3; color: #92400e; }

/* 处方审核 */
.rx-review-grid { display: flex; flex-direction: column; gap: 8px; }
.rx-review-field label { font-size: 11px; font-weight: 600; color: #6b7280; margin-bottom: 2px; display: block; }
.rx-review-value {
  padding: 8px 12px; background: #f9fafb; border-radius: 8px; font-size: 13px;
  border: 1px solid #e5e7eb; position: relative;
}
.rx-review-value.flagged { background: #fffbeb; border-color: #fcd34d; }
.flag-icon { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); cursor: help; }

.evidence-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 700;
}
.evidence-badge.t1 { background: #dcfce7; color: #16a34a; }
.evidence-badge.t2 { background: #dbeafe; color: #2563eb; }
.evidence-badge.t3 { background: #fef3c7; color: #d97706; }
.evidence-badge.t4 { background: #f3f4f6; color: #6b7280; }

/* Agent决策链 */
.decision-chain { display: flex; flex-direction: column; gap: 6px; }
.chain-step { display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: #f9fafb; border-radius: 8px; }
.step-num { width: 24px; height: 24px; border-radius: 50%; background: #e5e7eb; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.step-content { flex: 1; }
.step-action { font-size: 13px; font-weight: 600; }
.step-detail { font-size: 11px; color: #6b7280; }
.step-verdict { font-size: 16px; font-weight: 700; }
.step-verdict.ok { color: #10b981; }
.step-verdict.issue { color: #dc2626; }

/* ── 右栏: 裁决 ── */
.verdict-panel { width: 260px; background: #fff; padding: 16px; overflow-y: auto; }
.verdict-panel h3 { font-size: 15px; font-weight: 700; margin: 0 0 16px; }
.verdict-section { margin-bottom: 16px; }
.verdict-section label { display: block; font-size: 12px; font-weight: 600; color: #374151; margin-bottom: 6px; }

.score-buttons { display: flex; gap: 6px; }
.score-btn {
  width: 36px; height: 36px; border-radius: 8px; border: 2px solid #e5e7eb;
  background: #fff; font-size: 14px; font-weight: 700; cursor: pointer; transition: all 0.15s;
}
.score-btn.active { border-color: #3b82f6; background: #eff6ff; color: #2563eb; }
.score-labels { display: flex; justify-content: space-between; font-size: 10px; color: #9ca3af; margin-top: 4px; }

.issue-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.issue-chip {
  padding: 4px 8px; border-radius: 6px; font-size: 11px; cursor: pointer;
  background: #f3f4f6; border: 1px solid #e5e7eb; transition: all 0.15s;
}
.issue-chip.active { background: #fef2f2; border-color: #fca5a5; color: #dc2626; }

.verdict-textarea {
  width: 100%; padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 8px;
  font-size: 12px; resize: vertical; font-family: inherit;
}

.verdict-actions { display: flex; flex-direction: column; gap: 6px; margin-bottom: 20px; }
.v-btn {
  padding: 10px; border: none; border-radius: 8px; font-size: 13px;
  font-weight: 700; cursor: pointer; transition: all 0.15s;
}
.v-btn:active { transform: scale(0.97); }
.v-btn.pass { background: #10b981; color: #fff; }
.v-btn.revise { background: #fef3c7; color: #92400e; }
.v-btn.block { background: #fef2f2; color: #dc2626; }

.verdict-history { border-top: 1px solid #f3f4f6; padding-top: 12px; }
.verdict-history h4 { font-size: 12px; font-weight: 700; color: #6b7280; margin: 0 0 8px; }
.history-item { display: flex; gap: 6px; font-size: 11px; padding: 4px 0; }
.history-verdict { font-weight: 700; }
.history-verdict.pass { color: #10b981; }
.history-verdict.revise { color: #f59e0b; }
.history-verdict.block { color: #dc2626; }

.empty-center { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-center h3 { font-size: 16px; font-weight: 700; color: #6b7280; margin: 0 0 4px; }
.empty-center p { font-size: 13px; color: #9ca3af; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .audit-body { flex-direction: column !important; }
  .filter-panel { width: 100% !important; max-height: 40vh; overflow-y: auto; }
  .verdict-panel { width: 100% !important; }
  .metrics-bar { flex-wrap: wrap; gap: 12px; }
  .content-meta { flex-direction: column; gap: 4px; }
}
@media (min-width: 769px) and (max-width: 1024px) {
  .filter-panel { width: 220px !important; }
  .verdict-panel { width: 220px !important; }
}
</style>
