<script setup lang="ts">
// ============================================================
// ExpertHomeExample.vue - 专家首页使用示例
// 展示如何在Vue中集成React组件
// 位置: src/views/expert/ExpertHome.vue (替换原有文件)
// ============================================================

import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'

// 导入Vue包装器组件
import DualSignPanelVue from '@/components/vue-wrappers/DualSignPanelVue.vue'
import CGMChartVue from '@/components/vue-wrappers/CGMChartVue.vue'
import LogicFlowBridgeVue from '@/components/vue-wrappers/LogicFlowBridgeVue.vue'

// 导入类型
import type { AuditCase, DecisionRules, PublishResult, CGMDataPoint } from '@/types/react-components'

// 当前选中的标签页
const activeTab = ref<'audit' | 'trace' | 'brain'>('audit')

// 审核案例数据
const currentAuditCase = reactive<AuditCase>({
  id: 'tr_7721',
  patientId: 'PT-8821',
  rawMetrics: {
    phq9: 18,
    cgmTrend: '波动剧烈',
    riskLevel: 'R3'
  },
  originalL5Output: '检测到中重度抑郁倾向及餐后血糖控制不佳。建议立即启动抗抑郁筛查并限制碳水摄入。',
  narrativeL6Preview: '最近似乎感到身体有些沉重？没关系，这是身体在提醒我们需要一点小小的调整。试试看从一次深呼吸开始，慢慢找回节律。',
  status: 'pending',
  decisionRules: {
    trigger: 'PHQ9_DEPRESSION_CHECK',
    logic: 'IF phq9 >= 15 AND cgm_volatility > 3.9 THEN SET RISK = R3',
    octopus_clamp: 'LIMIT_TASKS = 1',
    narrative_override: 'CONVERT_TO_EMPATHY'
  },
  createdAt: new Date()
})

// 决策规则数据
const decisionRules = reactive<DecisionRules>({
  trigger: 'CGM_HIGH_VOLATILITY',
  logic: 'IF val > 10.0 AND trend == "UP" THEN SET RISK = R3',
  octopus_clamp: 'LIMIT_TASKS = 1',
  narrative_override: 'CONVERT_TO_EMPATHY'
})

// CGM数据
const cgmData = ref<CGMDataPoint[]>([
  { time: '08:00', value: 5.2, trend: 'stable' },
  { time: '09:00', value: 7.8, trend: 'up' },
  { time: '10:00', value: 11.2, trend: 'up' },
  { time: '11:00', value: 9.5, trend: 'down' },
  { time: '12:00', value: 6.8, trend: 'down' },
])

// 审核队列统计
const auditStats = reactive({
  pending: 12,
  approved: 45,
  rejected: 3
})

// 事件处理
const handlePublish = (result: PublishResult) => {
  if (result.success) {
    message.success(`发布成功! Trace ID: ${result.traceId}`)
    auditStats.pending--
    auditStats.approved++
  } else {
    message.error(`发布失败: ${result.error}`)
  }
}

const handleSignChange = (signs: { master: boolean; secondary: boolean }) => {
  console.log('签名状态变化:', signs)
}

const handleLineHover = (lineNumber: number | null) => {
  console.log('悬停行号:', lineNumber)
}

const handleCGMClick = (point: CGMDataPoint) => {
  message.info(`点击数据点: ${point.time} - ${point.value} mmol/L`)
}

// 加载更多审核案例
const loadMoreCases = async () => {
  // 模拟API调用
  message.loading('加载中...', 1)
}

onMounted(() => {
  console.log('专家首页已挂载')
})
</script>

