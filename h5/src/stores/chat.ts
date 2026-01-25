import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { ChatMessage, Task, Expert } from '@/api/types'
import chatApi from '@/api/chat'
import { useUserStore } from './user'
import storage from '@/utils/storage'

export const useChatStore = defineStore('chat', () => {
  // 从本地存储恢复状态
  const storedMessages = storage.getChatMessages()
  const storedTasks = storage.getTasks()

  // 状态
  const messages = ref<ChatMessage[]>(storedMessages)
  const tasks = ref<Task[]>(storedTasks)

  // 监听变化并持久化
  watch(messages, (val) => storage.setChatMessages(val), { deep: true })
  watch(tasks, (val) => storage.setTasks(val), { deep: true })
  const experts = ref<Expert[]>([
    { id: 'mental_health', name: '心理咨询师', role: '情绪管理、压力调节' },
    { id: 'nutrition', name: '营养师', role: '膳食指导、营养建议' },
    { id: 'sports_rehab', name: '运动康复师', role: '运动处方、损伤康复' },
    { id: 'tcm_wellness', name: '中医养生师', role: '体质调理、养生保健' }
  ])
  const currentExpert = ref<string>('mental_health')
  const isLoading = ref<boolean>(false)
  const conversationId = ref<string>('')

  // 计算属性
  const currentExpertInfo = computed(() => {
    return experts.value.find(e => e.id === currentExpert.value)
  })

  const pendingTasks = computed(() => {
    return tasks.value.filter(t => !t.completed)
  })

  const completedTasks = computed(() => {
    return tasks.value.filter(t => t.completed)
  })

  // 方法
  async function sendMessage(content: string) {
    const userStore = useUserStore()

    // 添加用户消息
    const userMessage: ChatMessage = {
      id: 'msg_' + Date.now(),
      role: 'user',
      content,
      timestamp: Date.now()
    }
    messages.value.push(userMessage)

    isLoading.value = true

    try {
      const response = await chatApi.sendMessage({
        user_id: userStore.userId,
        message: content,
        mode: 'ollama',
        efficacy_score: userStore.efficacyScore,
        wearable_data: userStore.wearableData
      })

      // 添加助手消息
      const assistantMessage: ChatMessage = {
        id: 'msg_' + Date.now(),
        role: 'assistant',
        content: response.answer || '抱歉，我暂时无法回答这个问题。',
        expert: currentExpertInfo.value?.name,
        timestamp: Date.now(),
        tasks: response.tasks
      }
      messages.value.push(assistantMessage)

      // 更新任务列表
      if (response.tasks && response.tasks.length > 0) {
        tasks.value.push(...response.tasks)
      }

      // 如果没有返回任务，尝试调用任务分解接口
      if (!response.tasks || response.tasks.length === 0) {
        try {
          const taskResponse = await chatApi.decomposeTasks(content, userStore.efficacyScore)
          if (taskResponse.tasks && taskResponse.tasks.length > 0) {
            // 为任务生成唯一 ID
            const newTasks = taskResponse.tasks.map((t: any, idx: number) => ({
              ...t,
              id: Date.now() + idx
            }))
            tasks.value.push(...newTasks)
            assistantMessage.tasks = newTasks
          }
        } catch (e) {
          console.log('Task decomposition skipped')
        }
      }

      if (response.conversation_id) {
        conversationId.value = response.conversation_id
      }

    } catch (error) {
      console.error('Send message error:', error)
      const errorMessage: ChatMessage = {
        id: 'msg_' + Date.now(),
        role: 'assistant',
        content: '网络错误，请稍后重试。',
        timestamp: Date.now()
      }
      messages.value.push(errorMessage)
    } finally {
      isLoading.value = false
    }
  }

  function setCurrentExpert(expertId: string) {
    currentExpert.value = expertId
  }

  function toggleTaskComplete(taskId: number) {
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      task.completed = !task.completed
    }
  }

  function clearMessages() {
    messages.value = []
    conversationId.value = ''
  }

  return {
    messages,
    tasks,
    experts,
    currentExpert,
    isLoading,
    conversationId,
    currentExpertInfo,
    pendingTasks,
    completedTasks,
    sendMessage,
    setCurrentExpert,
    toggleTaskComplete,
    clearMessages
  }
})
