import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { UserState, WearableData } from '@/api/types'
import storage from '@/utils/storage'

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

  // 首次运行时保存 userId
  if (!storedUserId) {
    storage.setUserId(userId.value)
  }

  // 监听变化并持久化
  watch(userId, (val) => storage.setUserId(val))
  watch(name, (val) => storage.setUserName(val))
  watch(efficacyScore, (val) => storage.setEfficacyScore(val))
  watch(wearableData, (val) => storage.setWearableData(val), { deep: true })

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

  function setUserInfo(info: Partial<UserState>) {
    if (info.id) userId.value = info.id
    if (info.name) name.value = info.name
    if (info.efficacy_score !== undefined) efficacyScore.value = info.efficacy_score
  }

  return {
    userId,
    name,
    efficacyScore,
    wearableData,
    efficacyLevel,
    efficacyColor,
    efficacyText,
    setEfficacyScore,
    updateWearableData,
    setUserInfo
  }
})
