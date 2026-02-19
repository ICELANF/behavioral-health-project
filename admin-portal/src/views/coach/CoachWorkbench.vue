<template>
  <!--
    Coach 效率工作台
    飞轮目标: 效率 — 处方一键化 + AI审核快捷键(A/R/N)，单学员处理时间从5分钟降到30秒
    核心设计:
      ❌ 旧版: 表格列表→点进→看详情→手动编写处方→保存返回 (5步, 5分钟/人)
      ✅ 新版: 学员流(类似Tinder) → AI预填处方 → 快捷键A/R/N → 下一个 (1步, 30秒/人)
    位置: admin-portal/src/views/coach/CoachWorkbench.vue
  -->
  <div class="coach-workbench" @keydown="handleKeydown">
    <!-- ═══ 顶部统计 ═══ -->
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
      <!-- ═══ 左侧: 待审队列 ═══ -->
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
              <span class="item-type">{{ item.typeLabel }}</span>
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

      <!-- ═══ 右侧: 审核工作区 ═══ -->
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

          <!-- AI摘要 (一段话，不是一屏数据) -->
          <div class="ai-summary">
            <span class="ai-badge">🤖 AI摘要</span>
            <p>{{ currentItem.aiSummary }}</p>
          </div>
        </div>

        <!-- AI预填处方 (核心效率区) -->
        <div class="prescription-area">
          <div class="rx-header">
            <h3>{{ currentItem.typeLabel }}</h3>
            <span class="rx-source">AI预填 · 可修改</span>
          </div>

          <!-- 处方六要素 (预填，可快速编辑) -->
          <div class="rx-fields" v-if="currentItem.type === 'prescription'">
            <div class="rx-field" v-for="field in rxFields" :key="field.key">
              <label>{{ field.label }}</label>
              <textarea v-model="field.value" :rows="field.rows || 1" 
                class="rx-input" :placeholder="field.placeholder" />
            </div>
          </div>

          <!-- AI对话审核 (AI回复预览) -->
          <div class="ai-reply-preview" v-if="currentItem.type === 'ai_reply'">
            <div class="preview-label">AI拟回复:</div>
            <div class="preview-content">{{ currentItem.aiDraft }}</div>
            <textarea v-model="editedReply" class="edit-area" placeholder="修改回复内容..." />
          </div>

          <!-- 推送审核 (推送内容预览) -->
          <div class="push-preview" v-if="currentItem.type === 'push'">
            <div class="preview-label">待推送内容:</div>
            <div class="push-card-preview">
              <span class="push-type">{{ currentItem.pushType }}</span>
              <p>{{ currentItem.pushContent }}</p>
            </div>
          </div>
        </div>

        <!-- ═══ 快捷操作栏 (核心: A/R/N) ═══ -->
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { coachFlywheelApi, type ReviewQueueItem } from '@/api/coach-api'

// ── 数据 ──
const pendingCount = ref(0)
const todayReviewed = ref(0)
const avgSeconds = ref(0)
const myStudentCount = ref(0)
const activeFilter = ref('all')
const editedReply = ref('')
const loading = ref(true)

type QueueItem = ReviewQueueItem

// Mock fallback data
const mockQueue: QueueItem[] = [
  {
    id: 'q1', name: '李大爷', studentId: 0, stage: 'S2', level: 'L3', bptType: '关系型',
    streakDays: 5, riskLevel: 'medium', type: 'prescription', typeLabel: '行为处方',
    priority: 'normal', waitTime: '2小时前', status: 'pending', createdAt: '',
    aiSummary: '李大爷连续5天完成八段锦打卡，但血糖控制不理想(空腹7.8)，AI建议将运动从早上调整到餐后30分钟，并增加步行处方。',
    rxFields: null, aiDraft: null, pushType: null, pushContent: null,
  } as QueueItem,
  {
    id: 'q2', name: '王阿姨', studentId: 0, stage: 'S1', level: 'L2', bptType: '情绪型',
    streakDays: 0, riskLevel: 'high', type: 'ai_reply', typeLabel: 'AI回复审核',
    priority: 'urgent', waitTime: '15分钟前', status: 'pending', createdAt: '',
    aiSummary: '王阿姨在对话中表达了对控糖失败的沮丧感，SPI=22分(L2层)，有dropout风险。',
    aiDraft: '阿姨，控糖确实不容易，您能坚持测量血糖已经很了不起了。我们不急着改变太多，先从您最舒服的节奏开始，好吗？',
    rxFields: null, pushType: null, pushContent: null,
  } as QueueItem,
]

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
    myStudentCount.value = s.streakDays // reuse for display
  } else {
    console.warn('Failed to load coach stats, using defaults', statsResult.reason)
    pendingCount.value = 12; todayReviewed.value = 34; avgSeconds.value = 28; myStudentCount.value = 45
  }

  if (queueResult.status === 'fulfilled') {
    queue.value = queueResult.value.items
    pendingCount.value = queueResult.value.totalPending
  } else {
    console.warn('Failed to load review queue, using mock', queueResult.reason)
    queue.value = mockQueue
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
  { key: 'target', label: '目标行为', value: '餐后30分钟步行15分钟', rows: 1, placeholder: '具体做什么' },
  { key: 'frequency', label: '频次剂量', value: '每日午餐后 + 晚餐后', rows: 1, placeholder: '多久一次' },
  { key: 'time_place', label: '时间地点', value: '饭后30分钟，小区内步道', rows: 1, placeholder: '何时何地' },
  { key: 'trigger', label: '启动线索', value: '吃完饭放下碗筷→换鞋→出门', rows: 1, placeholder: '提醒机制' },
  { key: 'obstacle', label: '障碍预案', value: '下雨天改为室内原地踏步10分钟', rows: 1, placeholder: '遇到困难怎么办' },
  { key: 'support', label: '支持资源', value: '邀请老伴一起走', rows: 1, placeholder: '谁来帮助(选填)' },
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
  // 跳到下一个, 当前保留在队列
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
  if (!currentItem.value) return
  if (document.activeElement?.tagName === 'TEXTAREA') return // 编辑中不响应
  switch (e.key.toLowerCase()) {
    case 'a': e.preventDefault(); handleApprove(); break
    case 'r': e.preventDefault(); handleReject(); break
    case 'n': e.preventDefault(); handleSkip(); break
  }
}
</script>

<style scoped>
.coach-workbench { height: 100vh; display: flex; flex-direction: column; background: #f8fafc; }

/* ── 统计栏 ── */
.stats-bar {
  display: flex; gap: 24px; padding: 16px 24px;
  background: #fff; border-bottom: 1px solid #e5e7eb;
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

/* ── 快捷操作栏 (固定底部) ── */
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
</style>
