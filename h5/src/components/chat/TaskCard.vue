<template>
  <div class="task-card" :class="{ 'is-completed': task.completed }">
    <div class="task-header">
      <van-checkbox
        :model-value="task.completed"
        @update:model-value="onToggle"
        shape="square"
      />
      <span class="task-type" :class="'type-' + task.type">
        {{ typeLabel }}
      </span>
    </div>
    <div class="task-content">{{ task.content }}</div>
    <div class="task-footer">
      <div class="task-difficulty">
        <van-icon
          v-for="i in 5"
          :key="i"
          :name="i <= task.difficulty ? 'star' : 'star-o'"
          :class="{ active: i <= task.difficulty }"
        />
      </div>
      <span v-if="task.expert" class="task-expert">{{ task.expert }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Task } from '@/api/types'

interface Props {
  task: Task
}

const props = defineProps<Props>()
const emit = defineEmits<{
  toggle: [id: number]
}>()

const typeLabel = computed(() => {
  const labels: Record<string, string> = {
    mental: '心理',
    nutrition: '营养',
    exercise: '运动',
    tcm: '中医'
  }
  return labels[props.task.type] || '其他'
})

function onToggle() {
  emit('toggle', props.task.id)
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.task-card {
  background-color: $background-color-light;
  border-radius: $border-radius;
  padding: $spacing-sm;
  margin-bottom: $spacing-xs;
  border-left: 3px solid $primary-color;
  transition: all 0.3s;

  &.is-completed {
    opacity: 0.6;
    border-left-color: $success-color;

    .task-content {
      text-decoration: line-through;
      color: $text-color-secondary;
    }
  }
}

.task-header {
  display: flex;
  align-items: center;
  margin-bottom: $spacing-xs;
}

.task-type {
  margin-left: $spacing-xs;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: $font-size-xs;

  &.type-mental {
    background-color: rgba($expert-mental, 0.1);
    color: $expert-mental;
  }

  &.type-nutrition {
    background-color: rgba($expert-nutrition, 0.1);
    color: $expert-nutrition;
  }

  &.type-exercise {
    background-color: rgba($expert-sports, 0.1);
    color: $expert-sports;
  }

  &.type-tcm {
    background-color: rgba($expert-tcm, 0.1);
    color: $expert-tcm;
  }
}

.task-content {
  font-size: $font-size-md;
  line-height: 1.5;
  margin-bottom: $spacing-xs;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-difficulty {
  .van-icon {
    font-size: 12px;
    color: $text-color-placeholder;
    margin-right: 2px;

    &.active {
      color: $warning-color;
    }
  }
}

.task-expert {
  font-size: $font-size-xs;
  color: $text-color-secondary;
}
</style>
