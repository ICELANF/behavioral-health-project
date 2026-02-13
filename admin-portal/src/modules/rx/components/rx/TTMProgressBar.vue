<!--
  TTMProgressBar.vue — TTM阶段进度可视化
  ==========================================
  水平阶段条 + 当前定位 + 就绪度/稳定度指示
-->

<template>
  <div class="ttm-progress">
    <div class="ttm-header">
      <span class="ttm-title">TTM 行为改变阶段</span>
      <a-tag :color="currentStage.color">{{ currentStage.label }}</a-tag>
    </div>

    <!-- 阶段进度条 -->
    <div class="ttm-track">
      <div
        v-for="(stage, idx) in stages"
        :key="idx"
        class="ttm-step"
        :class="{
          active: idx === modelValue,
          completed: idx < modelValue,
          clickable: interactive,
        }"
        @click="interactive && $emit('update:modelValue', idx)"
      >
        <div class="step-dot" :style="{ background: idx <= modelValue ? stage.color : '#e8e8e8' }">
          <check-outlined v-if="idx < modelValue" class="step-icon" />
          <span v-else class="step-number">{{ idx }}</span>
        </div>
        <span class="step-label" :class="{ highlight: idx === modelValue }">
          {{ stage.label }}
        </span>
      </div>
      <!-- 连线 -->
      <div class="ttm-line">
        <div
          class="ttm-line-fill"
          :style="{ width: `${(modelValue / 6) * 100}%` }"
        />
      </div>
    </div>

    <!-- 就绪度 & 稳定度 -->
    <div class="ttm-metrics" v-if="showMetrics">
      <div class="metric">
        <span class="metric-label">阶段就绪度</span>
        <a-progress
          :percent="Math.round(readiness * 100)"
          :stroke-color="readiness > 0.7 ? '#52c41a' : readiness > 0.4 ? '#faad14' : '#f5222d'"
          size="small"
          :show-info="true"
        />
      </div>
      <div class="metric">
        <span class="metric-label">阶段稳定度</span>
        <a-progress
          :percent="Math.round(stability * 100)"
          :stroke-color="stability > 0.7 ? '#52c41a' : stability > 0.4 ? '#faad14' : '#f5222d'"
          size="small"
          :show-info="true"
        />
      </div>
    </div>

    <!-- 阶段描述 -->
    <div class="ttm-desc" v-if="showDescription">
      {{ currentStage.description }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CheckOutlined } from '@ant-design/icons-vue'
import { TTM_STAGES } from '../../types/rx'

interface Props {
  modelValue: number      // TTM stage 0-6
  readiness?: number      // 0-1
  stability?: number      // 0-1
  showMetrics?: boolean
  showDescription?: boolean
  interactive?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readiness: 0.5,
  stability: 0.5,
  showMetrics: true,
  showDescription: true,
  interactive: false,
})

defineEmits(['update:modelValue'])

const stages = Object.values(TTM_STAGES)

const currentStage = computed(() => TTM_STAGES[props.modelValue] || TTM_STAGES[0])
</script>

<style scoped>
.ttm-progress {
  padding: 16px;
  background: #fafafa;
  border-radius: 10px;
}

.ttm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.ttm-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.ttm-track {
  position: relative;
  display: flex;
  justify-content: space-between;
  padding: 0 4px;
  margin-bottom: 16px;
}

.ttm-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  z-index: 1;
  cursor: default;
}

.ttm-step.clickable {
  cursor: pointer;
}

.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.ttm-step.active .step-dot {
  transform: scale(1.2);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.4);
}

.step-icon {
  font-size: 13px;
}

.step-number {
  font-size: 11px;
}

.step-label {
  font-size: 11px;
  color: #999;
  white-space: nowrap;
  transition: all 0.2s;
}

.step-label.highlight {
  color: #333;
  font-weight: 600;
}

.ttm-line {
  position: absolute;
  top: 14px;
  left: 18px;
  right: 18px;
  height: 2px;
  background: #e8e8e8;
  z-index: 0;
}

.ttm-line-fill {
  height: 100%;
  background: linear-gradient(90deg, #52c41a, #1890ff);
  transition: width 0.5s ease;
  border-radius: 1px;
}

.ttm-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 12px;
  color: #666;
}

.ttm-desc {
  margin-top: 12px;
  padding: 10px 12px;
  background: #fff;
  border-radius: 6px;
  font-size: 13px;
  color: #666;
  border-left: 3px solid v-bind('currentStage.color');
}
</style>
