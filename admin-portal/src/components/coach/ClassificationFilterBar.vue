<template>
  <div class="classification-filter-bar">
    <!-- 快捷预设行 -->
    <div class="preset-row">
      <a-tag
        v-for="p in presets"
        :key="p.label"
        :color="activePreset === p.label ? 'blue' : 'default'"
        style="cursor: pointer; margin-bottom: 4px"
        @click="$emit('preset', p)"
      >
        {{ p.label }}
      </a-tag>
    </div>

    <!-- 维度筛选芯片 + 排序 -->
    <div class="dimension-chips">
      <a-dropdown v-for="dim in dimensions" :key="dim.key" :trigger="['click']">
        <a-tag
          :color="hasFilter(dim.key) ? 'blue' : 'default'"
          style="cursor: pointer"
        >
          {{ dim.label }} <DownOutlined />
        </a-tag>
        <template #overlay>
          <a-menu @click="(e: any) => $emit('filter', dim.key, e.key)">
            <a-menu-item key="">全部</a-menu-item>
            <a-menu-item v-for="opt in dim.options" :key="opt.value">
              <a-badge :color="opt.color" :text="opt.label" />
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>

      <a-select
        :value="sortBy"
        size="small"
        style="width: 120px"
        @change="(val: string) => $emit('sort', val)"
      >
        <a-select-option value="priority">按优先级</a-select-option>
        <a-select-option value="risk">按风险</a-select-option>
        <a-select-option value="activity">按活跃度</a-select-option>
        <a-select-option value="name">按姓名</a-select-option>
        <a-select-option value="stage">按阶段</a-select-option>
      </a-select>
    </div>

    <!-- 已激活的过滤标签 -->
    <div v-if="activeFilterCount > 0" class="active-filters">
      <a-tag
        v-for="(val, key) in activeFilters"
        :key="key"
        closable
        @close="$emit('filter', key, '')"
      >
        {{ getDimensionLabel(key as string) }}: {{ getValueLabel(key as string, val) }}
      </a-tag>
      <a-button type="link" size="small" @click="$emit('clear')">清除全部</a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { DownOutlined } from '@ant-design/icons-vue'
import {
  DIMENSIONS, PRESETS,
  getDimensionLabel, getValueLabel,
} from '@/composables/useStudentClassification'

interface Props {
  filters: Record<string, string | undefined>
  activePreset?: string | null
  sortBy?: string
  /** 只显示指定维度 (默认全部4维) */
  visibleDimensions?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  activePreset: null,
  sortBy: 'priority',
  visibleDimensions: undefined,
})

defineEmits<{
  preset: [preset: typeof PRESETS[0]]
  filter: [dimension: string, value: string]
  sort: [value: string]
  clear: []
}>()

const presets = computed(() => PRESETS)

const dimensions = computed(() => {
  if (props.visibleDimensions) {
    return DIMENSIONS.filter(d => props.visibleDimensions!.includes(d.key))
  }
  return DIMENSIONS
})

function hasFilter(key: string): boolean {
  return !!props.filters[key]
}

const activeFilterCount = computed(() => {
  return Object.values(props.filters).filter(v => v).length
})

const activeFilters = computed(() => {
  const result: Record<string, string> = {}
  for (const [k, v] of Object.entries(props.filters)) {
    if (v && k !== 'sort_by') result[k] = v
  }
  return result
})
</script>

<style scoped>
.classification-filter-bar {
  margin-bottom: 16px;
}

.preset-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.dimension-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
}

@media (max-width: 640px) {
  .dimension-chips {
    gap: 6px;
  }
  .dimension-chips .ant-select {
    width: 100% !important;
  }
}
</style>
