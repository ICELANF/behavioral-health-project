<!--
  RxDashboard.vue — 行为处方综合仪表盘
  ========================================
  集成所有处方组件: Agent状态、计算表单、处方历史、交接日志、策略库
  
  路由: /rx/dashboard
  权限: coach 及以上
-->

<template>
  <div class="rx-dashboard">
    <!-- 顶部统计栏 -->
    <div class="dash-stats">
      <a-statistic title="活跃 Agent" :value="store.activeAgents.length" class="stat-item">
        <template #prefix><robot-outlined /></template>
        <template #suffix>/ {{ store.agentStatus?.agents.length || 0 }}</template>
      </a-statistic>
      <a-statistic title="总处方数" :value="store.totalPrescriptions" class="stat-item">
        <template #prefix><medicine-box-outlined /></template>
      </a-statistic>
      <a-statistic
        title="平均置信度"
        :value="Math.round(store.avgConfidence * 100)"
        suffix="%"
        class="stat-item"
        :value-style="{ color: store.avgConfidence >= 0.7 ? '#52c41a' : '#faad14' }"
      >
        <template #prefix><check-circle-outlined /></template>
      </a-statistic>
      <a-statistic title="待处理交接" :value="store.pendingHandoffs.length" class="stat-item">
        <template #prefix><swap-outlined /></template>
      </a-statistic>
    </div>

    <!-- 主布局: 左侧面板 + 右侧内容 -->
    <div class="dash-layout">
      <!-- 左侧: 计算面板 -->
      <div class="dash-left">
        <RxComputeForm :user-id="currentUserId" @computed="onRxComputed" />
      </div>

      <!-- 右侧: Tab 内容 -->
      <div class="dash-right">
        <a-tabs v-model:activeKey="activeTab" type="card">
          <!-- Tab 1: 当前处方 -->
          <a-tab-pane key="current" tab="当前处方">
            <div class="tab-content" v-if="store.currentRx">
              <RxPrescriptionCard
                :rx="store.currentRx"
                :default-expanded="true"
              />

              <!-- 计算元数据 -->
              <div class="compute-meta" v-if="store.computeResult">
                <a-descriptions size="small" :column="3" bordered>
                  <a-descriptions-item label="使用 Agent">
                    {{ fmt.formatAgent(store.computeResult.agent_used).icon }}
                    {{ fmt.formatAgent(store.computeResult.agent_used).name }}
                  </a-descriptions-item>
                  <a-descriptions-item label="计算耗时">
                    {{ Math.round(store.computeResult.computation_time_ms) }}ms
                  </a-descriptions-item>
                  <a-descriptions-item label="警告数">
                    {{ store.computeResult.warnings?.length || 0 }}
                  </a-descriptions-item>
                </a-descriptions>

                <a-alert
                  v-for="(warn, idx) in store.computeResult.warnings"
                  :key="idx"
                  :message="warn"
                  type="warning"
                  show-icon
                  class="warning-alert"
                />
              </div>
            </div>

            <a-empty v-else description="尚未计算处方，请在左侧填写上下文后生成" />
          </a-tab-pane>

          <!-- Tab 2: 处方历史 -->
          <a-tab-pane key="history" tab="处方历史">
            <div class="history-controls">
              <a-input-search
                v-model:value="historyUserId"
                placeholder="输入用户 ID"
                enter-button="查询"
                size="small"
                @search="loadHistory"
                style="width: 320px"
              />
            </div>

            <div class="history-list" v-if="store.rxHistory.length">
              <RxPrescriptionCard
                v-for="rx in store.rxHistory"
                :key="rx.rx_id"
                :rx="rx"
              />
              <a-pagination
                v-model:current="historyPage"
                :total="store.rxHistoryTotal"
                :page-size="20"
                size="small"
                show-quick-jumper
                @change="onHistoryPageChange"
                class="history-pagination"
              />
            </div>

            <a-empty v-else-if="!store.loading.history" description="暂无处方历史" />
            <a-spin v-if="store.loading.history" class="loading-spin" />
          </a-tab-pane>

          <!-- Tab 3: Agent 状态 -->
          <a-tab-pane key="agents" tab="Agent 集群">
            <AgentStatusPanel
              :status="store.agentStatus"
              :loading="store.loading.agents"
              @select="onAgentSelect"
            />
          </a-tab-pane>

          <!-- Tab 4: 交接日志 -->
          <a-tab-pane key="handoffs" tab="交接日志">
            <div class="handoff-controls">
              <a-input-search
                v-model:value="handoffUserId"
                placeholder="输入用户 ID"
                enter-button="查询"
                size="small"
                @search="loadHandoffs"
                style="width: 320px"
              />
            </div>
            <HandoffLogTable
              :handoffs="store.handoffLog"
              :loading="store.loading.handoff"
            />
          </a-tab-pane>

          <!-- Tab 5: 策略库 -->
          <a-tab-pane key="strategies" tab="策略模板库">
            <StrategyGrid
              :strategies="store.strategies"
              :loading="store.loading.strategies"
              @select="onStrategySelect"
            />
          </a-tab-pane>

          <!-- Tab 6: 协作编排 -->
          <a-tab-pane key="collaborate" tab="协作编排">
            <div class="collab-section">
              <a-card title="多 Agent 协作测试" size="small">
                <a-form layout="inline">
                  <a-form-item label="用户 ID">
                    <a-input v-model:value="collabUserId" size="small" style="width: 200px" />
                  </a-form-item>
                  <a-form-item label="消息">
                    <a-input v-model:value="collabMessage" size="small" style="width: 280px" />
                  </a-form-item>
                  <a-form-item>
                    <a-button
                      type="primary"
                      size="small"
                      :loading="store.loading.collaborate"
                      @click="runCollaboration"
                    >
                      <thunderbolt-outlined /> 执行协作
                    </a-button>
                  </a-form-item>
                </a-form>
              </a-card>

              <!-- 协作结果 -->
              <div class="collab-result" v-if="store.lastCollaboration">
                <a-descriptions bordered size="small" :column="2" title="协作结果">
                  <a-descriptions-item label="触发场景">
                    {{ store.lastCollaboration.scenario }}
                  </a-descriptions-item>
                  <a-descriptions-item label="执行耗时">
                    {{ Math.round(store.lastCollaboration.execution_time_ms) }}ms
                  </a-descriptions-item>
                  <a-descriptions-item label="参与 Agent" :span="2">
                    <a-tag
                      v-for="a in store.lastCollaboration.agents_involved"
                      :key="a"
                      :color="fmt.formatAgent(a).color"
                    >
                      {{ fmt.formatAgent(a).icon }} {{ fmt.formatAgent(a).name }}
                    </a-tag>
                  </a-descriptions-item>
                </a-descriptions>

                <RxPrescriptionCard
                  v-if="store.lastCollaboration.combined_prescription"
                  :rx="store.lastCollaboration.combined_prescription"
                  :default-expanded="true"
                  class="collab-rx"
                />

                <!-- 冲突解决 -->
                <a-card
                  v-if="store.lastCollaboration.conflict_resolution"
                  title="冲突解决"
                  size="small"
                  class="conflict-card"
                >
                  <pre class="conflict-json">{{ JSON.stringify(store.lastCollaboration.conflict_resolution, null, 2) }}</pre>
                </a-card>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>

    <!-- 错误通知 -->
    <a-alert
      v-if="store.error"
      :message="store.error.message"
      type="error"
      closable
      show-icon
      class="error-banner"
      @close="store.error = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  RobotOutlined,
  MedicineBoxOutlined,
  CheckCircleOutlined,
  SwapOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useRxStore } from '../stores/rxStore'
