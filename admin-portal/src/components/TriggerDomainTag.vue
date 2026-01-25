<script setup lang="ts">
import { computed } from 'vue'
import { Tag } from 'ant-design-vue'
import {
  ExperimentOutlined,
  CoffeeOutlined,
  ThunderboltOutlined,
  MedicineBoxOutlined,
  RestOutlined,
  HeartOutlined,
  DashboardOutlined
} from '@ant-design/icons-vue'
import { TRIGGER_DOMAINS } from '@/constants'
import type { TriggerDomain } from '@/types'

const props = defineProps<{
  domain: TriggerDomain
  showIcon?: boolean
}>()

const config = computed(() => TRIGGER_DOMAINS[props.domain])

const iconMap = {
  experiment: ExperimentOutlined,
  coffee: CoffeeOutlined,
  thunderbolt: ThunderboltOutlined,
  'medicine-box': MedicineBoxOutlined,
  rest: RestOutlined,
  heart: HeartOutlined,
  dashboard: DashboardOutlined
}

const IconComponent = computed(() => {
  if (!config.value) return null
  return iconMap[config.value.icon as keyof typeof iconMap]
})
</script>

<template>
  <Tag v-if="config" :color="config.color" class="trigger-domain-tag">
    <component v-if="showIcon && IconComponent" :is="IconComponent" />
    <span>{{ config.label }}</span>
  </Tag>
</template>

<style scoped>
.trigger-domain-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
</style>
