<template>
  <PageShell title="我的任务" :show-tab-bar="true">
    <template #header-right>
      <van-dropdown-menu>
        <van-dropdown-item v-model="filterType" :options="filterOptions" />
      </van-dropdown-menu>
    </template>

    <!-- Streak 徽章 -->
    <div v-if="stats.streak_days > 0" class="streak-badge">
      <span class="streak-fire">&#x1F525;</span>
      <span class="streak-text">连续 {{ stats.streak_days }} 天</span>
    </div>

    <!-- 进度统计 -->
    <div class="progress-card card">
      <div class="progress-info">
        <div class="progress-number">
          <span class="completed">{{ completedCount }}</span>
          <span class="divider">/</span>
          <span class="total">{{ totalCount }}</span>
        </div>
        <div class="progress-label">今日任务完成</div>
        <div class="completion-rate" v-if="stats.completion_rate_30d">
          30天完成率 {{ stats.completion_rate_30d }}%
        </div>
      </div>
      <van-circle
        :current-rate="progressRate"
        :rate="progressRate"
        :stroke-width="60"
        size="80px"
        color="#07c160"
        layer-color="#ebedf0"
      >
        <template #default>
          <span class="progress-text">{{ progressRate }}%</span>
        </template>
      </van-circle>
    </div>

    <van-loading v-if="loading" class="loading" />

    <template v-else>
      <!-- 待完成任务 -->
      <div v-if="pendingTasks.length > 0" class="task-section">
        <h3 class="section-title">待完成 ({{ pendingTasks.length }})</h3>
        <div
          v-for="task in pendingTasks"
          :key="task.id"
          class="task-item card"
        >
          <div class="task-header">
            <div class="task-tags">
              <van-tag :type="domainTagType(task.domain)" size="small">{{ task.domain_name || domainLabel(task.domain) }}</van-tag>
              <van-tag v-if="task.difficulty" plain size="small" :type="difficultyType(task.difficulty)">
                {{ difficultyLabel(task.difficulty) }}
              </van-tag>
              <!-- 来源标签（原则一：三来源可视化） -->
              <van-tag
                v-if="task.source"
                plain
                size="small"
                :type="sourceTagType(task.source)"
                class="source-tag"
              >
                {{ sourceLabel(task.source) }}
              </van-tag>
            </div>
          </div>
          <div class="task-title">{{ task.title }}</div>
          <div v-if="task.description" class="task-desc">{{ task.description }}</div>
          <div class="task-actions">
            <van-button
              type="success"
              size="small"
              round
              @click="showCompleteDialog(task)"
            >
              完成
            </van-button>
            <van-button
              type="default"
              size="small"
              round
              plain
              @click="handleSkip(task)"
            >
              跳过
            </van-button>
          </div>
        </div>
      </div>

      <!-- 已完成任务 -->
      <div v-if="completedTasks.length > 0" class="task-section">
        <h3 class="section-title">已完成 ({{ completedTasks.length }})</h3>
        <div
          v-for="task in completedTasks"
          :key="task.id"
          class="task-item card completed"
        >
          <div class="task-header">
            <div class="task-tags">
              <van-tag :type="domainTagType(task.domain)" size="small" plain>{{ task.domain_name || domainLabel(task.domain) }}</van-tag>
              <van-tag plain size="small" :type="sourceTagType(task.source)" class="source-tag">
                {{ sourceLabel(task.source) }}
              </van-tag>
            </div>
            <van-icon name="success" color="#07c160" />
          </div>
          <div class="task-title done">{{ task.title }}</div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="filteredTasks.length === 0 && !loading" class="empty-state">
        <van-icon name="todo-list-o" size="64" color="#ddd" />
        <p>暂无任务</p>
        <van-button type="primary" size="small" @click="loadTasks">
          刷新任务
        </van-button>
      </div>
    </template>

    <!-- 完成对话框 -->
    <van-dialog
      v-model:show="showDialog"
      title="完成任务"
      show-cancel-button
      @confirm="handleComplete"
    >
      <div class="complete-dialog">
        <div class="mood-select">
          <p>完成后的心情</p>
          <div class="mood-options">
            <span
              v-for="m in moodOptions"
              :key="m.value"
              class="mood-item"
              :class="{ active: completeForm.mood_score === m.value }"
              @click="completeForm.mood_score = m.value"
            >
              {{ m.emoji }}
            </span>
          </div>
        </div>
        <van-field
          v-model="completeForm.note"
          type="textarea"
          placeholder="写点什么（可选）"
          rows="2"
          maxlength="200"
          show-word-limit
        />
      </div>
    </van-dialog>

  </PageShell>

  <!-- 悬浮添加按钮（原则一：三来源入口） -->
  <div class="fab-add" @click="openAddPanel">
    <van-icon name="plus" size="24" color="#fff" />
  </div>

  <!-- 添加任务底部面板 -->
  <van-popup
    v-model:show="showAddPanel"
    position="bottom"
    :style="{ height: '75vh', borderRadius: '16px 16px 0 0' }"
    safe-area-inset-bottom
  >
    <div class="add-panel">
      <div class="add-panel-header">
        <span class="add-panel-title">添加任务</span>
        <van-icon name="cross" @click="showAddPanel = false" />
      </div>

      <!-- 三来源说明 -->
      <div class="source-legend">
        <span class="legend-item coach">教练指定</span>
        <span class="legend-item ai">AI推荐</span>
        <span class="legend-item self">自选</span>
      </div>

      <van-loading v-if="poolLoading" class="pool-loading" />

      <van-tabs v-else v-model:active="addTab" animated>
        <!-- Tab 1: AI推荐（原则一 L2，关注领域优先） -->
        <van-tab title="AI推荐" name="ai">
          <div class="tab-content">
            <div v-if="taskPool.ai_recommended?.length === 0" class="pool-empty">
              <p>暂无 AI 推荐</p>
              <p class="hint">设置关注领域后将自动生成</p>
            </div>
            <div
              v-for="(candidate, idx) in taskPool.ai_recommended"
              :key="idx"
              class="candidate-card"
              :class="{ 'already-today': candidate.already_today }"
            >
              <div class="candidate-header">
                <van-tag type="primary" size="small">{{ candidate.domain_name }}</van-tag>
                <van-tag plain size="small" :type="difficultyType(candidate.difficulty)">
                  {{ difficultyLabel(candidate.difficulty) }}
                </van-tag>
                <span v-if="candidate.already_today" class="today-hint">今日已有</span>
              </div>
              <div class="candidate-title">{{ candidate.title }}</div>
              <div v-if="candidate.description" class="candidate-desc">{{ candidate.description }}</div>
              <van-button
                type="primary"
                size="small"
                round
                :disabled="candidate.already_today"
                @click="addCandidateTask(candidate)"
              >
                {{ candidate.already_today ? '今日已有' : '添加' }}
              </van-button>
            </div>
          </div>
        </van-tab>

        <!-- Tab 2: 自选（原则一 L3，按关注领域分组） -->
        <van-tab title="自选" name="self">
          <div class="tab-content">
            <div v-if="Object.keys(taskPool.user_selectable || {}).length === 0" class="pool-empty">
              <p>暂无候选任务</p>
            </div>

            <!-- 关注领域（优先展示） -->
            <template v-for="(info, domain) in taskPool.user_selectable" :key="domain">
              <div v-if="info.is_focus" class="domain-group">
                <div class="domain-group-header">
                  <span class="domain-label">{{ info.domain_name }}</span>
                  <van-tag size="small" type="success">关注</van-tag>
                </div>
                <div
                  v-for="(c, i) in info.candidates"
                  :key="i"
                  class="candidate-card"
                  :class="{ 'already-today': c.already_today }"
                >
                  <div class="candidate-header">
                    <van-tag plain size="small" :type="difficultyType(c.difficulty)">
                      {{ difficultyLabel(c.difficulty) }}
                    </van-tag>
                    <span v-if="c.already_today" class="today-hint">今日已有</span>
                  </div>
                  <div class="candidate-title">{{ c.title }}</div>
                  <div v-if="c.description" class="candidate-desc">{{ c.description }}</div>
                  <van-button
                    type="success"
                    size="small"
                    round
                    :disabled="c.already_today"
                    @click="addCandidateTask(c)"
                  >
                    {{ c.already_today ? '今日已有' : '选择' }}
                  </van-button>
                </div>
              </div>
            </template>

            <!-- 其他领域（折叠展示） -->
            <van-collapse v-model="expandedDomains">
              <template v-for="(info, domain) in taskPool.user_selectable" :key="domain">
                <van-collapse-item
                  v-if="!info.is_focus"
                  :title="info.domain_name"
                  :name="domain"
                >
                  <div
                    v-for="(c, i) in info.candidates"
                    :key="i"
                    class="candidate-card"
                    :class="{ 'already-today': c.already_today }"
                  >
                    <div class="candidate-header">
                      <van-tag plain size="small" :type="difficultyType(c.difficulty)">
                        {{ difficultyLabel(c.difficulty) }}
                      </van-tag>
                    </div>
                    <div class="candidate-title">{{ c.title }}</div>
                    <div v-if="c.description" class="candidate-desc">{{ c.description }}</div>
                    <van-button
                      type="success"
                      size="small"
                      round
                      :disabled="c.already_today"
                      @click="addCandidateTask(c)"
                    >
                      {{ c.already_today ? '今日已有' : '选择' }}
                    </van-button>
                  </div>
                </van-collapse-item>
              </template>
            </van-collapse>
          </div>
        </van-tab>

        <!-- Tab 3: 教练指定（原则一 L1，只读展示） -->
        <van-tab title="教练指定" name="coach">
          <div class="tab-content">
            <div v-if="taskPool.coach_pending?.length === 0" class="pool-empty">
              <p>暂无教练指定任务</p>
              <p class="hint">教练指定任务经 AI 生成后由教练审核推送</p>
            </div>
            <div
              v-for="task in taskPool.coach_pending"
              :key="task.id"
              class="candidate-card coach-card"
            >
              <div class="candidate-header">
                <van-tag type="warning" size="small">{{ task.domain_name || domainLabel(task.domain) }}</van-tag>
                <van-tag plain size="small" :type="difficultyType(task.difficulty)">
                  {{ difficultyLabel(task.difficulty) }}
                </van-tag>
                <van-tag type="warning" size="small" plain>教练指定</van-tag>
              </div>
              <div class="candidate-title">{{ task.title }}</div>
              <div v-if="task.description" class="candidate-desc">{{ task.description }}</div>
              <p class="coach-readonly-hint">教练指定任务已在今日任务中，无需重复添加</p>
            </div>
          </div>
        </van-tab>
      </van-tabs>
    </div>
  </van-popup>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { showToast, showSuccessToast } from 'vant'
