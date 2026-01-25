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
      <!-- 进度统计 -->
      <div class="progress-card card">
        <div class="progress-info">
          <div class="progress-number">
            <span class="completed">{{ completedCount }}</span>
            <span class="divider">/</span>
            <span class="total">{{ totalCount }}</span>
          </div>
          <div class="progress-label">任务完成</div>
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

      <!-- 待完成任务 -->
      <div v-if="pendingTasks.length > 0" class="task-section">
        <h3 class="section-title">待完成 ({{ pendingTasks.length }})</h3>
        <TaskCard
          v-for="task in pendingTasks"
          :key="task.id"
          :task="task"
          @toggle="chatStore.toggleTaskComplete"
        />
      </div>

      <!-- 已完成任务 -->
      <div v-if="completedTasks.length > 0" class="task-section">
        <h3 class="section-title">已完成 ({{ completedTasks.length }})</h3>
        <TaskCard
          v-for="task in completedTasks"
          :key="task.id"
          :task="task"
          @toggle="chatStore.toggleTaskComplete"
        />
      </div>

      <!-- 空状态 -->
      <div v-if="filteredTasks.length === 0" class="empty-state">
        <van-icon name="todo-list-o" size="64" color="#ddd" />
        <p>暂无任务</p>
        <van-button type="primary" size="small" to="/chat">
          开始对话获取任务
        </van-button>
      </div>
    </div>

    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import TabBar from '@/components/common/TabBar.vue'
import TaskCard from '@/components/chat/TaskCard.vue'

const chatStore = useChatStore()

const filterType = ref('all')
const filterOptions = [
  { text: '全部', value: 'all' },
  { text: '心理', value: 'mental' },
  { text: '营养', value: 'nutrition' },
  { text: '运动', value: 'exercise' },
  { text: '中医', value: 'tcm' }
]

const filteredTasks = computed(() => {
  if (filterType.value === 'all') {
    return chatStore.tasks
  }
  return chatStore.tasks.filter(t => t.type === filterType.value)
})

const pendingTasks = computed(() => filteredTasks.value.filter(t => !t.completed))
const completedTasks = computed(() => filteredTasks.value.filter(t => t.completed))

const totalCount = computed(() => filteredTasks.value.length)
const completedCount = computed(() => completedTasks.value.length)
const progressRate = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((completedCount.value / totalCount.value) * 100)
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.progress-card {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .progress-info {
    .progress-number {
      font-size: 24px;
      font-weight: bold;

      .completed {
        color: $success-color;
      }

      .divider {
        color: $text-color-placeholder;
        margin: 0 4px;
      }

      .total {
        color: $text-color;
      }
    }

    .progress-label {
      font-size: $font-size-sm;
      color: $text-color-secondary;
      margin-top: 4px;
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
