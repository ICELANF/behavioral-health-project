import { ref, onMounted, onUnmounted } from 'vue'
import { showNotify } from 'vant'
import storage from '@/utils/storage'

interface WSOptions {
  /** WebSocket 路径 (default: /api/v1/ws) */
  path?: string
  /** 自动重连 (default: true) */
  autoReconnect?: boolean
  /** 重连间隔 ms (default: 3000) */
  reconnectInterval?: number
  /** 最大重连次数 (default: 10) */
  maxRetries?: number
  /** 心跳间隔 ms (default: 30000) */
  heartbeatInterval?: number
}

export function useWebSocket(options: WSOptions = {}) {
  const {
    path = '/api/v1/ws',
    autoReconnect = true,
    reconnectInterval = 3000,
    maxRetries = 10,
    heartbeatInterval = 30000,
  } = options

  const connected = ref(false)
  const lastMessage = ref<any>(null)
  const retryCount = ref(0)

  let ws: WebSocket | null = null
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function getWsUrl(): string {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = baseUrl.replace(/^https?:\/\//, '').replace(/\/$/, '')
    const token = storage.getToken()
    const url = `${protocol}//${host}${path}`
    return token ? `${url}?token=${token}` : url
  }

  function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return
    }

    try {
      ws = new WebSocket(getWsUrl())

      ws.onopen = () => {
        connected.value = true
        retryCount.value = 0
        startHeartbeat()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          lastMessage.value = data

          // 处理不同类型的推送
          if (data.type === 'reminder') {
            showNotify({
              type: 'warning',
              message: data.title || '健康提醒',
              duration: 5000,
            })
          } else if (data.type === 'coach_message') {
            showNotify({
              type: 'primary',
              message: `教练消息: ${data.content?.slice(0, 50) || ''}`,
              duration: 5000,
            })
          } else if (data.type === 'pong') {
            // heartbeat response, ignore
          }
        } catch {
          // non-JSON message
        }
      }

      ws.onclose = () => {
        connected.value = false
        stopHeartbeat()
        if (autoReconnect && retryCount.value < maxRetries) {
          scheduleReconnect()
        }
      }

      ws.onerror = () => {
        connected.value = false
      }
    } catch {
      connected.value = false
      if (autoReconnect && retryCount.value < maxRetries) {
        scheduleReconnect()
      }
    }
  }

  function disconnect() {
    stopHeartbeat()
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (ws) {
      ws.close()
      ws = null
    }
    connected.value = false
  }

  function send(data: any) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }

  function startHeartbeat() {
    stopHeartbeat()
    heartbeatTimer = setInterval(() => {
      send({ type: 'ping' })
    }, heartbeatInterval)
  }

  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
    retryCount.value++
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, reconnectInterval)
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    lastMessage,
    retryCount,
    connect,
    disconnect,
    send,
  }
}
