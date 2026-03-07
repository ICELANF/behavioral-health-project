<template>
  <div>
    <div class="page-header">
      <h2>AI 飞轮</h2>
      <button class="run-btn" :disabled="running" @click="runFlywheel">
        {{ running ? '运行中...' : '▶ 运行AI飞轮' }}
      </button>
    </div>

    <!-- 步骤条 -->
    <div class="steps-bar">
      <div v-for="(step, idx) in steps" :key="step.id" class="step-item" :class="{ done: stepDone(idx), active: stepActive(idx) }">
        <div class="step-circle">
          <span v-if="stepDone(idx)">✓</span>
          <span v-else>{{ idx + 1 }}</span>
        </div>
        <div class="step-info">
          <div class="step-name">{{ step.name }}</div>
          <div class="step-desc">{{ step.desc }}</div>
        </div>
        <div v-if="idx < steps.length - 1" class="step-line"></div>
      </div>
    </div>

    <!-- AI运行结果 -->
    <div v-if="aiResult" class="card" style="margin-bottom:16px">
      <div class="card-header"><h3>AI建议</h3></div>
      <div class="suggestions">
        <div v-for="(s, i) in suggestions" :key="i" class="suggestion-item">
          <span class="s-num">{{ i + 1 }}</span>
          <span class="s-text">{{ s }}</span>
        </div>
      </div>
    </div>

    <!-- 审核队列 -->
    <div class="card">
      <div class="card-header">
        <h3>待审 AI 计划</h3>
        <button class="refresh-btn" @click="loadReviewQueue">刷新</button>
      </div>
      <div v-if="queueLoading" class="loading">加载中...</div>
      <div v-else-if="queue.length === 0" class="empty">暂无待审计划</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>学员</th>
            <th>计划概要</th>
            <th>优先级</th>
            <th>时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="q in queue" :key="q.id">
            <td>{{ q.student_name || q.coach_name || '—' }}</td>
            <td>{{ q.plan_summary || q.summary || '—' }}</td>
            <td><span class="priority-tag" :class="'p-' + q.priority">{{ q.priority || 'normal' }}</span></td>
            <td>{{ q.created_at?.slice(0, 10) || '—' }}</td>
            <td class="action-cell">
              <button class="action-btn action-approve" @click="approveQueue(q)">通过</button>
              <button class="action-btn action-reject" @click="rejectQueue(q)">驳回</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api/index'

const running = ref(false)
const currentStep = ref(-1)
const aiResult = ref<any>(null)
const queue = ref<any[]>([])
const queueLoading = ref(false)

const steps = [
  { id: 'assess',   name: '数据采集', desc: '收集学员行为数据' },
  { id: 'analyze',  name: 'AI分析',   desc: '智能分析行为模式' },
  { id: 'plan',     name: '生成计划', desc: '制定个性化方案' },
  { id: 'review',   name: '教练审核', desc: '人工确认与调整' },
  { id: 'push',     name: '推送执行', desc: '下发并追踪效果' },
]

function stepDone(idx: number) { return currentStep.value > idx }
function stepActive(idx: number) { return currentStep.value === idx }

const suggestions = computed(() => {
  if (!aiResult.value) return []
  const s = aiResult.value.suggestions
  if (Array.isArray(s)) return s.map((item: any) => item.text || item)
  if (typeof s === 'string') return [s]
  return []
})

async function runFlywheel() {
  running.value = true
  currentStep.value = 0
  aiResult.value = null
  try {
    const stepDelay = (ms: number) => new Promise(r => setTimeout(r, ms))
    for (let i = 0; i < steps.length - 1; i++) {
      currentStep.value = i
      if (i === 2) {
        const res: any = await api.post('/api/v1/agent/run', { agent_type: 'coach_flywheel' })
        aiResult.value = res
      } else {
        await stepDelay(600)
      }
    }
    currentStep.value = steps.length - 1
    await loadReviewQueue()
  } catch (e: any) {
    alert(e.response?.data?.detail || 'AI飞轮运行失败')
    currentStep.value = -1
  } finally {
    running.value = false
  }
}

