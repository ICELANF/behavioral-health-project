/**
 * 学习状态 Store
 * 管理学习记录、连续打卡、内容进度缓存
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import http from '@/api/request'

interface LearningStats {
  total_minutes:       number
  total_articles:      number
  total_courses:       number
  current_streak:      number
  longest_streak:      number
  total_points:        number
  weekly_minutes:      number[]   // 近7天每天分钟数
  monthly_completions: number
}

interface ContentProgress {
  content_id:       number
  progress_pct:     number   // 0-100
  completed:        boolean
  last_position?:   number   // 视频/音频秒数
}

export const useLearningStore = defineStore('learning', () => {
  const stats           = ref<LearningStats | null>(null)
  const progressCache   = ref<Record<number, ContentProgress>>({})
  const loading         = ref(false)
  const lastFetchedAt   = ref<number>(0)

  // ── Computed ──────────────────────────────────────────
  const currentStreak   = computed(() => stats.value?.current_streak  ?? 0)
  const totalMinutes    = computed(() => stats.value?.total_minutes    ?? 0)
  const weeklyMinutes   = computed(() => stats.value?.weekly_minutes   ?? [0,0,0,0,0,0,0])

  // ── Actions ───────────────────────────────────────────
  async function fetchStats(force = false) {
    const now = Date.now()
    if (!force && stats.value && now - lastFetchedAt.value < 60_000) return
    loading.value = true
    try {
      const res = await http.get<LearningStats>('/v1/learning/grower/stats')
      stats.value = res
      lastFetchedAt.value = now
    } catch {
      // 静默失败，保持旧数据
    } finally {
      loading.value = false
    }
  }

  function setProgress(contentId: number, progress: Partial<ContentProgress>) {
    progressCache.value[contentId] = {
      content_id:   contentId,
      progress_pct: 0,
      completed:    false,
      ...progressCache.value[contentId],
      ...progress,
    }
  }

  function getProgress(contentId: number): ContentProgress | undefined {
    return progressCache.value[contentId]
  }

  async function recordProgress(contentId: number, data: {
    progress_pct?: number
    completed?:    boolean
    last_position?: number
    time_spent_seconds?: number
  }) {
    try {
      await http.post(`/v1/content/${contentId}/progress`, data)
      setProgress(contentId, data as Partial<ContentProgress>)
    } catch {/* ignore */}
  }

  function reset() {
    stats.value         = null
    progressCache.value = {}
    lastFetchedAt.value = 0
  }

  return {
    stats,
    progressCache,
    loading,
    currentStreak,
    totalMinutes,
    weeklyMinutes,
    fetchStats,
    setProgress,
    getProgress,
    recordProgress,
    reset,
  }
})
