import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { DailyTask } from '@/data/tasks'
import { DEFAULT_TASKS } from '@/data/tasks'

export const useVisionStore = defineStore('vision', () => {
  const tasks = ref<DailyTask[]>(DEFAULT_TASKS.map(t => ({ ...t })))
  const score = ref(0)
  const streak = ref(0)
  const userName = ref('同学')

  const doneCount = computed(() => tasks.value.filter(t => t.done).length)
  const riskLevel = computed(() => {
    if (doneCount.value >= 4) return 'normal'
    if (doneCount.value >= 2) return 'watch'
    return 'alert'
  })

  function toggleTask(id: number) {
    const t = tasks.value.find(t => t.id === id)
    if (t) t.done = !t.done
  }

  function setScore(s: number) { score.value = s }
  function setStreak(s: number) { streak.value = s }
  function setUserName(n: string) { userName.value = n }

  return { tasks, score, streak, userName, doneCount, riskLevel, toggleTask, setScore, setStreak, setUserName }
})