import PageShell from '@/components/common/PageShell.vue'
import api from '@/api/index'

interface Task {
  id: number
  domain: string
  domain_name?: string
  title: string
  description?: string
  difficulty?: string
  status: string
  source?: string
}

interface Candidate {
  domain: string
  domain_name: string
  title: string
  description?: string
  difficulty: string
  rx_id?: string
  source_hint?: string
  already_today?: boolean
}

interface TaskPool {
  focus_domains: string[]
  covered_today: string[]
  coach_pending: Task[]
  ai_recommended: Candidate[]
  user_selectable: Record<string, {
    domain_name: string
    is_focus: boolean
    candidates: Candidate[]
  }>
}

const loading = ref(true)
const tasks = ref<Task[]>([])
const stats = reactive({
  streak_days: 0,
  completion_rate_30d: 0,
  action_completed_7d: 0,
})

const filterType = ref('all')
const filterOptions = [
  { text: '全部', value: 'all' },
  { text: '营养', value: 'nutrition' },
  { text: '运动', value: 'exercise' },
  { text: '睡眠', value: 'sleep' },
  { text: '情绪', value: 'emotion' },
  { text: '压力', value: 'stress' },
  { text: '认知', value: 'cognitive' },
  { text: '社交', value: 'social' },
]

const filteredTasks = computed(() => {
  if (filterType.value === 'all') return tasks.value
  return tasks.value.filter(t => t.domain === filterType.value)
})

