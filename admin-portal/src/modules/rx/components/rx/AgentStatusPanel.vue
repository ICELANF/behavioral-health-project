<!--
  AgentStatusPanel.vue — 4-Agent 状态监控面板
  =============================================
  实时显示 Agent 注册状态、活跃会话、处方统计
-->

<template>
  <div class="agent-panel">
    <div class="panel-header">
      <h3 class="panel-title">
        <robot-outlined /> Expert Agent 集群
      </h3>
      <div class="orchestrator-status">
        <span
          class="status-dot"
          :class="orchestratorClass"
        />
        编排器: {{ orchestratorLabel }}
      </div>
    </div>

    <!-- Agent 卡片网格 -->
    <div class="agent-grid" v-if="agents.length">
      <div
        v-for="agent in agents"
        :key="agent.agent_type"
        class="agent-card"
        :class="{ inactive: agent.status !== 'active' }"
        @click="$emit('select', agent)"
      >
        <div class="agent-icon" :style="{ background: getColor(agent.agent_type) }">
          {{ getIcon(agent.agent_type) }}
        </div>
        <div class="agent-info">
          <div class="agent-name">{{ agent.name }}</div>
          <div class="agent-stats">
            <span>
              <span class="stat-dot" :class="agent.status" />
              {{ statusLabel(agent.status) }}
            </span>
            <span>{{ agent.active_sessions }} 会话</span>
          </div>
        </div>
        <div class="agent-metrics">
          <div class="metric-row">
            <span class="metric-key">总处方</span>
            <span class="metric-val">{{ agent.total_prescriptions }}</span>
          </div>
          <div class="metric-row">
            <span class="metric-key">平均置信度</span>
            <span
              class="metric-val"
              :style="{ color: confidenceColor(agent.avg_confidence) }"
            >
              {{ Math.round(agent.avg_confidence * 100) }}%
            </span>
          </div>
        </div>
        <div class="agent-caps">
          <a-tag
            v-for="cap in agent.capabilities.slice(0, 3)"
            :key="cap"
            size="small"
          >
            {{ cap }}
          </a-tag>
          <a-tag v-if="agent.capabilities.length > 3" size="small">
            +{{ agent.capabilities.length - 3 }}
          </a-tag>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <a-empty
      v-else-if="!loading"
      description="暂无注册Agent"
    />

    <!-- 加载 -->
    <div class="loading-state" v-if="loading">
      <a-spin />
      <span>获取 Agent 状态...</span>
    </div>

    <!-- 全局统计 -->
    <div class="global-stats" v-if="agents.length">
      <div class="g-stat">
        <span class="g-val">{{ agents.length }}</span>
        <span class="g-label">注册Agent</span>
      </div>
      <div class="g-stat">
        <span class="g-val">{{ totalSessions }}</span>
        <span class="g-label">活跃会话</span>
      </div>
      <div class="g-stat">
        <span class="g-val">{{ totalRx }}</span>
        <span class="g-label">总处方数</span>
      </div>
      <div class="g-stat">
        <span class="g-val" :style="{ color: confidenceColor(avgConf) }">
          {{ Math.round(avgConf * 100) }}%
        </span>
        <span class="g-label">平均置信度</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RobotOutlined } from '@ant-design/icons-vue'
import type { AgentStatusEntry, AgentStatusResponse } from '../../types/rx'
import { AGENT_LABELS, ExpertAgentType } from '../../types/rx'

interface Props {
  status: AgentStatusResponse | null
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

defineEmits(['select'])

const agents = computed<AgentStatusEntry[]>(() => props.status?.agents || [])

const orchestratorClass = computed(() => {
  const s = props.status?.orchestrator_status
  return s === 'ready' ? 'green' : s === 'degraded' ? 'yellow' : 'red'
})

const orchestratorLabel = computed(() => {
  const map: Record<string, string> = {
    ready: '就绪',
    degraded: '降级',
    down: '离线',
  }
  return map[props.status?.orchestrator_status || ''] || '未知'
})

const totalSessions = computed(() =>
  agents.value.reduce((s, a) => s + a.active_sessions, 0)
)

const totalRx = computed(() =>
  agents.value.reduce((s, a) => s + a.total_prescriptions, 0)
)

const avgConf = computed(() => {
  const active = agents.value.filter((a) => a.total_prescriptions > 0)
  if (!active.length) return 0
  return active.reduce((s, a) => s + a.avg_confidence, 0) / active.length
})

function getColor(type: string) {
  return AGENT_LABELS[type as ExpertAgentType]?.color || '#999'
}

function getIcon(type: string) {
  return AGENT_LABELS[type as ExpertAgentType]?.icon || '🤖'
}

function statusLabel(s: string) {
  return { active: '在线', inactive: '离线', error: '异常' }[s] || s
}

function confidenceColor(v: number) {
  if (v >= 0.8) return '#52c41a'
  if (v >= 0.6) return '#faad14'
  return '#f5222d'
}
</script>

<style scoped>
.agent-panel {
  background: #fff;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.orchestrator-status {
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.green  { background: #52c41a; box-shadow: 0 0 6px rgba(82, 196, 26, 0.4); }
.status-dot.yellow { background: #faad14; box-shadow: 0 0 6px rgba(250, 173, 20, 0.4); }
.status-dot.red    { background: #f5222d; box-shadow: 0 0 6px rgba(245, 34, 45, 0.4); }

.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.agent-card {
  padding: 14px;
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.agent-card:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.12);
}

.agent-card.inactive {
  opacity: 0.5;
}

.agent-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.agent-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.agent-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.agent-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #999;
}

.stat-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 3px;
  vertical-align: middle;
}

.stat-dot.active  { background: #52c41a; }
.stat-dot.inactive { background: #d9d9d9; }
.stat-dot.error   { background: #f5222d; }

.agent-metrics {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.metric-key { color: #999; }
.metric-val { font-weight: 500; color: #333; }

.agent-caps {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 24px;
  color: #999;
}

.global-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding-top: 14px;
  border-top: 1px solid #f0f0f0;
}

.g-stat {
  text-align: center;
}

.g-val {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #333;
}

.g-label {
  font-size: 11px;
  color: #999;
}
</style>
