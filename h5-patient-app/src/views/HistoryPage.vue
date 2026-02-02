<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAssessmentStore } from '@/stores/assessment'
import type { AssessmentResult } from '@/types'

const router = useRouter()
const userStore = useUserStore()
const assessmentStore = useAssessmentStore()

const loading = ref(false)
const finished = ref(false)
const page = ref(1)
const historyList = ref<AssessmentResult[]>([])

/**
 * 加载评估历史
 */
const onLoad = async () => {
  if (!userStore.user?.id) {
    finished.value = true
    return
  }

  loading.value = true
  try {
    const results = await assessmentStore.fetchHistory(userStore.user.id, page.value, 10)

    if (results.length === 0) {
      finished.value = true
    } else {
      historyList.value.push(...results)
      page.value++
    }
  } catch (error) {
    console.error('Load history error:', error)
    finished.value = true
  } finally {
    loading.value = false
  }
}

/**
 * 查看评估详情
 */
const viewDetail = (assessmentId: string) => {
  router.push(`/result/${assessmentId}`)
}

/**
 * 格式化时间
 */
const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

/**
 * 返回首页
 */
const goBack = () => {
  router.back()
}

onMounted(() => {
  // 如果store中已有历史数据，直接使用
  if (assessmentStore.history.length > 0) {
    historyList.value = [...assessmentStore.history]
    finished.value = true
  }
})
</script>

<template>
  <div class="history-page page-container">
    <van-nav-bar title="评估历史" left-arrow @click-left="goBack">
      <template #right>
        <van-tag type="warning">Beta</van-tag>
      </template>
    </van-nav-bar>

    <div class="content-wrapper">
      <!-- 历史记录列表 -->
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="onLoad"
      >
        <van-cell
          v-for="item in historyList"
          :key="item.assessment_id"
          :title="formatTime(item.timestamp)"
          is-link
          @click="viewDetail(item.assessment_id)"
        >
          <template #label>
            <div class="assessment-info">
              <div class="risk-info">
                <van-tag
                  :type="item.risk_assessment.risk_level === 'R0' ? 'success' :
                        item.risk_assessment.risk_level === 'R1' ? 'primary' :
                        item.risk_assessment.risk_level === 'R2' ? 'warning' : 'danger'"
                >
                  {{ assessmentStore.getRiskLevelText(item.risk_assessment.risk_level) }}
                </van-tag>
                <span class="score">{{ item.risk_assessment.risk_score.toFixed(1) }}分</span>
              </div>
              <div class="concern">
                主要关注: {{ item.risk_assessment.primary_concern }}
              </div>
            </div>
          </template>
        </van-cell>

        <!-- 空状态 -->
        <div v-if="historyList.length === 0 && finished" class="empty-state">
          <div class="empty-state-icon">📋</div>
          <div class="empty-state-text">暂无评估历史</div>
          <van-button type="primary" size="small" @click="router.push('/data-input')" style="margin-top: 16px">
            开始第一次评估
          </van-button>
        </div>
      </van-list>
    </div>
  </div>
</template>

<style scoped>
.history-page {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.content-wrapper {
  padding: 16px;
}

.assessment-info {
  margin-top: 8px;
}

.risk-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.score {
  font-size: 14px;
  font-weight: 500;
  color: #323233;
}

.concern {
  font-size: 12px;
  color: #969799;
  margin-top: 4px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.empty-state-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state-text {
  font-size: 14px;
  color: #969799;
}
</style>
