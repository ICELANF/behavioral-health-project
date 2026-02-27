import { ref, computed } from 'vue'
import api from '@/api/index'

export interface TodayAction {
  id: string
  order: number
  title: string
  tag: string
  tagColor: string
  timeHint: string
  inputMode?: 'photo' | 'voice' | 'text' | 'device'
  quickLabel?: string
  done: boolean
  doneTime?: string
  source?: string   // 'rx' | 'self' | 'coach' | 'system'
  agentId?: string
}

export interface CatalogItem {
  id: string
  category: string
  default_title: string
  estimated_minutes: number
  difficulty?: 'easy' | 'moderate' | 'challenging'
  icon?: string
  description?: string
  domain?: string
  points_reward?: { growth: number; contribution: number; influence: number }
  frequency_suggestion?: string
}

export function useTaskGroups() {
  const allTasks = ref<TodayAction[]>([])
  const dailyPoints = ref(0)
  const streakDays = ref(0)

  // ── 分组 ──
  const coachTasks = computed(() =>
    allTasks.value.filter(a => !a.done && a.source === 'coach')
  )
  const aiTasks = computed(() =>
    allTasks.value.filter(a => !a.done && a.source === 'rx')
  )
  const selfTasks = computed(() =>
    allTasks.value.filter(a => !a.done && (a.source === 'self' || a.source === 'system'))
  )
  const doneTasks = computed(() =>
    allTasks.value.filter(a => a.done)
  )

  const totalCount = computed(() => allTasks.value.length)
  const doneCount = computed(() => doneTasks.value.length)
  const completionPct = computed(() =>
    totalCount.value > 0 ? Math.round((doneCount.value / totalCount.value) * 100) : 0
  )

  // ── 加载今日任务 ──
  async function loadTodayTasks() {
    try {
      const data: any = await api.get('/api/v1/daily-tasks/today')
      allTasks.value = (data.tasks || []).map((t: any) => ({
        id: t.id,
        order: t.order,
        title: t.title,
        tag: t.tag,
        tagColor: t.tag_color,
        timeHint: t.time_hint,
        inputMode: t.input_mode,
        quickLabel: t.quick_label,
        done: t.done,
        doneTime: t.done_time,
        source: t.source,
        agentId: t.agent_id,
      }))
      streakDays.value = data.streak_days || 0
    } catch { /* 静默 */ }
  }

  // ── 打卡 ──
  async function checkin(action: TodayAction) {
    // 乐观更新
    action.done = true
    action.doneTime = new Date().toTimeString().slice(0, 5)

    let result = {
      points_earned: 0, emoji: '', message: '', streak_days: 0, badge_unlocked: '',
      points_breakdown: null as Record<string, number> | null, badge_name: '', milestone_reached: '',
    }
    try {
      const res: any = await api.post(`/api/v1/daily-tasks/${action.id}/checkin`)
      result = { ...result, ...res }
      if (res.streak_days) streakDays.value = res.streak_days
      if (res.points_earned) dailyPoints.value += res.points_earned
    } catch { /* 乐观更新已生效 */ }

    return result
  }

  // ── 删除自选任务 ──
  async function removeSelfTask(taskId: string) {
    try {
      await api.delete(`/api/v1/daily-tasks/${taskId}`)
      allTasks.value = allTasks.value.filter(t => t.id !== taskId)
      return true
    } catch {
      return false
    }
  }

  // ── 自选目录 ──
  const catalog = ref<CatalogItem[]>([])
  const catalogLoading = ref(false)

  async function loadCatalog() {
    catalogLoading.value = true
    try {
      const data: any = await api.get('/api/v1/daily-tasks/catalog')
      catalog.value = (data.items || []).map((c: any) => ({
        id: c.id,
        category: c.category || c.tag || '',
        default_title: c.default_title || c.title || '',
        estimated_minutes: c.estimated_minutes || 0,
        difficulty: c.difficulty || 'easy',
        icon: c.icon || '',
        description: c.description || '',
        domain: c.domain || '',
        points_reward: c.points_reward || null,
        frequency_suggestion: c.frequency_suggestion || 'daily',
      }))
    } catch { /* 静默 */ }
    catalogLoading.value = false
  }

  async function addFromCatalog(catalogId: string, customTitle?: string) {
    try {
      const body: any = { catalog_id: catalogId }
      if (customTitle) body.custom_title = customTitle
      await api.post('/api/v1/daily-tasks/add-from-catalog', body)
      // 重新加载任务列表
      await loadTodayTasks()
      return true
    } catch {
      return false
    }
  }

  return {
    allTasks,
    coachTasks,
    aiTasks,
    selfTasks,
    doneTasks,
    dailyPoints,
    streakDays,
    totalCount,
    doneCount,
    completionPct,
    loadTodayTasks,
    checkin,
    removeSelfTask,
    catalog,
    catalogLoading,
    loadCatalog,
    addFromCatalog,
  }
}
