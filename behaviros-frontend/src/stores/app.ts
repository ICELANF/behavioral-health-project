/**
 * 应用全局 Store — 侧边栏状态、主题、通知
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const theme = ref<'light' | 'dark'>('light')
  const notifications = ref<Array<{ id: string; type: string; message: string; time: string }>>([])

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function addNotification(type: string, message: string) {
    notifications.value.unshift({
      id: Date.now().toString(),
      type,
      message,
      time: new Date().toISOString(),
    })
    if (notifications.value.length > 50) {
      notifications.value = notifications.value.slice(0, 50)
    }
  }

  function clearNotifications() {
    notifications.value = []
  }

  return {
    sidebarCollapsed, theme, notifications,
    toggleSidebar, addNotification, clearNotifications,
  }
})
