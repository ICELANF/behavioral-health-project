<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAssessmentStore } from '@/stores/assessment'

const router = useRouter()
const userStore = useUserStore()
const assessmentStore = useAssessmentStore()

const loading = ref(false)
const activeTab = ref(0)

// 统计数据
const stats = computed(() => {
  const history = assessmentStore.history

  if (history.length === 0) {
    return {
      totalCount: 0,
      avgScore: 0,
      riskDistribution: {} as Record<string, number>,
      recentTrend: 'stable' as 'improving' | 'stable' | 'worsening'
    }
  }

  // 计算总评估次数
  const totalCount = history.length

  // 计算平均分数
  const avgScore = history.reduce((sum, item) => sum + item.risk_assessment.risk_score, 0) / totalCount

  // 风险等级分布
  const riskDistribution: Record<string, number> = {}
  history.forEach(item => {
    const level = item.risk_assessment.risk_level
    riskDistribution[level] = (riskDistribution[level] || 0) + 1
  })

  // 趋势分析（最近3次 vs 之前3次）
  let recentTrend: 'improving' | 'stable' | 'worsening' = 'stable'
  if (history.length >= 6) {
    const recentAvg = history.slice(0, 3).reduce((sum, item) => sum + item.risk_assessment.risk_score, 0) / 3
    const previousAvg = history.slice(3, 6).reduce((sum, item) => sum + item.risk_assessment.risk_score, 0) / 3

    if (recentAvg < previousAvg - 5) recentTrend = 'improving'
    else if (recentAvg > previousAvg + 5) recentTrend = 'worsening'
  }

  return {
    totalCount,
    avgScore,
    riskDistribution,
    recentTrend
  }
})

// Trigger统计
const triggerStats = computed(() => {
  const history = assessmentStore.history
  const triggerCounts: Record<string, number> = {}

  history.forEach(assessment => {
    assessment.triggers?.forEach(trigger => {
      triggerCounts[trigger.name] = (triggerCounts[trigger.name] || 0) + 1
    })
  })

  return Object.entries(triggerCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([name, count]) => ({ name, count }))
})

