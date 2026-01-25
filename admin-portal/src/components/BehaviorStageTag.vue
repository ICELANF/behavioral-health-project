<script setup lang="ts">
import { computed } from 'vue'
import { Tag, Tooltip } from 'ant-design-vue'
import { TTM_STAGES } from '@/constants'
import type { TTMStage } from '@/types'

const props = defineProps<{
  stage: TTMStage
  showTooltip?: boolean
}>()

const config = computed(() => TTM_STAGES[props.stage])

const stageDescriptions: Record<TTMStage, string> = {
  precontemplation: '尚未意识到问题或无改变意愿',
  contemplation: '开始意识到问题，考虑改变',
  preparation: '准备在近期采取行动',
  action: '正在积极改变行为',
  maintenance: '维持新行为，预防复发',
  termination: '新行为已成为习惯'
}

const description = computed(() => stageDescriptions[props.stage])
</script>

<template>
  <Tooltip v-if="showTooltip && config" :title="description">
    <Tag :color="config.color" class="behavior-stage-tag">
      <span class="stage-order">{{ config.order }}</span>
      <span class="stage-label">{{ config.label }}</span>
    </Tag>
  </Tooltip>
  <Tag v-else-if="config" :color="config.color" class="behavior-stage-tag">
    <span class="stage-label">{{ config.label }}</span>
  </Tag>
</template>

<style scoped>
.behavior-stage-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.stage-order {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  font-size: 10px;
  font-weight: 600;
}

.stage-label {
  font-size: 12px;
}
</style>
