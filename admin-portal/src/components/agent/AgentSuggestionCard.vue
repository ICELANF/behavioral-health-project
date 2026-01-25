<template>
  <a-card class="agent-suggestion-card" :class="{ 'has-alerts': hasAlerts }">
    <template #title>
      <div class="card-header">
        <RobotOutlined class="agent-icon" />
        <span>Agent 建议</span>
        <a-badge v-if="pendingCount > 0" :count="pendingCount" class="pending-badge" />
      </div>
    </template>
    <template #extra>
      <a-button type="link" size="small" @click="refresh">
        <ReloadOutlined /> 刷新
      </a-button>
    </template>

    <a-spin :spinning="loading">
      <div v-if="suggestions.length === 0" class="empty-state">
        <SmileOutlined style="font-size: 32px; color: #bfbfbf" />
        <p>暂无新建议</p>
      </div>

      <div v-else class="suggestions-list">
        <div
          v-for="suggestion in suggestions"
          :key="suggestion.id"
          class="suggestion-item"
          :class="getSuggestionClass(suggestion)"
        >
          <div class="suggestion-header">
            <a-tag :color="getTypeColor(suggestion.type)">{{ getTypeLabel(suggestion.type) }}</a-tag>
            <span class="priority">优先级: {{ suggestion.priority }}</span>
            <span v-if="suggestion.confidence" class="confidence">
              置信度: {{ Math.round(suggestion.confidence * 100) }}%
            </span>
          </div>

          <div class="suggestion-content">
            <p class="suggestion-text">{{ suggestion.text }}</p>
            <p v-if="suggestion.rationale" class="suggestion-rationale">
              <InfoCircleOutlined /> {{ suggestion.rationale }}
            </p>
          </div>

          <div class="suggestion-actions">
            <a-button type="primary" size="small" @click="handleAccept(suggestion)">
              <CheckOutlined /> 采纳
            </a-button>
            <a-button size="small" @click="handleModify(suggestion)">
              <EditOutlined /> 修改
            </a-button>
            <a-button size="small" danger @click="handleReject(suggestion)">
              <CloseOutlined /> 拒绝
            </a-button>
          </div>
        </div>
      </div>

      <!-- 风险标记 -->
      <div v-if="riskFlags.length > 0" class="risk-section">
        <a-divider>风险提示</a-divider>
        <a-alert
          v-for="flag in riskFlags"
          :key="flag"
          :message="getRiskLabel(flag)"
          type="warning"
          show-icon
          style="margin-bottom: 8px"
        />
      </div>

      <!-- 反馈给模型按钮 -->
      <div class="feedback-section">
        <a-button block @click="showFeedbackModal = true">
          <MessageOutlined /> 反馈给模型
        </a-button>
      </div>
    </a-spin>

    <!-- 反馈弹窗 -->
    <a-modal
      v-model:open="showFeedbackModal"
      title="反馈给模型"
      @ok="submitFeedback"
    >
      <a-form layout="vertical">
        <a-form-item label="评分">
          <a-rate v-model:value="feedbackForm.rating" />
        </a-form-item>
        <a-form-item label="反馈内容">
          <a-textarea
            v-model:value="feedbackForm.comment"
            placeholder="请描述建议的问题或改进意见..."
            :rows="4"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </a-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  RobotOutlined,
  ReloadOutlined,
  SmileOutlined,
  CheckOutlined,
  EditOutlined,
  CloseOutlined,
  InfoCircleOutlined,
  MessageOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useAgentStore, type AgentSuggestion } from '@/stores/agent'

interface Props {
  taskId?: string
  suggestions?: AgentSuggestion[]
  riskFlags?: string[]
  confidence?: number
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  suggestions: () => [],
  riskFlags: () => [],
  loading: false
})

const emit = defineEmits<{
  (e: 'accept', suggestion: AgentSuggestion): void
  (e: 'reject', suggestion: AgentSuggestion): void
  (e: 'modify', suggestion: AgentSuggestion): void
  (e: 'refresh'): void
}>()

const agentStore = useAgentStore()

const showFeedbackModal = ref(false)
const feedbackForm = ref({
  rating: 0,
  comment: ''
})

const pendingCount = computed(() => agentStore.pendingCount)
const hasAlerts = computed(() =>
  props.riskFlags.length > 0 ||
  props.suggestions.some(s => s.priority >= 9)
)

const getTypeColor = (type: string): string => {
  const colors: Record<string, string> = {
    action: 'blue',
    task: 'green',
    alert: 'red',
    content: 'purple',
    resource: 'orange'
  }
  return colors[type] || 'default'
}

const getTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    action: '行动',
    task: '任务',
    alert: '预警',
    content: '内容',
    resource: '资源'
  }
  return labels[type] || type
}

const getSuggestionClass = (suggestion: AgentSuggestion): string => {
  if (suggestion.type === 'alert' || suggestion.priority >= 9) return 'urgent'
  if (suggestion.priority >= 7) return 'important'
  return ''
}

const getRiskLabel = (flag: string): string => {
  const labels: Record<string, string> = {
    high_glucose: '检测到高血糖',
    high_blood_pressure: '检测到高血压',
    abnormal_heart_rate: '心率异常',
    high_risk_user: '高风险用户'
  }
  return labels[flag] || flag
}

const handleAccept = (suggestion: AgentSuggestion) => {
  emit('accept', suggestion)
  message.success('已采纳建议')
}

const handleReject = (suggestion: AgentSuggestion) => {
  emit('reject', suggestion)
  message.info('已拒绝建议')
}

const handleModify = (suggestion: AgentSuggestion) => {
  emit('modify', suggestion)
}

const refresh = () => {
  emit('refresh')
}

const submitFeedback = async () => {
  if (props.taskId) {
    await agentStore.submitFeedback({
      task_id: props.taskId,
      reviewer_id: 'current-user', // 实际应从auth store获取
      reviewer_role: 'COACH',
      feedback_type: 'rate',
      rating: feedbackForm.value.rating,
      comment: feedbackForm.value.comment
    })
    message.success('反馈已提交')
  }
  showFeedbackModal.value = false
  feedbackForm.value = { rating: 0, comment: '' }
}
</script>

<style scoped>
.agent-suggestion-card {
  border-radius: 8px;
}

.agent-suggestion-card.has-alerts {
  border-color: #ff4d4f;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-icon {
  color: #1890ff;
  font-size: 18px;
}

.pending-badge {
  margin-left: 8px;
}

.empty-state {
  text-align: center;
  padding: 32px;
  color: #8c8c8c;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.suggestion-item {
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  background: #fafafa;
}

.suggestion-item.urgent {
  border-color: #ff4d4f;
  background: #fff2f0;
}

.suggestion-item.important {
  border-color: #faad14;
  background: #fffbe6;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.priority,
.confidence {
  font-size: 12px;
  color: #8c8c8c;
}

.suggestion-text {
  font-size: 14px;
  margin-bottom: 4px;
}

.suggestion-rationale {
  font-size: 12px;
  color: #8c8c8c;
}

.suggestion-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.risk-section {
  margin-top: 16px;
}

.feedback-section {
  margin-top: 16px;
}
</style>
