<template>
  <router-view />
</template>

<script setup lang="ts">
import { watch, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { showNotify } from 'vant'
import storage from '@/utils/storage'
import { useNotificationStore, type NotificationMessage } from '@/stores/notification'

const route = useRoute()
const notifStore = useNotificationStore()

let ws: WebSocket | null = null
let heartbeatTimer: ReturnType<typeof setInterval> | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let retryCount = 0
const MAX_RETRIES = 10
const RECONNECT_INTERVAL = 3000
const HEARTBEAT_INTERVAL = 30000

function getWsUrl(): string | null {
  const token = storage.getToken()
  const authUser = storage.getAuthUser()
  const userId = authUser?.id
  if (!token || !userId) return null

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return `${protocol}//${host}/ws/user/${userId}?token=${token}`
}

function connectWs() {
  const url = getWsUrl()
  if (!url) return
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return

  try {
    ws = new WebSocket(url)

    ws.onopen = () => {
      notifStore.setConnected(true)
      retryCount = 0
      startHeartbeat()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        // 心跳/连接确认 — 不处理
        if (data.type === 'ping' || data.type === 'pong' || data.type === 'connected') return

        // 通知类型消息 → 存入 store + toast
        if (data.type === 'notification' && data.data) {
          const msg: NotificationMessage = {
            type: data.data.type || 'system',
            title: data.data.title,
            body: data.data.body,
            data: data.data,
            timestamp: data.timestamp,
          }
          notifStore.addMessage(msg)
          showToast(msg)
        }
      } catch {
        // non-JSON message, ignore
      }
    }

    ws.onclose = () => {
      notifStore.setConnected(false)
      stopHeartbeat()
      if (retryCount < MAX_RETRIES) {
        scheduleReconnect()
      }
    }

    ws.onerror = () => {
      notifStore.setConnected(false)
    }
  } catch {
    notifStore.setConnected(false)
    if (retryCount < MAX_RETRIES) {
      scheduleReconnect()
    }
  }
}

function disconnectWs() {
  stopHeartbeat()
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  if (ws) { ws.close(); ws = null }
  notifStore.setConnected(false)
}

function startHeartbeat() {
  stopHeartbeat()
  heartbeatTimer = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }))
    }
  }, HEARTBEAT_INTERVAL)
}

function stopHeartbeat() {
  if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
}

function scheduleReconnect() {
  if (reconnectTimer) return
  retryCount++
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    connectWs()
  }, RECONNECT_INTERVAL)
}

function showToast(msg: NotificationMessage) {
  const typeMap: Record<string, { type: 'primary' | 'success' | 'warning' | 'danger'; prefix: string }> = {
    coach_push: { type: 'primary', prefix: '教练推送' },
    coach_message: { type: 'primary', prefix: '教练消息' },
    assessment: { type: 'success', prefix: '评估通知' },
    device_alert: { type: 'warning', prefix: '设备预警' },
    system: { type: 'primary', prefix: '系统通知' },
  }
  const cfg = typeMap[msg.type] || typeMap.system
  showNotify({
    type: cfg.type,
    message: `${cfg.prefix}: ${msg.title || msg.body || ''}`.slice(0, 60),
    duration: 4000,
  })
}

// 监听路由变化：登录后连接，登出后断开
watch(
  () => route.path,
  () => {
    const token = storage.getToken()
    if (token && !notifStore.connected) {
      connectWs()
    } else if (!token) {
      disconnectWs()
      notifStore.reset()
    }
  },
  { immediate: true }
)

onUnmounted(() => {
  disconnectWs()
})
</script>

<style lang="scss">
html {
  background: #e2e8f0;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  max-width: 430px;
  margin: 0 auto;
  min-height: 100dvh;
  background: var(--bg, #f8fafc);
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.06);
  overflow-y: auto;
  position: relative;
}
</style>
