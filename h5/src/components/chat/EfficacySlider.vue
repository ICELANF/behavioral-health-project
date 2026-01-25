<template>
  <div class="efficacy-slider">
    <div class="efficacy-header">
      <span class="efficacy-label">效能感</span>
      <span class="efficacy-value" :style="{ color: efficacyColor }">
        {{ modelValue }}
      </span>
    </div>
    <van-slider
      :model-value="modelValue"
      @update:model-value="onUpdate"
      :min="0"
      :max="100"
      :bar-height="8"
      :active-color="efficacyColor"
    />
    <div class="efficacy-status" :style="{ color: efficacyColor }">
      {{ efficacyText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const efficacyColor = computed(() => {
  if (props.modelValue < 20) return '#ee0a24'
  if (props.modelValue < 50) return '#ff976a'
  return '#07c160'
})

const efficacyText = computed(() => {
  if (props.modelValue < 20) return '需要休息'
  if (props.modelValue < 50) return '逐步恢复'
  return '状态良好'
})

function onUpdate(value: number | number[]) {
  emit('update:modelValue', Array.isArray(value) ? value[0] : value)
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.efficacy-slider {
  padding: $spacing-sm $spacing-md;
  background-color: $background-color-light;
  border-top: 1px solid $border-color;
}

.efficacy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-xs;
}

.efficacy-label {
  font-size: $font-size-sm;
  color: $text-color-secondary;
}

.efficacy-value {
  font-size: $font-size-lg;
  font-weight: bold;
}

.efficacy-status {
  text-align: center;
  font-size: $font-size-sm;
  margin-top: $spacing-xs;
  font-weight: 500;
}
</style>