const pendingTasks = computed(() => filteredTasks.value.filter(t => t.status === 'pending'))
const completedTasks = computed(() => filteredTasks.value.filter(t => t.status === 'completed'))

const totalCount = computed(() => filteredTasks.value.length)
const completedCount = computed(() => completedTasks.value.length)
const progressRate = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((completedCount.value / totalCount.value) * 100)
})

// 完成对话框
const showDialog = ref(false)
const selectedTask = ref<Task | null>(null)
const completeForm = reactive({ note: '', mood_score: 0 })
const moodOptions = [
  { value: 1, emoji: '\u{1F614}' },
  { value: 2, emoji: '\u{1F610}' },
  { value: 3, emoji: '\u{1F642}' },
  { value: 4, emoji: '\u{1F60A}' },
  { value: 5, emoji: '\u{1F929}' },
]

// 添加任务面板
const showAddPanel = ref(false)
const addTab = ref('ai')
const poolLoading = ref(false)
const taskPool = ref<TaskPool>({
  focus_domains: [],
  covered_today: [],
  coach_pending: [],
  ai_recommended: [],
  user_selectable: {},
})
const expandedDomains = ref<string[]>([])

// ────────────────────────────────────────────────────────────────
// 标签映射
// ────────────────────────────────────────────────────────────────

function domainLabel(domain: string) {
  const map: Record<string, string> = {
    nutrition: '营养', exercise: '运动', sleep: '睡眠',
    emotion: '情绪', stress: '压力', cognitive: '认知',
    social: '社交', tcm: '中医',
  }
  return map[domain] || domain
}

