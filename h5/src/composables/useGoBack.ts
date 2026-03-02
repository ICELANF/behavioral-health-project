/**
 * useGoBack — 统一返回逻辑
 *
 * 优先 router.back()（有历史则真正后退），
 * 无历史时直接跳角色首页，避免"返回没反应"。
 */
import { useRouter } from 'vue-router'
import storage from '@/utils/storage'

const ROLE_HOME_MAP: Record<string, string> = {
  observer:   '/home/observer',
  grower:     '/home/today',
  sharer:     '/home/sharer',
  coach:      '/home/coach',
  promoter:   '/home/pro',
  supervisor: '/home/pro',
  master:     '/home/master',
  admin:      '/home/admin',
}

function getRoleHome(): string {
  const authUser = storage.getAuthUser()
  const role = (authUser?.role || 'observer').toLowerCase()
  return ROLE_HOME_MAP[role] || '/home/observer'
}

export function useGoBack() {
  const router = useRouter()

  function goBack() {
    const prevPath = window.history.state?.back as string | null
    if (prevPath) {
      router.back()
    } else {
      router.replace(getRoleHome())
    }
  }

  return { goBack }
}
