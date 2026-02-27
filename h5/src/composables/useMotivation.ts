import { ref, onMounted } from 'vue'
import api from '@/api/index'

interface WeekTrendItem {
  date: string
  pct: number
}

interface RecentBadge {
  name: string
  icon: string
}

export function useMotivation() {
  const todayPoints = ref(0)
  const weekPoints = ref(0)
  const totalPoints = ref(0)
  const tasksTotal = ref(0)
  const currentStreak = ref(0)
  const longestStreak = ref(0)
  const weekTrend = ref<WeekTrendItem[]>([])
  const recentBadge = ref<RecentBadge | null>(null)
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const data: any = await api.get('/api/v1/home/motivation-stats')
      todayPoints.value = data.today_points ?? 0
      weekPoints.value = data.week_points ?? 0
      totalPoints.value = data.total_points ?? 0
      tasksTotal.value = data.tasks_completed_total ?? 0
      currentStreak.value = data.current_streak ?? 0
      longestStreak.value = data.longest_streak ?? 0
      weekTrend.value = data.week_trend ?? []
      recentBadge.value = data.recent_badge ?? null
    } catch {
      // use defaults
    } finally {
      loading.value = false
    }
  }

  onMounted(load)

  return {
    todayPoints,
    weekPoints,
    totalPoints,
    tasksTotal,
    currentStreak,
    longestStreak,
    weekTrend,
    recentBadge,
    loading,
    reload: load,
  }
}
