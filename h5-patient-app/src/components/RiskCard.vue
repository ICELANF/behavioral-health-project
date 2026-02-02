<script setup lang="ts">
/**
 * 风险卡片组件
 * 用于显示风险等级和分数
 */
import { computed } from 'vue'
import { useAssessmentStore } from '@/stores/assessment'

interface Props {
  riskLevel: 'R0' | 'R1' | 'R2' | 'R3' | 'R4'
  riskScore: number
}

const props = defineProps<Props>()
const assessmentStore = useAssessmentStore()

const levelText = computed(() => assessmentStore.getRiskLevelText(props.riskLevel))
const levelColor = computed(() => assessmentStore.getRiskLevelColor(props.riskLevel))
</script>

<template>
  <div class="risk-card">
    <div class="risk-level-badge" :style="{ backgroundColor: levelColor }">
      {{ levelText }}
    </div>
    <div class="risk-score">
      <div class="score-value">{{ riskScore.toFixed(1) }}</div>
      <div class="score-label">风险分数</div>
    </div>
  </div>
</template>

<style scoped>
.risk-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}

.risk-level-badge {
  padding: 8px 16px;
  border-radius: 8px;
  color: white;
  font-size: 16px;
  font-weight: bold;
  white-space: nowrap;
}

.risk-score {
  flex: 1;
  text-align: center;
}

.score-value {
  font-size: 32px;
  font-weight: bold;
  color: #323233;
}

.score-label {
  font-size: 12px;
  color: #969799;
  margin-top: 4px;
}
</style>
