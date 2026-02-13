<!--
  HandoffLogTable.vue — Agent 交接日志表
  =========================================
  显示 Agent 之间的交接历史, 含状态流转、优先级
-->

<template>
  <div class="handoff-table">
    <div class="table-header">
      <h4>
        <swap-outlined /> Agent 交接日志
      </h4>
      <a-badge :count="pendingCount" :overflow-count="99">
        <a-tag color="blue">{{ handoffs.length }} 条记录</a-tag>
      </a-badge>
    </div>

    <a-table
      :columns="columns"
      :data-source="handoffs"
      :loading="loading"
      :pagination="{ pageSize: 10, size: 'small' }"
      row-key="handoff_id"
      size="small"
      :scroll="{ x: 680 }"
    >
      <!-- 来源 Agent -->
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'source_agent'">
          <span class="agent-tag" :style="{ borderColor: getColor(record.source_agent) }">
            {{ getIcon(record.source_agent) }} {{ getName(record.source_agent) }}
          </span>
        </template>

        <!-- 方向箭头 -->
        <template v-if="column.key === 'direction'">
          <arrow-right-outlined class="direction-arrow" />
        </template>

        <!-- 目标 Agent -->
        <template v-if="column.key === 'target_agent'">
          <span class="agent-tag" :style="{ borderColor: getColor(record.target_agent) }">
            {{ getIcon(record.target_agent) }} {{ getName(record.target_agent) }}
          </span>
        </template>

        <!-- 交接类型 -->
        <template v-if="column.key === 'handoff_type'">
          <a-tag :color="typeColor(record.handoff_type)" size="small">
            {{ typeLabel(record.handoff_type) }}
          </a-tag>
        </template>

        <!-- 状态 -->
        <template v-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)" size="small">
            {{ statusLabel(record.status) }}
          </a-tag>
        </template>

        <!-- 优先级 -->
        <template v-if="column.key === 'priority'">
          <span :class="'priority-' + record.priority">
            {{ '●'.repeat(record.priority) }}
          </span>
        </template>

        <!-- 时间 -->
        <template v-if="column.key === 'created_at'">
          <span class="time-text">{{ formatTime(record.created_at) }}</span>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { SwapOutlined, ArrowRightOutlined } from '@ant-design/icons-vue'
import type { HandoffLogEntry } from '../../types/rx'
import { AGENT_LABELS, ExpertAgentType } from '../../types/rx'

interface Props {
  handoffs: HandoffLogEntry[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

const pendingCount = computed(() =>
  props.handoffs.filter((h) => h.status === 'initiated' || h.status === 'in_progress').length
)

const columns = [
  { title: '来源', key: 'source_agent', width: 130 },
  { title: '', key: 'direction', width: 40, align: 'center' as const },
  { title: '目标', key: 'target_agent', width: 130 },
  { title: '类型', key: 'handoff_type', width: 100 },
  { title: '状态', key: 'status', width: 80 },
  { title: '优先级', key: 'priority', width: 70, align: 'center' as const },
  { title: '原因', dataIndex: 'reason', key: 'reason', ellipsis: true },
  { title: '时间', key: 'created_at', width: 140 },
]

function getColor(type: string) {
  return AGENT_LABELS[type as ExpertAgentType]?.color || '#999'
}

function getIcon(type: string) {
  return AGENT_LABELS[type as ExpertAgentType]?.icon || '🤖'
}

function getName(type: string) {
  return AGENT_LABELS[type as ExpertAgentType]?.name || type
}

function typeLabel(t: string): string {
  const map: Record<string, string> = {
    stage_promotion: '阶段晋升',
    stage_regression: '阶段回退',
    domain_coordination: '领域协调',
    cross_cutting: '交叉处理',
    emergency_takeover: '紧急接管',
    scheduled_handoff: '计划交接',
  }
  return map[t] || t
}

function typeColor(t: string): string {
  const map: Record<string, string> = {
    stage_promotion: 'green',
    stage_regression: 'orange',
    domain_coordination: 'blue',
    cross_cutting: 'purple',
    emergency_takeover: 'red',
    scheduled_handoff: 'cyan',
  }
  return map[t] || 'default'
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    initiated: '已发起',
    accepted: '已接受',
    in_progress: '进行中',
    completed: '已完成',
    rejected: '已拒绝',
    cancelled: '已取消',
  }
  return map[s] || s
}

function statusColor(s: string): string {
  const map: Record<string, string> = {
    initiated: 'processing',
    accepted: 'blue',
    in_progress: 'orange',
    completed: 'green',
    rejected: 'red',
    cancelled: 'default',
  }
  return map[s] || 'default'
}

function formatTime(t: string): string {
  return new Date(t).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.handoff-table {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.table-header h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.agent-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border: 1.5px solid;
  border-radius: 12px;
  font-size: 12px;
}

.direction-arrow {
  color: #ccc;
}

.priority-1 { color: #52c41a; }
.priority-2 { color: #faad14; }
.priority-3 { color: #fa541c; }
.priority-4 { color: #f5222d; }
.priority-5 { color: #cf1322; font-weight: 700; }

.time-text {
  font-size: 12px;
  color: #999;
}
</style>
