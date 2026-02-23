import { computed } from 'vue'

export function useSearchScope() {
  const roleLevel = computed(() => {
    return parseInt(localStorage.getItem('bhp_role_level') || '0', 10)
  })

  const placeholder = computed(() => {
    const lv = roleLevel.value
    if (lv >= 4) return '搜索学员、任务、内容... (绑定范围)'
    if (lv >= 3) return '搜索内容、学习、任务...'
    if (lv >= 2) return '搜索内容、我的任务...'
    return '搜索健康内容...'
  })

  const modules = computed(() => {
    const lv = roleLevel.value
    if (lv >= 4) return ['users', 'prescriptions', 'tasks', 'checkins', 'content']
    if (lv >= 3) return ['content', 'tasks', 'checkins']
    if (lv >= 2) return ['content', 'tasks']
    return ['content']
  })

  return { roleLevel, placeholder, modules }
}
