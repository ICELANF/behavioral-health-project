<template>
  <div class="health-task-list">
    <!-- 标题栏 -->
    <div v-if="showHeader" class="task-header">
      <div class="task-title">
        <span class="title-icon" v-if="titleIcon">{{ titleIcon }}</span>
        <span class="title-text">{{ title }}</span>
      </div>
      <div v-if="!showProgressRing && showProgress" class="task-progress">
        {{ completedCount }}/{{ tasks.length }}
      </div>
    </div>

    <!-- 进度环区域（独立于标题栏） -->
    <div v-if="showProgressRing && tasks.length > 0" class="progress-ring-section">
      <svg class="progress-ring" width="56" height="56" viewBox="0 0 56 56">
        <circle class="ring-bg" cx="28" cy="28" r="23" fill="none" stroke="#e5e7eb" stroke-width="4" />
        <circle
          class="ring-fg"
          cx="28" cy="28" r="23"
          fill="none"
          stroke="#10b981"
          stroke-width="4"
          stroke-linecap="round"
          :stroke-dasharray="ringCircumference"
          :stroke-dashoffset="ringOffset"
          transform="rotate(-90 28 28)"
        />
      </svg>
      <div class="ring-info">
        <span class="ring-text">{{ completedCount }}/{{ tasks.length }}</span>
        <span class="ring-hint" v-if="allCompleted">全部完成！</span>
        <span class="ring-hint" v-else>还有 {{ tasks.length - completedCount }} 项待完成</span>
      </div>
    </div>

    <!-- 已完成折叠区 -->
    <div
      v-if="collapsible && completedTasks.length > 0"
      class="completed-toggle"
      @click="showCompleted = !showCompleted"
    >
      <CheckOutlined class="completed-toggle-icon" />
      <span>已完成 {{ completedTasks.length }} 项</span>
      <span class="toggle-arrow" :class="{ expanded: showCompleted }">&#9654;</span>
    </div>

    <!-- 已完成任务列表（折叠） -->
    <TransitionGroup name="task-slide" tag="div" class="task-list compact" v-if="collapsible && showCompleted">
      <div
        v-for="task in completedTasks"
        :key="task.id"
        class="task-item completed"
      >
        <div class="task-checkbox">
          <div class="checkbox checked"><CheckOutlined /></div>
        </div>
        <div class="task-content">
          <div class="task-name">{{ task.name }}</div>
        </div>
        <div v-if="task.emoji" class="task-icon-sm">{{ task.emoji }}</div>
        <span v-if="showSourceBadge && task.source" class="source-badge" :class="'source-' + task.source">
          {{ sourceLabel(task.source) }}
        </span>
      </div>
    </TransitionGroup>

    <!-- 未完成任务列表 -->
    <TransitionGroup name="task-slide" tag="div" class="task-list" :class="{ compact: compact }">
      <div
        v-for="task in visibleUncompletedTasks"
        :key="task.id"
        class="task-item"
        :class="{ disabled: task.disabled }"
        @click="handleTaskClick(task)"
      >
        <div class="task-checkbox">
          <div class="checkbox">
            <span class="checkbox-ring"></span>
          </div>
        </div>
        <div class="task-content">
          <div class="task-name">{{ task.name }}</div>
          <div v-if="task.hint" class="task-hint">{{ task.hint }}</div>
        </div>
        <div v-if="task.emoji" class="task-icon">{{ task.emoji }}</div>
        <span v-if="showSourceBadge && task.source" class="source-badge" :class="'source-' + task.source">
          {{ sourceLabel(task.source) }}
        </span>
        <!-- 删除按钮：仅自选+未完成 -->
        <button
          v-if="showDeleteButton && task.source === 'self' && !task.completed"
          class="delete-btn"
          @click.stop="handleDelete(task)"
          title="删除任务"
        >&times;</button>
      </div>
    </TransitionGroup>

    <!-- "还有 N 项" 展开行 -->
    <div
      v-if="hasMoreUncompleted"
      class="show-more-row"
      @click="showAllUncompleted = !showAllUncompleted"
    >
      <template v-if="!showAllUncompleted">还有 {{ hiddenUncompletedCount }} 项 &#9654;</template>
      <template v-else>收起 &#9660;</template>
    </div>

    <!-- 全部完成鼓励（非折叠模式） -->
    <div v-if="!collapsible && showEncouragement && allCompleted" class="task-encouragement">
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
import { ref, computed } from 'vue'
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
  source?: 'rx' | 'self' | 'coach'
}

interface Props {
  tasks: Task[]
  title?: string
  titleIcon?: string
  showHeader?: boolean
  showProgress?: boolean
  showProgressRing?: boolean
  showSourceBadge?: boolean
  showDeleteButton?: boolean
  collapsible?: boolean
  maxUncompleted?: number
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
  (e: 'delete', task: Task): void
}

const props = withDefaults(defineProps<Props>(), {
  title: '任务列表',
  titleIcon: '✨',
  showHeader: true,
  showProgress: true,
  showProgressRing: false,
  showSourceBadge: false,
  showDeleteButton: false,
  collapsible: false,
  maxUncompleted: 5,
  showEncouragement: true,
  encouragementIcon: '🎉',
  encouragementText: '太棒了！所有任务已完成',
  emptyIcon: '📝',
  emptyText: '暂无任务',
  compact: false
})