async function loadReviewQueue() {
  queueLoading.value = true
  try {
    const res: any = await api.get('/api/v1/coach/review-queue?status=pending')
    queue.value = res.items || (Array.isArray(res) ? res : [])
  } catch { queue.value = [] }
  queueLoading.value = false
}

async function approveQueue(q: any) {
  try {
    await api.post(`/api/v1/coach/review-queue/${q.id}/approve`)
    queue.value = queue.value.filter(i => i.id !== q.id)
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

async function rejectQueue(q: any) {
  const reason = prompt('驳回原因（可选）') ?? ''
  try {
    await api.post(`/api/v1/coach/review-queue/${q.id}/reject`, { reason })
    queue.value = queue.value.filter(i => i.id !== q.id)
  } catch (e: any) { alert(e.response?.data?.detail || '操作失败') }
}

onMounted(loadReviewQueue)
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #111827; margin: 0; }

.run-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, #7c3aed, #3b82f6);
  color: #fff; border: none; border-radius: 8px;
  font-size: 14px; font-weight: 600; cursor: pointer;
}
.run-btn:hover { opacity: 0.9; }
.run-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.steps-bar {
  display: flex;
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  overflow-x: auto;
}

.step-item {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 120px;
  position: relative;
}

.step-circle {
  width: 36px; height: 36px;
  border-radius: 50%;
  border: 2px solid #d1d5db;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 600;
  color: #9ca3af;
  background: #fff;
  flex-shrink: 0;
  z-index: 1;
  transition: all 0.3s;
}

.step-item.done .step-circle { border-color: #10b981; background: #10b981; color: #fff; }
.step-item.active .step-circle { border-color: #3b82f6; color: #3b82f6; animation: pulse 1s infinite; }

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(59,130,246,0.4); }
  50% { box-shadow: 0 0 0 6px rgba(59,130,246,0); }
}

.step-info { padding: 0 12px; }
.step-name { font-size: 13px; font-weight: 600; color: #111827; }
.step-desc { font-size: 11px; color: #9ca3af; margin-top: 2px; }

.step-line {
  flex: 1;
  height: 2px;
  background: #e5e7eb;
  margin: 0 4px;
}
.step-item.done .step-line { background: #10b981; }

.card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); margin-bottom: 16px; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-header h3 { font-size: 15px; font-weight: 600; margin: 0; }
.refresh-btn { padding: 6px 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; font-size: 12px; cursor: pointer; }

.suggestions { display: flex; flex-direction: column; gap: 10px; }
.suggestion-item { display: flex; align-items: flex-start; gap: 10px; padding: 12px; background: #f0fdf4; border-radius: 8px; border-left: 3px solid #10b981; }
.s-num { width: 22px; height: 22px; border-radius: 50%; background: #10b981; color: #fff; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.s-text { font-size: 13px; color: #374151; line-height: 1.5; }

.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 12px; color: #6b7280; font-weight: 500; border-bottom: 2px solid #f3f4f6; }
.data-table td { padding: 12px; color: #374151; border-bottom: 1px solid #f9fafb; }
.data-table tr:last-child td { border-bottom: none; }

.priority-tag { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 500; }
.p-urgent { background: #fee2e2; color: #dc2626; }
.p-high { background: #ffedd5; color: #ea580c; }
.p-normal { background: #dbeafe; color: #1d4ed8; }

.action-cell { display: flex; gap: 6px; }
.action-btn { padding: 5px 12px; border-radius: 6px; border: none; font-size: 12px; cursor: pointer; }
.action-approve { background: #d1fae5; color: #065f46; }
.action-approve:hover { background: #a7f3d0; }
.action-reject { background: #fee2e2; color: #dc2626; }
.action-reject:hover { background: #fecaca; }

.loading, .empty { color: #9ca3af; font-size: 13px; text-align: center; padding: 32px 0; }
</style>
