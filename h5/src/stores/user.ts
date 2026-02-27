import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { UserState, WearableData } from '@/api/types'
import storage from '@/utils/storage'

const ROLE_LABELS: Record<string, string> = {
  observer: '观察者',
  grower: '成长者',
  sharer: '分享者',
  coach: '教练',
  promoter: '促进师',
  supervisor: '督导师',
  master: '大师',
  admin: '管理员',
}

const DEFAULT_AVATAR = '/images/default-avatar.svg'

export const useUserStore = defineStore('user', () => {
  // 从本地存储恢复状态
  const storedUserId = storage.getUserId()
  const storedName = storage.getUserName()
  const storedEfficacy = storage.getEfficacyScore()
  const storedWearable = storage.getWearableData()

  // 状态
  const userId = ref<string>(storedUserId || 'user_' + Date.now())
  const name = ref<string>(storedName)
  const efficacyScore = ref<number>(storedEfficacy)
  const wearableData = ref<WearableData>(storedWearable)

  // 新增: 头像、角色、成长积分
  const avatar = ref<string>(localStorage.getItem('bhp_user_avatar') || '')
  const role = ref<string>(localStorage.getItem('bhp_user_role') || 'grower')
  const growthPoints = ref<number>(parseInt(localStorage.getItem('bhp_user_growth_points') || '0', 10))

  // 计算属性: 头像URL (带默认fallback)
  const avatarUrl = computed(() => avatar.value || DEFAULT_AVATAR)

  // 计算属性: 中文角色名
  const roleLabel = computed(() => ROLE_LABELS[role.value] || role.value)

  // 首次运行时保存 userId
  if (!storedUserId) {
    storage.setUserId(userId.value)
  }

  // 监听变化并持久化
  watch(userId, (val) => storage.setUserId(val))
  watch(name, (val) => storage.setUserName(val))
  watch(efficacyScore, (val) => storage.setEfficacyScore(val))
  watch(wearableData, (val) => storage.setWearableData(val), { deep: true })
  watch(avatar, (val) => localStorage.setItem('bhp_user_avatar', val))
  watch(role, (val) => localStorage.setItem('bhp_user_role', val))
  watch(growthPoints, (val) => localStorage.setItem('bhp_user_growth_points', String(val)))

  // 计算属性
  const efficacyLevel = computed(() => {
    if (efficacyScore.value < 20) return 'low'
    if (efficacyScore.value < 50) return 'medium'
    return 'high'
  })

  const efficacyColor = computed(() => {
    if (efficacyScore.value < 20) return '#ee0a24'
    if (efficacyScore.value < 50) return '#ff976a'
    return '#07c160'
  })

  const efficacyText = computed(() => {
    if (efficacyScore.value < 20) return '需要休息'
    if (efficacyScore.value < 50) return '逐步恢复'
    return '状态良好'
  })

  // 方法
  function setEfficacyScore(score: number) {
    efficacyScore.value = Math.max(0, Math.min(100, score))
  }

  function updateWearableData(data: Partial<WearableData>) {
    wearableData.value = { ...wearableData.value, ...data }
  }

  function setUserInfo(info: Partial<UserState> & { avatar?: string; role?: string; growth_points?: number }) {
    if (info.id) userId.value = info.id
    if (info.name) name.value = info.name
    if (info.efficacy_score !== undefined) efficacyScore.value = info.efficacy_score
    if (info.avatar !== undefined) avatar.value = info.avatar
    if (info.role) role.value = info.role
    if (info.growth_points !== undefined) growthPoints.value = info.growth_points
  }

  function updateAvatar(url: string) {
    avatar.value = url
  }

  function updateName(newName: string) {
    name.value = newName
  }

  function logout() {
    storage.clearAuth()
    storage.clearAll()
    userId.value = ''
    name.value = '用户'
    efficacyScore.value = 50
    wearableData.value = {}
    avatar.value = ''
    role.value = 'grower'
    growthPoints.value = 0
    localStorage.removeItem('bhp_user_avatar')
    localStorage.removeItem('bhp_user_role')
    localStorage.removeItem('bhp_user_growth_points')
    window.location.href = '/portal'
  }

  return {
    userId,
    name,
    efficacyScore,
    wearableData,
    avatar,
    role,
    growthPoints,
    avatarUrl,
    roleLabel,
    efficacyLevel,
    efficacyColor,
    efficacyText,
    setEfficacyScore,
    updateWearableData,
    setUserInfo,
    updateAvatar,
    updateName,
    logout
  }
})