const emit = defineEmits<Emits>()

// 折叠状态
const showCompleted = ref(false)
const showAllUncompleted = ref(false)

// 计算属性
const completedCount = computed(() => props.tasks.filter(t => t.completed).length)
const allCompleted = computed(() => props.tasks.length > 0 && completedCount.value === props.tasks.length)

const completedTasks = computed(() => props.tasks.filter(t => t.completed))
const uncompletedTasks = computed(() => props.tasks.filter(t => !t.completed))

const visibleUncompletedTasks = computed(() => {
  if (!props.collapsible || showAllUncompleted.value || uncompletedTasks.value.length <= props.maxUncompleted) {
    return uncompletedTasks.value
  }
  return uncompletedTasks.value.slice(0, props.maxUncompleted)
})

const hasMoreUncompleted = computed(() =>
  props.collapsible && uncompletedTasks.value.length > props.maxUncompleted
)

const hiddenUncompletedCount = computed(() =>
  uncompletedTasks.value.length - props.maxUncompleted
)

// SVG 进度环
const ringCircumference = computed(() => 2 * Math.PI * 23) // r=23
const ringOffset = computed(() => {
  if (props.tasks.length === 0) return ringCircumference.value
  const pct = completedCount.value / props.tasks.length
  return ringCircumference.value * (1 - pct)
})

// 来源标签
const sourceLabel = (source: string) => {
  const map: Record<string, string> = {
    rx: '🤖 系统',
    self: '👤 自选',
    coach: '👨‍⚕️ 教练',
  }
  return map[source] || source
}

// 事件
const handleTaskClick = (task: Task) => {
  if (task.disabled) return
  emit('toggle', task)
  emit('click', task)
}

const handleDelete = (task: Task) => {
  emit('delete', task)
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
  margin-bottom: 12px;
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

/* 进度环区域 */
.progress-ring-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 12px 0 16px;
  margin-bottom: 4px;
}

.progress-ring {
  flex-shrink: 0;
}

.ring-fg {
  transition: stroke-dashoffset 0.6s ease;
}

.ring-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ring-text {
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
}

.ring-hint {
  font-size: 13px;
  color: #6b7280;
}

.task-progress {
  background: #f3f4f6;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
}

/* 已完成折叠切换 */
.completed-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #f0fdf4;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #059669;
  margin-bottom: 10px;
  transition: background 0.2s;
}

.completed-toggle:hover {
  background: #dcfce7;
}

.completed-toggle-icon {
  color: #10b981;
}

.toggle-arrow {
  margin-left: auto;
  font-size: 10px;
  transition: transform 0.3s;
  color: #9ca3af;
}

.toggle-arrow.expanded {
  transform: rotate(90deg);
}

/* 任务列表 */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-list.compact {
  gap: 6px;
  margin-bottom: 10px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #f9fafb;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
  position: relative;
}

.task-item:hover {
  background: #f3f4f6;
  transform: translateX(4px);
}

.task-item.completed {
  opacity: 0.6;
  background: #f0fdf4;
  border-color: #10b981;
  padding: 10px 14px;
  cursor: default;
}

.task-item.completed:hover {
  transform: none;
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
  width: 28px;
  height: 28px;
  border: 3px solid #d1d5db;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: all 0.3s;
  flex-shrink: 0;
}

.checkbox.checked {
  background: #10b981;
  border-color: #10b981;
  color: #fff;
  width: 24px;
  height: 24px;
  font-size: 12px;
}

/* 任务内容 */
.task-content {
  flex: 1;
  min-width: 0;
}

.task-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.task-item.completed .task-name {
  text-decoration: line-through;
  color: #9ca3af;
  font-size: 13px;
}

.task-hint {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 2px;
}

/* 任务图标 */
.task-icon {
  font-size: 28px;
  opacity: 0.8;
  flex-shrink: 0;
}

.task-icon-sm {
  font-size: 20px;
  opacity: 0.6;
  flex-shrink: 0;
}

/* 来源标签 */
.source-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
  white-space: nowrap;
}

.source-rx {
  background: #dbeafe;
  color: #1d4ed8;
}

.source-self {
  background: #ede9fe;
  color: #6d28d9;
}

.source-coach {
  background: #fef3c7;
  color: #92400e;
}

/* 删除按钮 */
.delete-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: #fee2e2;
  color: #dc2626;
  border-radius: 50%;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  padding: 0;
}

.delete-btn:hover {
  background: #fca5a5;
  transform: scale(1.1);
}

/* "还有 N 项" 行 */
.show-more-row {
  text-align: center;
  padding: 10px;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
  border-radius: 10px;
  margin-top: 6px;
  transition: background 0.2s;
}

.show-more-row:hover {
  background: #f3f4f6;
  color: #374151;
}

/* TransitionGroup 动画 */
.task-slide-enter-active,
.task-slide-leave-active {
  transition: all 0.4s ease;
}

.task-slide-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.task-slide-leave-to {
  opacity: 0;
  transform: translateX(20px);
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  margin-top: 0;
  margin-bottom: 0;
  overflow: hidden;
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
