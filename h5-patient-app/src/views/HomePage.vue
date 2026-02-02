<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAssessmentStore } from '@/stores/assessment'
import { showConfirmDialog } from 'vant'

const router = useRouter()
const userStore = useUserStore()
const assessmentStore = useAssessmentStore()

// 最近评估列表
const recentAssessments = ref<any[]>([])
const loading = ref(false)

/**
 * 加载最近评估
 */
const loadRecentAssessments = async () => {
  if (!userStore.user?.id) return

  loading.value = true
  try {
    recentAssessments.value = await assessmentStore.fetchRecent(userStore.user.id, 5)
  } catch (error) {
    console.error('Load recent assessments error:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 跳转到数据录入
 */
const goToDataInput = () => {
  router.push('/data-input')
}

/**
 * 跳转到历史记录
 */
const goToHistory = () => {
  router.push('/history')
}

/**
 * 跳转到数据分析
 */
const goToAnalysis = () => {
  router.push('/analysis')
}

/**
 * 跳转到个人设置
 */
const goToSettings = () => {
  router.push('/settings')
}

/**
 * 跳转到AI聊天
 */
const goToChat = () => {
  router.push('/chat')
}

/**
 * 跳转到健康数据
 */
const goToHealthData = () => {
  router.push('/health-data')
}

/**
 * 查看评估结果
 */
const viewResult = (assessmentId: string) => {
  router.push(`/result/${assessmentId}`)
}

/**
 * 用户登出
 */
const handleLogout = async () => {
  showConfirmDialog({
    title: '确认退出',
    message: '确定要退出登录吗？'
  })
    .then(async () => {
      await userStore.logout()
      router.replace('/login')
    })
    .catch(() => {
      // 取消
    })
}

/**
 * 格式化时间
 */
const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 小于1小时
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return `${minutes}分钟前`
  }

  // 小于1天
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000)
    return `${hours}小时前`
  }

  // 大于1天
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

onMounted(() => {
  loadRecentAssessments()
})
</script>

<template>
  <div class="home-page page-container">
    <van-nav-bar title="行为健康" right-text="退出" @click-right="handleLogout" />

    <div class="content-wrapper">
      <!-- 用户信息卡片 -->
      <van-card
        :title="userStore.userName"
        :desc="`用户ID: ${userStore.user?.id} | 角色: ${userStore.userRole}`"
        thumb="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
      >
        <template #tags>
          <van-tag plain type="primary">{{ userStore.user?.email }}</van-tag>
        </template>
      </van-card>

      <!-- AI 健康助手入口 -->
      <div class="ai-chat-entry" @click="goToChat">
        <div class="ai-chat-icon">
          <van-icon name="service-o" size="32" color="#1989fa" />
        </div>
        <div class="ai-chat-info">
          <div class="ai-chat-title">AI 健康助手</div>
          <div class="ai-chat-desc">随时为你解答健康问题</div>
        </div>
        <van-icon name="arrow" color="#969799" />
      </div>

      <!-- 快捷操作 -->
      <van-cell-group title="快捷操作" inset>
        <van-grid :column-num="3" :border="false">
          <van-grid-item icon="edit" text="数据录入" @click="goToDataInput" />
          <van-grid-item icon="chart-trending-o" text="健康数据" @click="goToHealthData" />
          <van-grid-item icon="bar-chart-o" text="历史记录" @click="goToHistory" />
          <van-grid-item icon="graphic" text="数据分析" @click="goToAnalysis" />
          <van-grid-item icon="service-o" text="AI助手" @click="goToChat" />
          <van-grid-item icon="setting-o" text="个人设置" @click="goToSettings" />
        </van-grid>
      </van-cell-group>

      <!-- 最近评估 -->
      <van-cell-group title="最近评估" inset>
        <template v-if="loading">
          <div class="loading-wrapper">
            <van-loading>加载中...</van-loading>
          </div>
        </template>

        <template v-else-if="recentAssessments.length > 0">
          <van-cell
            v-for="item in recentAssessments"
            :key="item.assessment_id"
            :title="formatTime(item.timestamp)"
            is-link
            @click="viewResult(item.assessment_id)"
          >
            <template #label>
              <div class="assessment-info">
                <span
                  class="risk-level"
                  :class="`risk-level-${item.risk_assessment.risk_level}`"
                  :style="{ color: assessmentStore.getRiskLevelColor(item.risk_assessment.risk_level) }"
                >
                  {{ assessmentStore.getRiskLevelText(item.risk_assessment.risk_level) }}
                </span>
                <span class="score">
                  分数: {{ item.risk_assessment.risk_score.toFixed(1) }}
                </span>
              </div>
            </template>
          </van-cell>
        </template>

        <template v-else>
          <div class="empty-state">
            <div class="empty-state-icon">📊</div>
            <div class="empty-state-text">暂无评估记录</div>
            <van-button type="primary" size="small" @click="goToDataInput" style="margin-top: 16px">
              立即开始评估
            </van-button>
          </div>
        </template>
      </van-cell-group>

      <!-- 健康提示 -->
      <van-notice-bar
        left-icon="volume-o"
        text="建议每周进行1-2次行为健康评估，及时了解自己的健康状况"
        style="margin: 16px"
      />
    </div>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
}

.ai-chat-entry {
  display: flex;
  align-items: center;
  padding: 16px;
  margin: 16px;
  background: linear-gradient(135deg, #e8f4ff, #f0f9eb);
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s;
}

.ai-chat-entry:active {
  transform: scale(0.98);
}

.ai-chat-icon {
  width: 56px;
  height: 56px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  box-shadow: 0 2px 8px rgba(25, 137, 250, 0.2);
}

.ai-chat-info {
  flex: 1;
}

.ai-chat-title {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 4px;
}

.ai-chat-desc {
  font-size: 13px;
  color: #969799;
}

.assessment-info {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

.risk-level {
  font-weight: 500;
}

.score {
  color: #969799;
  font-size: 12px;
}
</style>
