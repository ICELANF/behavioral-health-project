<template>
  <span class="source-badge" :class="'source--' + source">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  source: string
}>()

const label = computed(() => {
  switch (props.source) {
    case 'rx': return 'AI处方'
    case 'coach': return '教练指派'
    case 'self': return '自定'
    case 'system': return '系统'
    default: return props.source || ''
  }
})
</script>

<style scoped>
.source-badge {
  display: inline-block;
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  line-height: 1.6;
  vertical-align: middle;
}

.source--rx {
  background: #dcfce7;
  color: #15803d;
}

.source--self {
  background: #f3f4f6;
  color: #6b7280;
}

.source--coach {
  background: #dbeafe;
  color: #1d4ed8;
}

.source--system {
  background: #fff7ed;
  color: #c2410c;
}
</style>
