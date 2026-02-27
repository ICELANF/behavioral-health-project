<template>
  <div class="task-group" v-if="tasks.length > 0">
    <!-- 标题栏 (可点击折叠) -->
    <div class="group-header" @click="expanded = !expanded">
      <div class="header-left">
        <span class="header-icon">{{ icon }}</span>
        <span class="header-title" :style="{ color: themeColors.text }">{{ title }}</span>
        <span class="header-count" :style="{ background: themeColors.bg, color: themeColors.text }">
          {{ tasks.length }}
        </span>
      </div>
      <div class="header-right">
        <slot name="header-action" />
        <span class="expand-arrow" :class="{ open: expanded }">&#9662;</span>
      </div>
    </div>

    <!-- 任务列表 -->
    <Transition name="group-expand">
      <div class="group-body" v-show="expanded">
        <div
          v-for="action in visibleTasks" :key="action.id"
          class="action-card" :class="{ done: action.done, active: !action.done }"
          @click="$emit('click-action', action)"
        >
          <!-- 左: 完成圆圈 -->
          <div class="action-check">
            <div class="check-circle" :class="{ checked: action.done }">
              <span v-if="action.done" class="check-icon">&#10003;</span>
              <span v-else class="action-order">{{ action.order }}</span>
            </div>
          </div>

          <!-- 中: 内容 -->
          <div class="action-body">
            <div class="action-title" :class="{ 'line-through': action.done }">
              {{ action.title }}
            </div>
            <div class="action-meta">
              <span class="meta-tag" :style="{ background: action.tagColor + '20', color: action.tagColor }">
                {{ action.tag }}
              </span>
              <TaskSourceBadge v-if="action.source" :source="action.source" />
              <span class="meta-time">{{ action.timeHint }}</span>
            </div>
          </div>

          <!-- 右: 打卡/完成时间 -->
          <div class="action-quick" v-if="!action.done">
            <button class="quick-btn" @click.stop="$emit('checkin', action)">
              {{ action.quickLabel || '打卡' }}
            </button>
          </div>
          <div class="action-quick" v-else>
            <span class="done-time">{{ action.doneTime }}</span>
          </div>
        </div>

        <!-- 展开/收起按钮 -->
        <button
          v-if="tasks.length > maxVisible"
          class="toggle-btn"
          @click.stop="showAll = !showAll"
        >
          {{ showAll ? '收起' : `显示更多 (${tasks.length - maxVisible})` }}
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import TaskSourceBadge from './TaskSourceBadge.vue'
import type { TodayAction } from '@/composables/useTaskGroups'

const props = withDefaults(defineProps<{
  title: string
  icon: string
  color: string
  tasks: TodayAction[]
  defaultExpanded?: boolean
  maxVisible?: number
}>(), {
  defaultExpanded: true,
  maxVisible: 3,
})

defineEmits<{
  (e: 'checkin', action: TodayAction): void
  (e: 'click-action', action: TodayAction): void
}>()

const expanded = ref(props.defaultExpanded)
const showAll = ref(false)

const visibleTasks = computed(() =>
  showAll.value ? props.tasks : props.tasks.slice(0, props.maxVisible)
)

const THEME_MAP: Record<string, { text: string; bg: string }> = {
  blue:    { text: '#1d4ed8', bg: '#dbeafe' },
  green:   { text: '#15803d', bg: '#dcfce7' },
  gray:    { text: '#6b7280', bg: '#f3f4f6' },
  emerald: { text: '#047857', bg: '#d1fae5' },
}

const themeColors = computed(() => THEME_MAP[props.color] || THEME_MAP.gray)
</script>

<style scoped>
.task-group { margin-bottom: 12px; padding: 0 20px; }

/* ── 标题栏 ── */
.group-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 0; cursor: pointer; user-select: none;
}
.header-left { display: flex; align-items: center; gap: 6px; }
.header-icon { font-size: 16px; }
.header-title { font-size: 15px; font-weight: 700; }
.header-count {
  font-size: 11px; font-weight: 700; padding: 1px 7px;
  border-radius: 10px; min-width: 20px; text-align: center;
}
.header-right { display: flex; align-items: center; gap: 8px; }
.expand-arrow {
  font-size: 12px; color: #9ca3af; transition: transform 0.25s;
  display: inline-block;
}
.expand-arrow.open { transform: rotate(0deg); }
.expand-arrow:not(.open) { transform: rotate(-90deg); }

/* ── 任务卡片 (复用 GrowerTodayHome 样式) ── */
.group-body { display: flex; flex-direction: column; gap: 8px; }

.action-card {
  display: flex; align-items: center; gap: 12px;
  background: #fff; border: 1px solid #e5e7eb; border-radius: 14px;
  padding: 14px 16px; transition: all 0.2s; cursor: pointer;
}
.action-card.active:active { transform: scale(0.98); background: #f9fafb; }
.action-card.done { background: #f9fafb; border-color: #f3f4f6; }

.check-circle {
  width: 32px; height: 32px; border-radius: 50%;
  border: 2.5px solid #d1d5db; display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700; color: #9ca3af; transition: all 0.3s; flex-shrink: 0;
}
.check-circle.checked {
  border-color: var(--bhp-brand-primary, #10b981);
  background: var(--bhp-brand-primary, #10b981); color: #fff;
}

.action-body { flex: 1; min-width: 0; }
.action-title { font-size: 14px; font-weight: 600; color: #111827; }
.action-title.line-through { text-decoration: line-through; color: #9ca3af; }
.action-meta { display: flex; align-items: center; gap: 8px; margin-top: 4px; flex-wrap: wrap; }
.meta-tag { font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
.meta-time { font-size: 11px; color: #9ca3af; }

.quick-btn {
  background: var(--bhp-brand-primary, #10b981); color: #fff;
  border: none; border-radius: 8px; padding: 6px 14px;
  font-size: 13px; font-weight: 600; cursor: pointer;
  white-space: nowrap; transition: all 0.2s;
}
.quick-btn:active { transform: scale(0.95); }
.done-time { font-size: 12px; color: #9ca3af; }

/* ── 展开/收起按钮 ── */
.toggle-btn {
  background: none; border: none; color: #6b7280;
  font-size: 13px; padding: 8px 0; cursor: pointer; width: 100%; text-align: center;
}
.toggle-btn:active { color: #374151; }

/* ── 展开/折叠动画 ── */
.group-expand-enter-active,
.group-expand-leave-active { transition: all 0.25s ease; overflow: hidden; }
.group-expand-enter-from,
.group-expand-leave-to { opacity: 0; max-height: 0; }
.group-expand-enter-to,
.group-expand-leave-from { opacity: 1; max-height: 2000px; }
</style>
