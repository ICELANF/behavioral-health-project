<script setup lang="ts">
import { computed } from 'vue'
import { Tag, Tooltip } from 'ant-design-vue'
import { COACH_LEVELS } from '@/constants'
import type { CoachLevel } from '@/types'

const props = defineProps<{
  level: CoachLevel
  showDescription?: boolean
}>()

const config = computed(() => COACH_LEVELS[props.level] || COACH_LEVELS.L0)
</script>

<template>
  <Tooltip v-if="showDescription" :title="config.description">
    <Tag :color="config.color" class="coach-level-badge">
      <span class="level-code">{{ level }}</span>
      <span class="level-label">{{ config.label }}</span>
    </Tag>
  </Tooltip>
  <Tag v-else :color="config.color" class="coach-level-badge">
    <span class="level-code">{{ level }}</span>
    <span class="level-label">{{ config.label }}</span>
  </Tag>
</template>

<style scoped>
.coach-level-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
}

.level-code {
  font-weight: 600;
}

.level-label {
  font-size: 12px;
}
</style>