<template>
  <div class="expert-home">
    <!-- 顶部导航栏 -->
    <header class="expert-header">
      <div class="header-left">
        <h1 class="page-title">专家工作台</h1>
        <span class="version-tag">v16.1.0</span>
      </div>
      <div class="header-tabs">
        <button 
          :class="['tab-btn', { active: activeTab === 'audit' }]"
          @click="activeTab = 'audit'"
        >
          待审队列 ({{ auditStats.pending }})
        </button>
        <button 
          :class="['tab-btn', { active: activeTab === 'trace' }]"
          @click="activeTab = 'trace'"
        >
          决策回溯
        </button>
        <button 
          :class="['tab-btn', { active: activeTab === 'brain' }]"
          @click="activeTab = 'brain'"
        >
          规则引擎
        </button>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="expert-main">
      <!-- 审核队列标签页 -->
      <template v-if="activeTab === 'audit'">
        <div class="audit-section">
          <!-- 统计卡片 -->
          <div class="stats-row">
            <div class="stat-card pending">
              <span class="stat-value">{{ auditStats.pending }}</span>
              <span class="stat-label">待审核</span>
            </div>
            <div class="stat-card approved">
              <span class="stat-value">{{ auditStats.approved }}</span>
              <span class="stat-label">已通过</span>
            </div>
            <div class="stat-card rejected">
              <span class="stat-value">{{ auditStats.rejected }}</span>
              <span class="stat-label">已驳回</span>
            </div>
          </div>

          <!-- 双签审批面板 (React组件) -->
          <div class="dual-sign-section">
            <h2 class="section-title">当前审核案例</h2>
            <DualSignPanelVue
              :audit-case="currentAuditCase"
              container-class="dual-sign-wrapper"
              @publish="handlePublish"
              @sign-change="handleSignChange"
              @mounted="() => console.log('DualSignPanel mounted')"
              @error="(e) => console.error('DualSignPanel error:', e)"
            />
          </div>

          <!-- CGM图表 (React组件) -->
          <div class="cgm-section">
            <h2 class="section-title">患者CGM数据</h2>
            <CGMChartVue
              :data="cgmData"
              :patient-id="currentAuditCase.patientId"
              :show-raw-data="true"
              :height="250"
              container-class="cgm-wrapper"
              @data-point-click="handleCGMClick"
            />
          </div>
        </div>
      </template>

      <!-- 决策回溯标签页 -->
      <template v-else-if="activeTab === 'trace'">
        <div class="trace-section">
          <h2 class="section-title">决策逻辑联动</h2>
          <p class="section-desc">
            鼠标悬停在右侧解释卡片上，左侧代码将自动高亮对应行
          </p>
          <LogicFlowBridgeVue
            :decision-rules="decisionRules"
            container-class="logic-bridge-wrapper"
            @line-hover="handleLineHover"
          />
        </div>
      </template>

      <!-- 规则引擎标签页 -->
      <template v-else-if="activeTab === 'brain'">
        <div class="brain-section">
          <div class="placeholder-card">
            <span class="placeholder-icon">🧠</span>
            <h3>规则引擎</h3>
            <p>规则引擎可视化编辑功能开发中...</p>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<style scoped>
.expert-home {
  min-height: 100vh;
  background: linear-gradient(to bottom right, #f1f5f9, #f8fafc, #f1f5f9);
}

.expert-header {
  height: 80px;
  background: linear-gradient(to right, #475569, #64748b, #475569);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  margin: 0;
}

.version-tag {
  font-size: 0.75rem;
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.header-tabs {
  display: flex;
  gap: 1rem;
}

.tab-btn {
  padding: 0.5rem 1rem;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: rgba(255, 255, 255, 0.9);
}

.tab-btn.active {
  color: #4ade80;
  font-weight: 600;
}

.expert-main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 1rem;
}

.section-desc {
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 1.5rem;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-card.pending { border-left: 4px solid #f59e0b; }
.stat-card.approved { border-left: 4px solid #22c55e; }
.stat-card.rejected { border-left: 4px solid #ef4444; }

.stat-value {
  display: block;
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 0.875rem;
  color: #64748b;
}

.dual-sign-section,
.cgm-section,
.trace-section,
.brain-section {
  margin-bottom: 2rem;
}

.dual-sign-wrapper {
  border-radius: 1.5rem;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.cgm-wrapper {
  background: linear-gradient(135deg, #475569, #334155);
  border-radius: 0.75rem;
  padding: 1rem;
}

.logic-bridge-wrapper {
  background: white;
  border-radius: 1rem;
  border: 1px solid #e2e8f0;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.placeholder-card {
  background: white;
  border-radius: 1rem;
  padding: 4rem;
  text-align: center;
  border: 2px dashed #e2e8f0;
}

.placeholder-icon {
  font-size: 4rem;
  display: block;
  margin-bottom: 1rem;
}

.placeholder-card h3 {
  font-size: 1.5rem;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.placeholder-card p {
  color: #64748b;
}
</style>
