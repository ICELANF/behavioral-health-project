<template>
  <DualSignPanel :audit-case="demoCase" />
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import DualSignPanel from './DualSignPanel.vue'

const demoCase = reactive({
  id: 'CASE-2026-0216-001',
  patientId: 'PAT-10042',
  rawMetrics: {
    riskLevel: 'MEDIUM',
    bigFive: { N: 68, E: 42, O: 55, A: 71, C: 38 },
    phq9: '12',
    cgmCV: 42,
    cgmTrend: '高波动',
  },
  bapsProfile: {
    stage: 'preparation',
    readiness: 0.62,
    selfEfficacy: 0.45,
    socialSupport: 0.71,
    barriers: ['irregular_schedule', 'emotional_eating', 'low_motivation'],
    strengths: ['family_support', 'health_awareness'],
  },
  originalL5Output:
    '患者 PHQ-9 得分 12（中度抑郁），CGM 变异系数 42%（高波动），' +
    '建议启动 SSRI 联合认知行为干预方案，同时调整胰岛素基础量 +2U，' +
    '增加餐前速效比例。注意低血糖风险评估。',
  narrativeL6Preview:
    '您最近在血糖管理上已经取得了进步，我们注意到有些波动可能和情绪、作息有关。' +
    '教练建议您这周尝试一个简单的 "餐前 3 分钟深呼吸" 练习，' +
    '同时保持现有的饮食记录习惯。您的家人给了很好的支持，这是很珍贵的力量。' +
    '如果遇到困难，随时可以和 AI 助手聊聊。',
})
</script>
