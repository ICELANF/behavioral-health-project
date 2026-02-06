<template>
  <div class="health-task-list">
    <!-- 标题栏 -->
    <div v-if="showHeader" class="task-header">
      <div class="task-title">
        <span class="title-icon" v-if="titleIcon">{{ titleIcon }}</span>
        <span class="title-text">{{ title }}</span>
      </div>
      <div v-if="showProgress" class="task-progress">
        {{ completedCount }}/{{ tasks.length }}
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="task-list" :class="{ compact: compact }">
      <div
        v-for="task in tasks"
        :key="task.id"
        class="task-item"
        :class="{ completed: task.completed, disabled: task.disabled }"
        @click="handleTaskClick(task)"
      >
        <!-- 复选框 -->
        <div class="task-checkbox">
          <div class="checkbox" :class="{ checked: task.completed }">
            <CheckOutlined v-if="task.completed" />
          </div>
        </div>

        <!-- 任务内容 -->
        <div class="task-content">
          <div class="task-name">{{ task.name }}</div>
          <div v-if="task.hint" class="task-hint">💡 {{ task.hint }}</div>
          <div v-if="task.dueTime" class="task-due-time">
            ⏰ {{ task.dueTime }}
          </div>
        </div>

        <!-- 任务图标/徽章 -->
        <div v-if="task.icon || task.emoji" class="task-icon">
          {{ task.emoji || task.icon }}
        </div>
        <div v-else-if="task.priority" class="task-priority" :class="`priority-${task.priority}`">
          {{ priorityLabel(task.priority) }}
        </div>
      </div>
    </div>

    <!-- 完成鼓励 -->
    <div v-if="showEncouragement && allCompleted" class="task-encouragement">
      <div class="congrats-icon">{{ encouragementIcon }}</div>
      <div class="congrats-text">{{ encouragementText }}</div>
    </div>

    <!-- 空状态 -->
    <div v-if="tasks.length === 0" class="task-empty">
      <div class="empty-icon">{{ emptyIcon }}</div>
      <div class="empty-text">{{ emptyText }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CheckOutlined } from '@ant-design/icons-vue'

export interface Task {
  id: string | number
  name: string
  completed: boolean
  disabled?: boolean
  hint?: string
  dueTime?: string
  icon?: string
  emoji?: string
  priority?: 'high' | 'medium' | 'low'
}

interface Props {
  tasks: Task[]
  title?: string
  titleIcon?: string
  showHeader?: boolean
  showProgress?: boolean
  showEncouragement?: boolean
  encouragementIcon?: string
  encouragementText?: string
  emptyIcon?: string
  emptyText?: string
  compact?: boolean
}

interface Emits {
  (e: 'toggle', task: Task): void
  (e: 'click', task: Task): void
}

const props = withDefaults(defineProps<Props>(), {
  title: '任务列表',
  titleIcon: '✨',
  showHeader: true,
  showProgress: true,
  showEncouragement: true,
  encouragementIcon: '🎉',
  encouragementText: '太棒了！所有任务已完成',
  emptyIcon: '📝',
  emptyText: '暂无任务',
  compact: false
})

const emit = defineEmits<Emits>()

const completedCount = computed(() => {
  return props.tasks.filter(t => t.completed).length
})

const allCompleted = computed(() => {
  return props.tasks.length > 0 && completedCount.value === props.tasks.length
})

const handleTaskClick = (task: Task) => {
  if (task.disabled) return
  emit('toggle', task)
  emit('click', task)
}

const priorityLabel = (priority: 'high' | 'medium' | 'low') => {
  const map = {
    high: '高',
    medium: '中',
    low: '低'
  }
  return map[priority]
}
</script>

<style scoped>
.health-task-list {
  width: 100%;
}

/* 标题栏 */
.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.task-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 20px;
}

.title-text {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.task-progress {
  background: #f3f4f6;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
}

/* 任务列表 */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-list.compact {
  gap: 8px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px;
  background: #f9fafb;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.task-list.compact .task-item {
  padding: 14px;
  gap: 12px;
}

.task-item:hover {
  background: #f3f4f6;
  transform: translateX(4px);
}

.task-item.completed {
  opacity: 0.6;
  background: #f0fdf4;
  border-color: #10b981;
}

.task-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.task-item.disabled:hover {
  transform: none;
  background: #f9fafb;
}

/* 复选框 */
.checkbox {
  width: 32px;
  height: 32px;
  border: 3px solid #d1d5db;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.3s;
  flex-shrink: 0;
}

.task-list.compact .checkbox {
  width: 28px;
  height: 28px;
  font-size: 16px;
}

.checkbox.checked {
  background: #10b981;
  border-color: #10b981;
  color: #fff;
}

/* 任务内容 */
.task-content {
  flex: 1;
}

.task-name {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.task-list.compact .task-name {
  font-size: 15px;
}

.task-item.completed .task-name {
  text-decoration: line-through;
  color: #9ca3af;
}

.task-hint,
.task-due-time {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}

/* 任务图标 */
.task-icon {
  font-size: 32px;
  opacity: 0.8;
  flex-shrink: 0;
}

.task-list.compact .task-icon {
  font-size: 28px;
}

.task-priority {
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.task-priority.priority-high {
  background: #fee2e2;
  color: #dc2626;
}

.task-priority.priority-medium {
  background: #fef3c7;
  color: #d97706;
}

.task-priority.priority-low {
  background: #e0e7ff;
  color: #4f46e5;
}

/* 完成鼓励 */
.task-encouragement {
  margin-top: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: 12px;
  text-align: center;
  animation: slideDown 0.5s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.congrats-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.congrats-text {
  font-size: 16px;
  font-weight: 600;
  color: #92400e;
}

/* 空状态 */
.task-empty {
  text-align: center;
  padding: 40px 20px;
  color: #9ca3af;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 15px;
  color: #6b7280;
}
</style>
