<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAssessmentStore } from '@/stores/assessment'

const route = useRoute()
const router = useRouter()
const assessmentStore = useAssessmentStore()

const loading = ref(true)
const assessmentId = computed(() => route.params.id as string)

// 获取评估结果
const result = computed(() => assessmentStore.currentAssessment)

/**
 * 加载评估结果
 */
const loadResult = async () => {
  loading.value = true
  try {
    await assessmentStore.fetchResult(assessmentId.value)
  } catch (error) {
    console.error('Load result error:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 返回首页
 */
const goHome = () => {
  router.push('/')
}

/**
 * 继续评估
 */
const continueAssessment = () => {
  router.push('/data-input')
}

/**
 * 格式化时间
 */
const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

onMounted(() => {
  loadResult()
})
</script>

<template>
  <div class="result-page page-container">
    <van-nav-bar title="评估结果" left-arrow @click-left="goHome" />

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrapper">
      <van-loading size="24px">加载中...</van-loading>
    </div>

    <!-- 评估结果 -->
    <div v-else-if="result" class="content-wrapper">
      <!-- 风险等级卡片 -->
      <van-cell-group title="风险评估" inset>
        <van-cell>
          <div class="risk-card">
            <div
              class="risk-level-badge"
              :style="{
                backgroundColor: assessmentStore.getRiskLevelColor(result.risk_assessment.risk_level)
              }"
            >
              {{ assessmentStore.getRiskLevelText(result.risk_assessment.risk_level) }}
            </div>
            <div class="risk-score">
              <div class="score-value">{{ result.risk_assessment.risk_score.toFixed(1) }}</div>
              <div class="score-label">风险分数</div>
            </div>
          </div>
        </van-cell>

        <van-cell title="主要关注" :value="result.risk_assessment.primary_concern" />
        <van-cell title="紧急程度" :value="result.risk_assessment.urgency" />
        <van-cell title="评估时间" :value="formatTime(result.timestamp)" />
      </van-cell-group>

      <!-- Trigger列表 -->
      <van-cell-group title="识别的风险信号" inset>
        <template v-if="result.triggers.length > 0">
          <van-cell
            v-for="(trigger, index) in result.triggers"
            :key="index"
            :title="trigger.name"
          >
            <template #label>
              <div class="trigger-info">
                <van-tag :type="trigger.severity === 'critical' ? 'danger' : trigger.severity === 'high' ? 'warning' : 'primary'" size="medium">
                  {{ trigger.severity }}
                </van-tag>
                <span class="confidence">置信度: {{ (trigger.confidence * 100).toFixed(0) }}%</span>
              </div>
            </template>
          </van-cell>
        </template>
        <template v-else>
          <div class="empty-state">
            <div class="empty-state-text">未识别到风险信号</div>
          </div>
        </template>
      </van-cell-group>

      <!-- 路由决策 -->
      <van-cell-group title="专业建议" inset>
        <van-cell title="主要Agent" :value="result.routing_decision.primary_agent" />
        <van-cell
          v-if="result.routing_decision.secondary_agents.length > 0"
          title="辅助Agent"
          :value="result.routing_decision.secondary_agents.join(', ')"
        />
        <van-cell title="优先级" :value="`P${result.routing_decision.priority}`" />
        <van-cell title="建议响应时间" :value="result.routing_decision.response_time" />
      </van-cell-group>

      <!-- 推荐行动 -->
      <van-cell-group title="推荐行动" inset>
        <van-cell
          v-for="(action, index) in result.routing_decision.recommended_actions"
          :key="index"
          :title="`${index + 1}. ${action}`"
        />
      </van-cell-group>

      <!-- 评估理由 -->
      <van-cell-group title="评估说明" inset>
        <van-cell>
          <div class="reasoning-text">{{ result.risk_assessment.reasoning }}</div>
        </van-cell>
      </van-cell-group>

      <!-- 操作按钮 -->
      <div class="button-group">
        <van-button round block type="primary" @click="continueAssessment">
          继续评估
        </van-button>
        <van-button round block plain type="primary" @click="goHome">
          返回首页
        </van-button>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else class="empty-state">
      <div class="empty-state-icon">⚠️</div>
      <div class="empty-state-text">加载失败</div>
      <van-button type="primary" size="small" @click="loadResult" style="margin-top: 16px">
        重新加载
      </van-button>
    </div>
  </div>
</template>

<style scoped>
.result-page {
  min-height: 100vh;
}

.risk-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 0;
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

.trigger-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.confidence {
  font-size: 12px;
  color: #969799;
}

.reasoning-text {
  line-height: 1.6;
  color: #646566;
  padding: 8px 0;
}
</style>