// 加载数据
const loadData = async () => {
  if (!userStore.user?.id) return

  loading.value = true
  try {
    await assessmentStore.fetchHistory(userStore.user.id, 1, 50)
  } catch (error) {
    console.error('Load analysis data error:', error)
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="analysis-page page-container">
    <van-nav-bar title="数据分析" left-arrow @click-left="goBack" />

    <van-pull-refresh v-model="loading" @refresh="loadData">
      <div class="content-wrapper">
        <!-- 统计概览 -->
        <van-cell-group title="数据概览" inset>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value">{{ stats.totalCount }}</div>
              <div class="stat-label">评估次数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ stats.avgScore.toFixed(1) }}</div>
              <div class="stat-label">平均分数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">
                <van-icon
                  :name="stats.recentTrend === 'improving' ? 'arrow-down' :
                        stats.recentTrend === 'worsening' ? 'arrow-up' : 'minus'"
                  :color="stats.recentTrend === 'improving' ? '#07c160' :
                         stats.recentTrend === 'worsening' ? '#ee0a24' : '#969799'"
                />
              </div>
              <div class="stat-label">
                {{ stats.recentTrend === 'improving' ? '改善中' :
                   stats.recentTrend === 'worsening' ? '需关注' : '稳定' }}
              </div>
            </div>
          </div>
        </van-cell-group>

        <!-- 风险等级分布 -->
        <van-cell-group title="风险等级分布" inset>
          <div class="risk-distribution">
            <div
              v-for="(count, level) in stats.riskDistribution"
              :key="level"
              class="risk-bar-item"
            >
              <div class="risk-bar-label">
                <span>{{ assessmentStore.getRiskLevelText(level as string) }}</span>
                <span class="risk-bar-count">{{ count }}次</span>
              </div>
              <div class="risk-bar-container">
                <div
                  class="risk-bar"
                  :style="{
                    width: `${(count / stats.totalCount) * 100}%`,
                    backgroundColor: assessmentStore.getRiskLevelColor(level as string)
                  }"
                />
              </div>
            </div>

            <van-empty
              v-if="Object.keys(stats.riskDistribution).length === 0"
              description="暂无数据"
              image-size="80"
            />
          </div>
        </van-cell-group>

        <!-- 常见风险信号 -->
        <van-cell-group title="常见风险信号 (Top 5)" inset>
          <van-cell
            v-for="(item, index) in triggerStats"
            :key="item.name"
            :title="`${index + 1}. ${item.name}`"
            :value="`${item.count}次`"
          />

          <van-empty
            v-if="triggerStats.length === 0"
            description="暂无数据"
            image-size="80"
          />
        </van-cell-group>

        <!-- 评估历史趋势 -->
        <van-cell-group title="评估历史" inset>
          <div class="timeline">
            <div
              v-for="(item, index) in assessmentStore.history.slice(0, 10)"
              :key="item.assessment_id"
              class="timeline-item"
            >
              <div class="timeline-dot" :style="{ backgroundColor: assessmentStore.getRiskLevelColor(item.risk_assessment.risk_level) }" />
              <div class="timeline-content">
                <div class="timeline-header">
                  <van-tag
                    :type="item.risk_assessment.risk_level === 'R0' ? 'success' :
                          item.risk_assessment.risk_level === 'R1' ? 'primary' :
                          item.risk_assessment.risk_level === 'R2' ? 'warning' : 'danger'"
                    size="medium"
                  >
                    {{ assessmentStore.getRiskLevelText(item.risk_assessment.risk_level) }}
                  </van-tag>
                  <span class="timeline-score">{{ item.risk_assessment.risk_score.toFixed(1) }}分</span>
                </div>
                <div class="timeline-time">{{ new Date(item.timestamp).toLocaleString('zh-CN') }}</div>
                <div class="timeline-concern">{{ item.risk_assessment.primary_concern }}</div>
              </div>
            </div>

            <van-empty
              v-if="assessmentStore.history.length === 0"
              description="暂无评估记录"
              image-size="80"
            >
              <van-button type="primary" size="small" @click="router.push('/data-input')">
                开始第一次评估
              </van-button>
            </van-empty>
          </div>
        </van-cell-group>

        <!-- 健康建议 -->
        <van-cell-group title="健康建议" inset>
          <div class="health-tips">
            <van-notice-bar
              v-if="stats.recentTrend === 'worsening'"
              left-icon="warning-o"
              color="#ee0a24"
              background="#fff1f0"
              text="您的健康状况有下降趋势，建议咨询专业医生"
            />
            <van-notice-bar
              v-else-if="stats.recentTrend === 'improving'"
              left-icon="success"
              color="#07c160"
              background="#f0f9ff"
              text="您的健康状况正在改善，请继续保持良好习惯"
            />
            <van-notice-bar
              v-else
              left-icon="info-o"
              color="#1989fa"
              background="#f0f9ff"
              text="建议每周进行1-2次评估，持续关注健康状况"
            />
          </div>
        </van-cell-group>
      </div>
    </van-pull-refresh>
  </div>
</template>

<style scoped>
.analysis-page {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.content-wrapper {
  padding: 16px;
}

/* 统计网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding: 16px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #323233;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #969799;
}

/* 风险分布 */
.risk-distribution {
  padding: 16px;
}

.risk-bar-item {
  margin-bottom: 16px;
}

.risk-bar-item:last-child {
  margin-bottom: 0;
}

.risk-bar-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #323233;
}

.risk-bar-count {
  color: #969799;
  font-size: 12px;
}

.risk-bar-container {
  height: 8px;
  background-color: #f7f8fa;
  border-radius: 4px;
  overflow: hidden;
}

.risk-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

/* 时间轴 */
.timeline {
  padding: 16px;
}

.timeline-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  position: relative;
}

.timeline-item:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 20px;
  bottom: -20px;
  width: 2px;
  background-color: #ebedf0;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 4px;
  flex-shrink: 0;
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px #ebedf0;
}

.timeline-content {
  flex: 1;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.timeline-score {
  font-size: 16px;
  font-weight: 500;
  color: #323233;
}

.timeline-time {
  font-size: 12px;
  color: #969799;
  margin-bottom: 4px;
}

.timeline-concern {
  font-size: 14px;
  color: #646566;
}

/* 健康提示 */
.health-tips {
  padding: 16px;
}
</style>
