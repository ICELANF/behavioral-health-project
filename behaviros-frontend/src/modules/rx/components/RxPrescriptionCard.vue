<!--
  RxPrescriptionCard.vue — 行为处方卡片
  ========================================
  展示完整处方: 策略、强度、微行动、Agent来源
-->

<template>
  <div class="rx-card" :class="{ expanded }">
    <!-- 卡片头部 -->
    <div class="rx-header" @click="expanded = !expanded">
      <div class="rx-header-left">
        <span class="agent-badge" :style="{ background: agentInfo.color }">
          {{ agentInfo.icon }}
        </span>
        <div class="rx-header-text">
          <h4 class="rx-title">行为处方 #{{ rx.rx_id?.slice(-6) }}</h4>
          <span class="rx-time">{{ fmt.formatDate(rx.created_at) }}</span>
        </div>
      </div>
      <div class="rx-header-right">
        <a-tag :color="intensityInfo.color" class="intensity-tag">
          {{ intensityInfo.label }}强度
        </a-tag>
        <span class="confidence" :style="{ color: confidenceInfo.color }">
          ⬤ {{ Math.round(rx.confidence_score * 100) }}%
        </span>
        <down-outlined
          class="expand-icon"
          :class="{ rotated: expanded }"
        />
      </div>
    </div>

    <!-- 核心处方 -->
    <div class="rx-body">
      <!-- 策略区 -->
      <div class="rx-section">
        <div class="section-label">主策略</div>
        <div class="strategy-primary">
          <thunderbolt-outlined class="strategy-icon" />
          <span>{{ fmt.formatStrategy(rx.primary_strategy) }}</span>
        </div>
        <div class="strategy-secondary" v-if="rx.secondary_strategies?.length">
          <span
            v-for="s in rx.secondary_strategies"
            :key="s"
            class="sub-strategy"
          >
            {{ fmt.formatStrategy(s) }}
          </span>
        </div>
      </div>

      <!-- 沟通风格 -->
      <div class="rx-section">
        <div class="section-label">沟通风格</div>
        <div class="comm-style">
          {{ communicationLabel }}
        </div>
      </div>

      <!-- 推理依据 -->
      <div class="rx-section" v-if="rx.reasoning">
        <div class="section-label">决策推理</div>
        <div class="reasoning-text">{{ rx.reasoning }}</div>
      </div>
    </div>

    <!-- 展开: 微行动 + 禁忌 -->
    <div class="rx-expanded" v-if="expanded">
      <!-- 微行动列表 -->
      <div class="rx-section" v-if="rx.micro_actions?.length">
        <div class="section-label">
          <experiment-outlined /> 微行动 ({{ rx.micro_actions.length }})
        </div>
        <div class="micro-actions">
          <div
            v-for="action in rx.micro_actions"
            :key="action.action_id"
            class="micro-action"
          >
            <div class="action-head">
              <span class="action-title">{{ action.title }}</span>
              <a-tag size="small" color="blue">
                {{ fmt.formatDuration(action.duration_minutes) }}
              </a-tag>
            </div>
            <div class="action-desc">{{ action.description }}</div>
            <div class="action-meta">
              <span v-if="action.frequency">📅 {{ action.frequency }}</span>
              <span v-if="action.trigger_cue">🔔 {{ action.trigger_cue }}</span>
              <span v-if="action.reward_suggestion">🎁 {{ action.reward_suggestion }}</span>
            </div>
            <a-progress
              :percent="Math.round(action.difficulty * 100)"
              size="small"
              :stroke-color="action.difficulty > 0.7 ? '#f5222d' : action.difficulty > 0.4 ? '#faad14' : '#52c41a'"
              format="难度"
              class="action-difficulty"
            />
          </div>
        </div>
      </div>

      <!-- 禁忌症 -->
      <div class="rx-section" v-if="rx.contraindications?.length">
        <div class="section-label">
          <warning-outlined style="color: #fa541c" /> 禁忌提示
        </div>
        <div class="contraindications">
          <span v-for="c in rx.contraindications" :key="c" class="contra-item">
            {{ c }}
          </span>
        </div>
      </div>

      <!-- 协作Agent -->
      <div class="rx-section" v-if="rx.collaboration_agents?.length">
        <div class="section-label">参与协作的Agent</div>
        <div class="collab-agents">
          <span
            v-for="agent in rx.collaboration_agents"
            :key="agent"
            class="collab-badge"
            :style="{ borderColor: fmt.formatAgent(agent).color }"
          >
            {{ fmt.formatAgent(agent).icon }} {{ fmt.formatAgent(agent).name }}
          </span>
        </div>
      </div>

      <!-- 复查提醒 -->
      <div class="rx-review" v-if="rx.review_in_days">
        <calendar-outlined />
        建议 {{ rx.review_in_days }} 天后复查
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  DownOutlined,
  ThunderboltOutlined,
  ExperimentOutlined,
  WarningOutlined,
  CalendarOutlined,
} from '@ant-design/icons-vue'
import type { RxPrescriptionDTO } from '../types/rx'
import { CommunicationStyle, AGENT_LABELS, ExpertAgentType } from '../types/rx'
import { useRxFormatter } from '../composables/useRx'