function domainTagType(domain: string) {
  const map: Record<string, string> = {
    nutrition: 'success', exercise: 'warning', sleep: 'primary',
    emotion: 'danger', stress: 'primary', cognitive: 'primary',
    social: 'primary', tcm: 'success',
  }
  return map[domain] || 'default'
}

function difficultyLabel(d: string) {
  return { easy: '简单', moderate: '适中', challenging: '挑战' }[d] || d
}

function difficultyType(d: string) {
  return { easy: 'success', moderate: 'warning', challenging: 'danger' }[d] || 'default'
}

/** 来源标签（原则一：三来源可视化） */
function sourceLabel(source: string) {
  const map: Record<string, string> = {
    coach_assigned: '教练指定',
    coach: '教练指定',
    ai_recommended: 'AI推荐',
    user_selected: '自选',
    intervention_plan: '计划',
    system: '系统',
  }
  return map[source] || source
}

function sourceTagType(source: string) {
  const map: Record<string, string> = {
    coach_assigned: 'warning',
    coach: 'warning',
    ai_recommended: 'primary',
    user_selected: 'success',
    intervention_plan: 'default',
    system: 'default',
  }
  return map[source] || 'default'
}

// ────────────────────────────────────────────────────────────────
// 数据加载
// ────────────────────────────────────────────────────────────────

async function loadTasks() {
  loading.value = true
  try {
    const [todayRes, statsRes] = await Promise.allSettled([
      api.get('/api/v1/micro-actions/today'),
      api.get('/api/v1/micro-actions/stats'),
    ])
    if (todayRes.status === 'fulfilled') {
      tasks.value = (todayRes.value as any).tasks || []
    }
    if (statsRes.status === 'fulfilled' && statsRes.value) {
      const s = statsRes.value as any
      stats.streak_days = s.streak_days || 0
      stats.completion_rate_30d = s.completion_rate_30d || 0
      stats.action_completed_7d = s.action_completed_7d || 0
    }
  } catch {
    tasks.value = []
  } finally {
    loading.value = false
  }
}

async function openAddPanel() {
  showAddPanel.value = true
  poolLoading.value = true
  try {
    const pool = await api.get('/api/v1/micro-actions/task-pool') as TaskPool
    taskPool.value = pool
  } catch {
    showToast('加载候选任务失败')
  } finally {
    poolLoading.value = false
  }
}

// ────────────────────────────────────────────────────────────────
// 任务操作
// ────────────────────────────────────────────────────────────────

function showCompleteDialog(task: Task) {
  selectedTask.value = task
  completeForm.note = ''
  completeForm.mood_score = 0
  showDialog.value = true
}

async function handleComplete() {
  if (!selectedTask.value) return
  try {
    const res: any = await api.post(`/api/v1/micro-actions/${selectedTask.value.id}/complete`, {
      note: completeForm.note || undefined,
      mood_score: completeForm.mood_score || undefined,
    })
    const pts = res.points_earned || 3
    showSuccessToast(`完成！+${pts} 积分`)
    await loadTasks()
  } catch {
    showToast('操作失败')
  }
}

async function handleSkip(task: Task) {
  try {
    await api.post(`/api/v1/micro-actions/${task.id}/skip`)
    showToast('已跳过')
    await loadTasks()
  } catch {
    showToast('操作失败')
  }
}

/** 添加候选任务（原则一 L2/L3 + 原则四：从 AI 候选池确认） */
async function addCandidateTask(candidate: Candidate) {
  try {
    const res: any = await api.post('/api/v1/micro-actions/self-add', {
      domain: candidate.domain,
      title: candidate.title,
      description: candidate.description || '',
      difficulty: candidate.difficulty,
      rx_id: candidate.rx_id || undefined,
    })
    showSuccessToast(res.message || '已添加')
    showAddPanel.value = false
    await loadTasks()
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '添加失败'
    showToast(msg)
  }
}

onMounted(loadTasks)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.loading { text-align: center; padding: 40px 0; }

