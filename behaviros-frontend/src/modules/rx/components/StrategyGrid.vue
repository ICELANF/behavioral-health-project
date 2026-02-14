<!--
  StrategyGrid.vue — 12策略模板卡片网格
  ========================================
  显示策略适用阶段、人格亲和度、微行动模板
-->

<template>
  <div class="strategy-grid">
    <div class="grid-header">
      <h4>
        <appstore-outlined /> 策略模板库 ({{ strategies.length }})
      </h4>
      <a-segmented v-model:value="stageFilter" :options="stageFilterOptions" size="small" />
    </div>

    <div class="grid-body">
      <div
        v-for="strategy in filteredStrategies"
        :key="strategy.strategy_type"
        class="strategy-card"
        :class="{ selected: selectedType === strategy.strategy_type }"
        @click="$emit('select', strategy)"
      >
        <div class="card-top">
          <span class="strategy-name">{{ strategy.name_zh }}</span>
          <span class="strategy-en">{{ strategy.name_en }}</span>
        </div>

        <div class="card-desc">{{ strategy.description }}</div>

        <div class="card-stages">
          <span class="meta-label">适用阶段</span>
          <div class="stage-dots">
            <span
              v-for="s in 7"
              :key="s - 1"
              class="stage-dot"
              :class="{ active: strategy.applicable_stages.includes(s - 1) }"
              :title="'S' + (s - 1)"
            >
              {{ s - 1 }}
            </span>
          </div>
        </div>

        <div class="card-affinity" v-if="strategy.personality_affinity">
          <span class="meta-label">人格亲和</span>
          <div class="affinity-tags">
            <a-tag
              v-for="(desc, trait) in strategy.personality_affinity"
              :key="trait"
              size="small"
              :color="traitColor(trait as string)"
            >
              {{ trait }}: {{ desc }}
            </a-tag>
          </div>
        </div>

        <div class="card-actions" v-if="strategy.micro_action_templates?.length">
          <span class="meta-label">微行动模板 ({{ strategy.micro_action_templates.length }})</span>
        </div>
      </div>
    </div>

    <a-empty v-if="!filteredStrategies.length && !loading" description="当前阶段无匹配策略" />
    <div class="loading-state" v-if="loading">
      <a-spin size="small" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { AppstoreOutlined } from '@ant-design/icons-vue'
import type { StrategyTemplate, RxStrategyType } from '../types/rx'

interface Props {
  strategies: StrategyTemplate[]
  loading?: boolean
  selectedType?: RxStrategyType
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

defineEmits(['select'])

const stageFilter = ref<string>('all')

const stageFilterOptions = [
  { label: '全部', value: 'all' },
  { label: 'S0-S2 前期', value: 'early' },
  { label: 'S3-S4 行动', value: 'action' },
  { label: 'S5-S6 维持', value: 'maintain' },
]

const filteredStrategies = computed(() => {
  if (stageFilter.value === 'all') return props.strategies
  const ranges: Record<string, number[]> = {
    early: [0, 1, 2],
    action: [3, 4],
    maintain: [5, 6],
  }
  const allowed = ranges[stageFilter.value] || []
  return props.strategies.filter((s) =>
    s.applicable_stages.some((stage) => allowed.includes(stage))
  )
})

function traitColor(trait: string): string {
  const map: Record<string, string> = {
    O: 'blue', C: 'green', E: 'gold', A: 'purple', N: 'red',
  }
  return map[trait] || 'default'
}
</script>

<style scoped>
.strategy-grid {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.grid-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.grid-header h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.grid-body {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.strategy-card {
  padding: 14px;
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.strategy-card:hover {
  border-color: #40a9ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.strategy-card.selected {
  border-color: #1890ff;
  background: #e6f7ff;
}

.card-top {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.strategy-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.strategy-en {
  font-size: 11px;
  color: #999;
  text-transform: capitalize;
}

.card-desc {
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

.meta-label {
  font-size: 11px;
  color: #999;
  display: block;
  margin-bottom: 4px;
}

.stage-dots {
  display: flex;
  gap: 4px;
}

.stage-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  background: #f5f5f5;
  color: #ccc;
}

.stage-dot.active {
  background: #1890ff;
  color: #fff;
  font-weight: 600;
}

.affinity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.loading-state {
  text-align: center;
  padding: 16px;
}
</style>