import { useAgentPolling, useRxFormatter } from '../composables/useRx'
import {
  RxComputeForm,
  RxPrescriptionCard,
  AgentStatusPanel,
  HandoffLogTable,
  StrategyGrid,
} from '../components/rx'
import type { ComputeRxResponse, StrategyTemplate, AgentStatusEntry } from '../types/rx'

const store = useRxStore()
const fmt = useRxFormatter()

// 启动 Agent 状态轮询
useAgentPolling(30000)

// Tab 状态
const activeTab = ref('current')

// 当前操作用户 (从路由或 props 获取, 这里示例用固定值)
const currentUserId = ref('00000000-0000-0000-0000-000000000001')

// 历史查询
const historyUserId = ref('')
const historyPage = ref(1)

// 交接查询
const handoffUserId = ref('')

// 协作测试
const collabUserId = ref('')
const collabMessage = ref('')

// 事件处理
function onRxComputed(result: ComputeRxResponse) {
  activeTab.value = 'current'
}

function onAgentSelect(agent: AgentStatusEntry) {
  activeTab.value = 'agents'
  message.success(`已选择 ${agent.name} Agent`)
}

function onStrategySelect(strategy: StrategyTemplate) {
  activeTab.value = 'strategies'
  message.success(`已选择策略: ${strategy.name_zh}`)
}

async function loadHistory() {
  if (!historyUserId.value) return
  historyPage.value = 1
  await store.fetchHistory(historyUserId.value, 1, 20)
}

function onHistoryPageChange(page: number) {
  historyPage.value = page
  store.fetchHistory(historyUserId.value, page, 20)
}

async function loadHandoffs() {
  if (!handoffUserId.value) return
  await store.fetchHandoffLog(handoffUserId.value)
}

async function runCollaboration() {
  if (!collabUserId.value) {
    message.warning('请输入用户 ID')
    return
  }
  try {
    await store.executeCollaboration(collabUserId.value, {
      message: collabMessage.value || '你好，我想了解饮食建议',
    })
    message.success('协作编排完成')
  } catch (e: any) {
    message.error(e.message || '协作执行失败')
  }
}

// 初始化
onMounted(async () => {
  await store.fetchStrategies()
})
</script>

<style scoped>
.rx-dashboard {
  padding: 20px;
  min-height: 100vh;
  background: #f5f6f8;
}

.dash-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-item {
  background: #fff;
  padding: 16px 20px;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.dash-layout {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 20px;
  align-items: start;
}

.dash-left {
  position: sticky;
  top: 20px;
}

.dash-right {
  min-width: 0;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.compute-meta {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.warning-alert {
  font-size: 13px;
}

.history-controls,
.handoff-controls {
  margin-bottom: 14px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-pagination {
  margin-top: 12px;
  text-align: center;
}

.loading-spin {
  display: flex;
  justify-content: center;
  padding: 32px;
}

.collab-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.collab-result {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.collab-rx {
  margin-top: 8px;
}

.conflict-card {
  margin-top: 8px;
}

.conflict-json {
  font-size: 12px;
  background: #f5f5f5;
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0;
}

.error-banner {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  max-width: 500px;
  z-index: 1000;
}

/* 响应式 */
@media (max-width: 960px) {
  .dash-layout {
    grid-template-columns: 1fr;
  }

  .dash-left {
    position: static;
  }

  .dash-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