.streak-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  background: linear-gradient(135deg, #fff7e6, #ffe7ba);
  border-radius: $border-radius;
  margin-bottom: $spacing-sm;

  .streak-fire { font-size: 20px; }
  .streak-text { font-size: $font-size-md; font-weight: 600; color: #fa8c16; }
}

.progress-card {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .progress-info {
    .progress-number {
      font-size: 24px;
      font-weight: bold;
      .completed { color: $success-color; }
      .divider { color: $text-color-placeholder; margin: 0 4px; }
      .total { color: $text-color; }
    }
    .progress-label {
      font-size: $font-size-sm;
      color: $text-color-secondary;
      margin-top: 4px;
    }
    .completion-rate {
      font-size: $font-size-xs;
      color: $text-color-placeholder;
      margin-top: 2px;
    }
  }

  .progress-text {
    font-size: $font-size-lg;
    font-weight: bold;
    color: $success-color;
  }
}

.task-section {
  margin-bottom: $spacing-lg;
}

.section-title {
  font-size: $font-size-md;
  color: $text-color-secondary;
  margin-bottom: $spacing-sm;
}

.task-item {
  margin-bottom: $spacing-sm;

  .task-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;

    .task-tags {
      display: flex;
      align-items: center;
      gap: 4px;
      flex-wrap: wrap;
    }
  }

  .source-tag {
    font-size: 10px;
  }

  .task-title {
    font-size: $font-size-md;
    font-weight: 500;
    margin-bottom: 4px;

    &.done {
      text-decoration: line-through;
      color: $text-color-placeholder;
    }
  }

  .task-desc {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    margin-bottom: 8px;
    line-height: 1.5;
  }

  .task-actions {
    display: flex;
    gap: 8px;
    margin-top: 8px;
  }

  &.completed {
    opacity: 0.7;
  }
}

.complete-dialog {
  padding: 16px;

  .mood-select {
    margin-bottom: 12px;

    p {
      font-size: $font-size-sm;
      color: $text-color-secondary;
      margin-bottom: 8px;
    }

    .mood-options {
      display: flex;
      gap: 12px;
      justify-content: center;
    }

    .mood-item {
      font-size: 28px;
      cursor: pointer;
      padding: 4px 6px;
      border-radius: 8px;
      transition: transform 0.2s;

      &.active {
        transform: scale(1.3);
        background: #f0f9eb;
      }
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $spacing-lg * 2;
  color: $text-color-placeholder;

  p { margin: $spacing-md 0; }
}

// ────── 悬浮添加按钮 ──────
.fab-add {
  position: fixed;
  right: 20px;
  bottom: calc(60px + 20px); // TabBar 高度 + 间距
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #07c160, #00a850);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(7, 193, 96, 0.4);
  cursor: pointer;
  z-index: 100;
  transition: transform 0.2s, box-shadow 0.2s;

  &:active {
    transform: scale(0.94);
    box-shadow: 0 2px 6px rgba(7, 193, 96, 0.3);
  }
}

// ────── 添加任务面板 ──────
.add-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding-bottom: env(safe-area-inset-bottom);

  &-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 16px 8px;

    .add-panel-title {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $text-color;
    }

    .van-icon { font-size: 20px; color: $text-color-secondary; cursor: pointer; }
  }
}

.source-legend {
  display: flex;
  gap: 8px;
  padding: 0 16px 10px;

  .legend-item {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;

    &.coach { background: #fff7e6; color: #fa8c16; border: 1px solid #ffd591; }
    &.ai    { background: #e6f4ff; color: #1677ff; border: 1px solid #91caff; }
    &.self  { background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; }
  }
}

.pool-loading { text-align: center; padding: 40px 0; }

.tab-content {
  padding: 12px 16px 80px;
  overflow-y: auto;
  max-height: calc(75vh - 120px);
}

.pool-empty {
  text-align: center;
  padding: 32px 0;
  color: $text-color-placeholder;

  p { margin: 4px 0; }
  .hint { font-size: $font-size-sm; }
}

.domain-group {
  margin-bottom: $spacing-md;

  &-header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 8px;

    .domain-label {
      font-size: $font-size-md;
      font-weight: 600;
      color: $text-color;
    }
  }
}

.candidate-card {
  background: $background-color;
  border-radius: $border-radius;
  padding: 12px;
  margin-bottom: 10px;
  border: 1px solid $border-color;

  &.already-today {
    opacity: 0.55;
  }

  &.coach-card {
    border-color: #ffd591;
    background: #fffbe6;
  }

  .candidate-header {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: 6px;
    flex-wrap: wrap;

    .today-hint {
      font-size: 10px;
      color: $text-color-placeholder;
      margin-left: auto;
    }
  }

  .candidate-title {
    font-size: $font-size-md;
    font-weight: 500;
    margin-bottom: 4px;
    color: $text-color;
  }

  .candidate-desc {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    line-height: 1.5;
    margin-bottom: 8px;
  }

  .coach-readonly-hint {
    font-size: $font-size-xs;
    color: #fa8c16;
    margin-top: 6px;
  }
}
</style>
