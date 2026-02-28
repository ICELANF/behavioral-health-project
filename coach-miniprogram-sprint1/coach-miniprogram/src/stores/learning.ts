/**
 * Learning Store — 学习状态管理
 * 包含: 学分 / 学习进度 / 连续打卡 / 视频断点
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import http from '@/api/request'

// ─── 类型定义 ────────────────────────────────────────────────
export interface CreditSummary {
  total: number
  m1: number    // 知识类
  m2: number    // 技能类
  m3: number    // 实践类
  m4: number    // 评估类
  elective: number
}

export interface ContentProgress {
  content_id: number
  title: string
  cover_url?: string
  content_type: string
  progress_percent: number
  last_position?: string    // 视频秒数
  status: 'not_started' | 'in_progress' | 'completed'
  updated_at: string
}

export interface LearningStats {
  total_minutes: number
  today_minutes: number
  current_streak: number
  longest_streak: number
  total_points: number
  growth_points: number
  contribution_points: number
  influence_points: number
}

// ─── Store ───────────────────────────────────────────────────
export const useLearningStore = defineStore('learning', () => {
  // State
  const credits     = ref<CreditSummary>({ total: 0, m1: 0, m2: 0, m3: 0, m4: 0, elective: 0 })
  const stats       = ref<LearningStats | null>(null)
  const inProgress  = ref<ContentProgress[]>([])

  /** 视频断点缓存 { contentId: { percent, position(秒) } } */
  const videoProgress = ref<Record<number, { percent: number; position: number }>>({})

  // Computed
  const currentStreak = computed(() => stats.value?.current_streak || 0)
  const todayMinutes  = computed(() => stats.value?.today_minutes || 0)

  // Actions

  /** 加载学习统计 */
  async function loadStats() {
    try {
      const data = await http.get<LearningStats>('/v1/learning/my-stats')
      stats.value = data
    } catch { /* 静默 */ }
  }

  /** 加载学分汇总 */
  async function loadCredits() {
    try {
      const data = await http.get<CreditSummary>('/v1/credits/my')
      credits.value = data
    } catch { /* 静默 */ }
  }

  /** 加载进行中的课程（首页展示） */
  async function loadInProgress() {
    try {
      const list = await http.get<ContentProgress[]>('/v1/content/user/in-progress')
      inProgress.value = list.slice(0, 5)   // 最多展示5个
    } catch { /* 静默 */ }
  }

  /** 更新视频断点（由 VideoPlayer 每30s调用） */
  async function saveVideoProgress(contentId: number, percent: number, position: number) {
    // 本地缓存（即时）
    videoProgress.value[contentId] = { percent, position }

    // 上报服务端（30s心跳，防抖由调用方控制）
    try {
      await http.post('/v1/content/user/learning-progress', {
        content_id:      contentId,
        progress_percent: percent,
        last_position:   String(position)   // 视频秒数转字符串
      })
    } catch { /* 静默，下次重试 */ }
  }

  /** 获取视频断点（VideoPlayer 进入时调用） */
  async function getVideoProgress(contentId: number): Promise<number> {
    // 优先内存缓存
    if (videoProgress.value[contentId]) {
      return videoProgress.value[contentId].position
    }
    // 请求服务端
    try {
      const data = await http.get<ContentProgress>(`/v1/content/user/learning-progress/${contentId}`)
      if (data?.last_position) {
        const pos = parseInt(data.last_position)
        videoProgress.value[contentId] = { percent: data.progress_percent, position: pos }
        return pos
      }
    } catch { /* 无断点记录 */ }
    return 0
  }

  /** 完成课程模块（学分+积分联动） */
  async function completeModule(moduleId: string, evidenceType = 'attendance', score?: number) {
    const res = await http.post<{ credits_earned: number; points_earned: number }>(
      '/v1/learning/complete',
      { module_id: moduleId, evidence_type: evidenceType, score }
    )
    // 刷新学分和统计
    await Promise.all([loadCredits(), loadStats()])
    return res
  }

  /** 完成内容学习（积分触发） */
  async function completeContent(contentId: number, timeSpentSeconds: number) {
    await http.post('/v1/content/user/learning-progress', {
      content_id:        contentId,
      progress_percent:  100,
      time_spent_seconds: timeSpentSeconds,
      status:            'completed'
    })
    await loadStats()
  }

  return {
    credits, stats, inProgress, videoProgress,
    currentStreak, todayMinutes,
    loadStats, loadCredits, loadInProgress,
    saveVideoProgress, getVideoProgress,
    completeModule, completeContent
  }
})
