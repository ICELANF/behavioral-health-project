/**
 * useCurrentUser — 全平台用户信息组合式函数
 *
 * 提供: userName, avatarSrc, avatarText, roleName, adminLevel,
 *       refreshUserInfo(), handleLogout()
 */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const ROLE_NAMES: Record<string, string> = {
  OBSERVER: '观察者',
  GROWER: '成长者',
  SHARER: '分享者',
  COACH: '教练',
  PROMOTER: '推广者',
  SUPERVISOR: '督导',
  MASTER: '大师',
  ADMIN: '管理员',
}

const ROLE_LEVEL_MAP: Record<string, number> = {
  OBSERVER: 1, GROWER: 2, SHARER: 3, COACH: 4,
  PROMOTER: 5, SUPERVISOR: 5, MASTER: 6, ADMIN: 99,
}

export function useCurrentUser() {
  const router = useRouter()

  const userName = ref(
    localStorage.getItem('admin_name') || localStorage.getItem('admin_username') || ''
  )
  const avatarSrc = ref(localStorage.getItem('admin_avatar') || '')

  const avatarText = computed(() => {
    const name = userName.value || ''
    return name.length > 2 ? name.slice(-2) : name || '?'
  })

  const roleName = computed(() => {
    const r = localStorage.getItem('admin_role') || ''
    return ROLE_NAMES[r] || r || '用户'
  })

  const adminLevel = ROLE_LEVEL_MAP[localStorage.getItem('admin_role') || ''] || 0

  /** 调 GET /v1/auth/me 更新头像和姓名到 ref + localStorage */
  const refreshUserInfo = async () => {
    if (!localStorage.getItem('admin_token')) return
    try {
      const res = await request.get('/v1/auth/me')
      const me = res.data
      if (me.avatar_url) {
        avatarSrc.value = me.avatar_url
        localStorage.setItem('admin_avatar', me.avatar_url)
      }
      if (me.full_name) {
        userName.value = me.full_name
        localStorage.setItem('admin_name', me.full_name)
      }
    } catch {
      // silent — token may be expired
    }
  }

  /** 清除 localStorage → 跳转登录页 */
  const handleLogout = () => {
    const keys = [
      'admin_token', 'admin_refresh_token', 'admin_username', 'admin_role',
      'admin_level', 'admin_name', 'admin_user_id', 'admin_avatar',
    ]
    keys.forEach(k => localStorage.removeItem(k))
    router.push('/login')
  }

  return {
    userName,
    avatarSrc,
    avatarText,
    roleName,
    adminLevel,
    refreshUserInfo,
    handleLogout,
  }
}
