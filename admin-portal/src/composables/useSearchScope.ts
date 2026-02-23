import { computed } from 'vue'

const ROLE_LEVEL_MAP: Record<string, number> = {
  OBSERVER: 1, GROWER: 2, SHARER: 3, COACH: 4,
  PROMOTER: 5, SUPERVISOR: 5, MASTER: 6, ADMIN: 99,
  // backward compat
  PATIENT: 2, EXPERT: 5, COACH_SENIOR: 4, COACH_INTERMEDIATE: 4, COACH_JUNIOR: 4,
}

export function useSearchScope() {
  const roleLevel = computed(() => {
    const role = localStorage.getItem('admin_role') || ''
    return ROLE_LEVEL_MAP[role] || 0
  })

  const placeholder = computed(() => {
    const lv = roleLevel.value
    if (lv >= 99) return '搜索用户、内容、处方、任务... (全平台数据)'
    if (lv >= 4) return '搜索我的学员、消息、任务... (绑定学员范围)'
    if (lv >= 3) return '搜索内容、我的学习、任务...'
    return '搜索内容、我的任务...'
  })

  const scopeLabel = computed(() => {
    const lv = roleLevel.value
    if (lv >= 99) return '全平台'
    if (lv >= 4) return '绑定范围'
    return '个人范围'
  })

  const modules = computed(() => {
    const lv = roleLevel.value
    if (lv >= 99) return ['users', 'prescriptions', 'tasks', 'checkins', 'content']
    if (lv >= 4) return ['users', 'prescriptions', 'tasks', 'checkins', 'content']
    if (lv >= 3) return ['content', 'tasks', 'checkins']
    return ['content', 'tasks']
  })

  return { roleLevel, placeholder, scopeLabel, modules }
}
