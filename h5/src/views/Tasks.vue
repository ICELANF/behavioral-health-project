<template>
  <div class="page-container">
    <van-nav-bar title="我的任务">
      <template #right>
        <van-dropdown-menu>
          <van-dropdown-item v-model="filterType" :options="filterOptions" />
        </van-dropdown-menu>
      </template>
    </van-nav-bar>

    <div class="page-content">
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
              <van-tag :type="domainTagType(task.domain)" size="small">{{ domainLabel(task.domain) }}</van-tag>
              <van-tag v-if="task.difficulty" plain size="small" :type="difficultyType(task.difficulty)">
                {{ difficultyLabel(task.difficulty) }}
              </van-tag>
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
              <van-tag :type="domainTagType(task.domain)" size="small" plain>{{ domainLabel(task.domain) }}</van-tag>
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
    </div>

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

    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { showToast, showSuccessToast } from 'vant'
import TabBar from '@/components/common/TabBar.vue'
import api from '@/api/index'

interface Task {
  id: number
  domain: string
  title: string
  description?: string
  difficulty?: string
  status: string
  source?: string
}

const loading = ref(false)
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

function domainLabel(domain: string) {
  const map: Record<string, string> = {
    nutrition: '营养', exercise: '运动', sleep: '睡眠',
    emotion: '情绪', stress: '压力', cognitive: '认知', social: '社交',
  }
  return map[domain] || domain
}
function domainTagType(domain: string) {
  const map: Record<string, string> = {
    nutrition: 'success', exercise: 'warning', sleep: 'primary',
    emotion: 'danger', stress: 'primary', cognitive: 'primary', social: 'primary',
  }
  return map[domain] || 'default'
}
function difficultyLabel(d: string) {
  return { easy: '简单', moderate: '适中', challenging: '挑战' }[d] || d
}
function difficultyType(d: string) {
  return { easy: 'success', moderate: 'warning', challenging: 'danger' }[d] || 'default'
}

async function loadTasks() {
  loading.value = true
  try {
    const [todayRes, statsRes] = await Promise.all([
      api.get('/api/v1/micro-actions/today'),
      api.get('/api/v1/micro-actions/stats').catch(() => null),
    ])
    tasks.value = (todayRes as any).tasks || []
    if (statsRes) {
      stats.streak_days = (statsRes as any).streak_days || 0
      stats.completion_rate_30d = (statsRes as any).completion_rate_30d || 0
      stats.action_completed_7d = (statsRes as any).action_completed_7d || 0
    }
  } catch {
    tasks.value = []
  } finally {
    loading.value = false
  }
}

function showCompleteDialog(task: Task) {
  selectedTask.value = task
  completeForm.note = ''
  completeForm.mood_score = 0
  showDialog.value = true
}

async function handleComplete() {
  if (!selectedTask.value) return
  try {
    await api.post(`/api/v1/micro-actions/${selectedTask.value.id}/complete`, {
      note: completeForm.note || undefined,
      mood_score: completeForm.mood_score || undefined,
    })
    showSuccessToast('完成!')
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

  p {
    margin: $spacing-md 0;
  }
}
</style>