interface Props {
  rx: RxPrescriptionDTO
  defaultExpanded?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  defaultExpanded: false,
})

const expanded = ref(props.defaultExpanded)
const fmt = useRxFormatter()

const agentInfo = computed(() => {
  const agent = props.rx.computed_by || ExpertAgentType.BEHAVIOR_COACH
  return AGENT_LABELS[agent] || { name: '未知', icon: '🤖', color: '#999' }
})

const intensityInfo = computed(() => fmt.formatIntensity(props.rx.intensity))
const confidenceInfo = computed(() => fmt.formatConfidence(props.rx.confidence_score))

const COMM_LABELS: Record<string, string> = {
  [CommunicationStyle.EMPATHETIC]: '🤝 共情式',
  [CommunicationStyle.DATA_DRIVEN]: '📊 数据驱动',
  [CommunicationStyle.EXPLORATORY]: '🔍 探索式',
  [CommunicationStyle.SOCIAL_PROOF]: '👥 社会认同',
  [CommunicationStyle.CHALLENGE]: '🏆 挑战式',
  [CommunicationStyle.NEUTRAL]: '📝 中性',
}

const communicationLabel = computed(() => {
  return COMM_LABELS[props.rx.communication_style] || props.rx.communication_style
})
</script>

<style scoped>
.rx-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  overflow: hidden;
  transition: box-shadow 0.3s;
}

.rx-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.rx-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  cursor: pointer;
  user-select: none;
}

.rx-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.agent-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.rx-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.rx-time {
  font-size: 12px;
  color: #999;
}

.rx-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.confidence {
  font-size: 12px;
  font-weight: 500;
}

.expand-icon {
  transition: transform 0.3s;
  font-size: 12px;
  color: #999;
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

.rx-body {
  padding: 0 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rx-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-label {
  font-size: 12px;
  color: #999;
  display: flex;
  align-items: center;
  gap: 4px;
}

.strategy-primary {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  color: #1890ff;
}

.strategy-icon {
  color: #faad14;
}

.strategy-secondary {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.sub-strategy {
  padding: 2px 8px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.comm-style {
  font-size: 14px;
  color: #333;
}

.reasoning-text {
  font-size: 13px;
  color: #555;
  line-height: 1.5;
  padding: 8px 10px;
  background: #fafafa;
  border-radius: 6px;
}

/* 展开区域 */
.rx-expanded {
  padding: 0 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  border-top: 1px solid #f0f0f0;
  padding-top: 14px;
}

.micro-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.micro-action {
  padding: 10px 12px;
  background: #fafafa;
  border-radius: 8px;
  border-left: 3px solid #1890ff;
}

.action-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.action-desc {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
  line-height: 1.4;
}

.action-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 6px;
  font-size: 11px;
  color: #888;
}

.action-difficulty {
  margin-top: 6px;
}

.contraindications {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.contra-item {
  padding: 6px 10px;
  background: #fff2e8;
  border-radius: 4px;
  font-size: 12px;
  color: #d4380d;
}

.collab-agents {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.collab-badge {
  padding: 4px 10px;
  border: 1.5px solid;
  border-radius: 16px;
  font-size: 12px;
}

.rx-review {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #e6f7ff;
  border-radius: 6px;
  font-size: 13px;
  color: #0050b3;
}
</style>
