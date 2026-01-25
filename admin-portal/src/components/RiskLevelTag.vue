<script setup lang="ts">
import { computed } from 'vue'
import { Tag } from 'ant-design-vue'
import { RISK_LEVELS } from '@/constants'
import type { RiskLevel } from '@/types'

const props = defineProps<{
  level: RiskLevel
  size?: 'small' | 'default'
}>()

const config = computed(() => RISK_LEVELS[props.level] || RISK_LEVELS.normal)
</script>

<template>
  <Tag
    :color="config.color"
    :style="{
      backgroundColor: config.bgColor,
      borderColor: config.color,
      fontSize: size === 'small' ? '12px' : '14px'
    }"
  >
    {{ config.label }}
  </Tag>
</template>
