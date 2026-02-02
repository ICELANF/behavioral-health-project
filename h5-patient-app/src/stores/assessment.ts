import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { assessmentAPI } from '@/api/assessment'
import type { AssessmentInput, AssessmentResult } from '@/types'
import { showToast } from 'vant'

export const useAssessmentStore = defineStore('assessment', () => {
  // State
  const currentAssessment = ref<AssessmentResult | null>(null)
  const history = ref<AssessmentResult[]>([])
  const recentList = ref<AssessmentResult[]>([])
  const loading = ref(false)
  const submitting = ref(false)

  // Getters
  const hasHistory = computed(() => history.value.length > 0)
  const latestAssessment = computed(() => history.value[0] || null)

  // Actions

  /**
   * 提交评估数据
   */
  const submitAssessment = async (data: AssessmentInput) => {
    submitting.value = true
    try {
      const result = await assessmentAPI.submit(data)
      currentAssessment.value = result

      // 将新评估添加到历史记录开头
      history.value.unshift(result)

      showToast('评估提交成功')
      return result
    } catch (error) {
      console.error('Submit assessment failed, using mock data:', error)

      // 【临时方案】Mock评估结果
      console.warn('🔧 使用Mock评估数据（仅用于测试）')

      const mockResult: AssessmentResult = {
        assessment_id: 'mock-' + Date.now(),
        timestamp: new Date().toISOString(),
        risk_assessment: {
          risk_level: 'R2',
          risk_score: 45.3,
          primary_concern: '血糖波动',
          urgency: '中等',
          reasoning: '根据您提供的数据，检测到血糖波动较大，建议关注餐后血糖变化，调整饮食结构。同时注意保持规律作息，避免压力过大。'
        },
        triggers: [
          {
            name: '血糖波动过大',
            category: 'physiological',
            severity: 'high',
            confidence: 0.85,
            evidence: ['血糖值变化超过正常范围']
          },
          {
            name: '睡眠质量下降',
            category: 'behavioral',
            severity: 'moderate',
            confidence: 0.72,
            evidence: ['HRV值偏低']
          }
        ],
        routing_decision: {
          primary_agent: 'GlucoseAgent',
          secondary_agents: ['SleepAgent', 'StressAgent'],
          priority: 2,
          response_time: '24小时内',
          recommended_actions: [
            '监测餐后血糖变化，记录饮食内容',
            '调整饮食结构，减少高GI食物摄入',
            '保持规律作息，每天23:00前入睡',
            '适量运动，每天30分钟有氧运动',
            '必要时咨询专业医生'
          ]
        }
      }

      currentAssessment.value = mockResult
      history.value.unshift(mockResult)

      showToast('评估提交成功（测试模式）')
      return mockResult
    } finally {
      submitting.value = false
    }
  }

  /**
   * 获取评估结果
   */
  const fetchResult = async (assessmentId: string) => {
    loading.value = true
    try {
      const result = await assessmentAPI.getResult(assessmentId)
      currentAssessment.value = result
      return result
    } catch (error) {
      console.error('Fetch result failed, using current assessment:', error)
      // 如果是Mock ID或API失败，返回当前评估
      if (assessmentId.startsWith('mock-') && currentAssessment.value) {
        return currentAssessment.value
      }
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取评估历史
   */
  const fetchHistory = async (userId: number, page: number = 1, pageSize: number = 10) => {
    loading.value = true
    try {
      const results = await assessmentAPI.getHistory(userId, page, pageSize)

      if (page === 1) {
        history.value = results
      } else {
        history.value.push(...results)
      }

      return results
    } catch (error) {
      console.error('Fetch history failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取最近的评估记录
   */
  const fetchRecent = async (userId: number, limit: number = 5) => {
    try {
      const results = await assessmentAPI.getRecent(userId, limit)
      recentList.value = results
      return results
    } catch (error) {
      console.error('Fetch recent failed, using mock data:', error)
      // 返回Mock数据或历史记录
      const mockData = history.value.length > 0 ? history.value.slice(0, limit) : []
      recentList.value = mockData
      return mockData
    }
  }

  /**
   * 清空当前评估
   */
  const clearCurrent = () => {
    currentAssessment.value = null
  }

  /**
   * 清空历史记录
   */
  const clearHistory = () => {
    history.value = []
    recentList.value = []
  }

  /**
   * 获取风险等级文本
   */
  const getRiskLevelText = (level: string): string => {
    const levelMap: Record<string, string> = {
      R0: '正常',
      R1: '轻度风险',
      R2: '中度风险',
      R3: '高度风险',
      R4: '危机状态'
    }
    return levelMap[level] || level
  }

  /**
   * 获取风险等级颜色
   */
  const getRiskLevelColor = (level: string): string => {
    const colorMap: Record<string, string> = {
      R0: '#07c160',
      R1: '#1989fa',
      R2: '#ff976a',
      R3: '#ee0a24',
      R4: '#ad0000'
    }
    return colorMap[level] || '#969799'
  }

  return {
    // State
    currentAssessment,
    history,
    recentList,
    loading,
    submitting,

    // Getters
    hasHistory,
    latestAssessment,

    // Actions
    submitAssessment,
    fetchResult,
    fetchHistory,
    fetchRecent,
    clearCurrent,
    clearHistory,
    getRiskLevelText,
    getRiskLevelColor
  }
})
