import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface NotificationMessage {
  type: string  // coach_push | assessment | device_alert | system | coach_message | reminder
  title?: string
  body?: string
  data?: Record<string, any>
  timestamp?: string
}

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)
  const latestMessages = ref<NotificationMessage[]>([])
  const connected = ref(false)

  function increment() {
    unreadCount.value++
  }

  function setCount(n: number) {
    unreadCount.value = Math.max(0, n)
  }

  function markRead(count: number = 1) {
    unreadCount.value = Math.max(0, unreadCount.value - count)
  }

  function addMessage(msg: NotificationMessage) {
    latestMessages.value.unshift(msg)
    // 只保留最近 50 条
    if (latestMessages.value.length > 50) {
      latestMessages.value = latestMessages.value.slice(0, 50)
    }
    increment()
  }

  function setConnected(val: boolean) {
    connected.value = val
  }

  function reset() {
    unreadCount.value = 0
    latestMessages.value = []
    connected.value = false
  }

  return {
    unreadCount,
    latestMessages,
    connected,
    increment,
    setCount,
    markRead,
    addMessage,
    setConnected,
    reset,
  }
})
